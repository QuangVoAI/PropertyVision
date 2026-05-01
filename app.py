from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.agentic_rag import run_agentic_rag
from src.analytics import (
    SCENARIO_PRESETS,
    compute_undervalued_scores,
    district_scorecard,
    forecast_district_prices,
    simulate_price,
    summarize_market,
)
from src.db import get_connection
from src.pipeline import raw_files_status, seed_kaggle_data, seed_synthetic_data
from src.rag import build_vector_store, package_status, rag_runtime_mode, reset_vector_store


st.set_page_config(page_title="PropertyVision", page_icon="🏙️", layout="wide")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --navy: #102542;
            --gold: #d4a017;
            --cream: #f7f3e9;
            --slate: #274060;
        }
        .stApp {
            background: linear-gradient(180deg, #f7f3e9 0%, #ffffff 65%);
        }
        h1, h2, h3 {
            color: var(--navy);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #102542 0%, #1f3b5b 100%);
        }
        [data-testid="stSidebar"] * {
            color: white;
        }
        .metric-card {
            padding: 0.8rem 1rem;
            border-radius: 14px;
            background: rgba(16, 37, 66, 0.06);
            border: 1px solid rgba(16, 37, 66, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_listings() -> pd.DataFrame:
    conn = get_connection()
    query = """
    SELECT
        f.listing_id,
        c.city_name,
        d.district_name,
        p.property_type_name,
        f.owner_name,
        f.address,
        f.area_sqm,
        f.bedrooms,
        f.legal_status,
        f.posted_date,
        f.price_text,
        f.price_vnd,
        f.price_per_sqm,
        f.latitude,
        f.longitude,
        f.description
    FROM fact_listings f
    JOIN dim_city c ON c.city_id = f.city_id
    JOIN dim_district d ON d.district_id = f.district_id
    JOIN dim_property_type p ON p.property_type_id = f.property_type_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data
def load_monthly() -> pd.DataFrame:
    conn = get_connection()
    query = """
    SELECT
        c.city_name,
        d.district_name,
        m.month,
        m.avg_price_per_sqm,
        m.listing_count
    FROM mart_district_monthly m
    JOIN dim_district d ON d.district_id = m.district_id
    JOIN dim_city c ON c.city_id = d.city_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def build_sidebar(df: pd.DataFrame) -> tuple[str, list[str], list[str]]:
    st.sidebar.title("PropertyVision")
    city = st.sidebar.selectbox("Thành phố", sorted(df["city_name"].unique()))
    district_options = sorted(df.loc[df["city_name"] == city, "district_name"].unique())
    type_options = sorted(df["property_type_name"].unique())
    selected_districts = st.sidebar.multiselect("Quận/Huyện", district_options, default=district_options[:3])
    selected_types = st.sidebar.multiselect("Loại nhà", type_options, default=type_options)
    return city, selected_districts, selected_types


def render_data_control_panel() -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Data Control")
    status = raw_files_status()
    st.sidebar.caption(
        "Kaggle files: "
        f"HCM {'OK' if status['hcmc_csv'] else 'Missing'} | "
        f"HN {'OK' if status['hanoi_csv'] else 'Missing'}"
    )
    if st.sidebar.button("Load Synthetic Demo Data", use_container_width=True):
        message = seed_synthetic_data()
        st.cache_data.clear()
        st.sidebar.success(message)
    if st.sidebar.button("Import Kaggle CSV", use_container_width=True, disabled=not all(status.values())):
        try:
            message = seed_kaggle_data()
            st.cache_data.clear()
            st.sidebar.success(message)
        except Exception as exc:
            st.sidebar.error(str(exc))
    st.sidebar.markdown("---")
    st.sidebar.subheader("RAG Control")
    pkg = package_status()
    st.sidebar.caption(
        "Runtime: "
        f"{rag_runtime_mode()} | chromadb={'OK' if pkg['chromadb'] else 'Missing'} | "
        f"sentence-transformers={'OK' if pkg['sentence_transformers'] else 'Missing'} | "
        f"openai={'OK' if pkg['openai'] else 'Missing'}"
    )
    if st.sidebar.button("Build Vector Index", use_container_width=True):
        try:
            result = build_vector_store(force_rebuild=True)
            if result.get("enabled"):
                st.sidebar.success(f"Vector index ready: {result.get('chunks', 0)} chunks")
            else:
                st.sidebar.warning(result.get("reason", "Index build skipped"))
        except Exception as exc:
            st.sidebar.error(str(exc))
    if st.sidebar.button("Reset Vector Index", use_container_width=True):
        reset_vector_store()
        st.sidebar.success("Vector index removed.")


def render_overview(filtered_df: pd.DataFrame, monthly_df: pd.DataFrame, scorecard_df: pd.DataFrame) -> None:
    st.subheader("Tổng quan thị trường")
    summary = summarize_market(filtered_df, monthly_df)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tin đăng", f"{summary['listing_count']:,}")
    col2.metric("Quận theo bộ lọc", f"{summary['district_count']}")
    col3.metric("Giá trung bình / m²", f"{summary['avg_price_per_sqm']/1_000_000:.1f} triệu")
    col4.metric("Biến động thị trường", f"{summary['market_delta_pct']:.1f}%", delta=f"{summary['market_delta_pct']:.1f}%")

    district_heat = (
        filtered_df.groupby(["district_name"], as_index=False)
        .agg(avg_price_per_sqm=("price_per_sqm", "mean"), latitude=("latitude", "mean"), longitude=("longitude", "mean"))
    )
    fig = px.scatter_map(
        district_heat,
        lat="latitude",
        lon="longitude",
        size="avg_price_per_sqm",
        color="avg_price_per_sqm",
        hover_name="district_name",
        zoom=10,
        height=500,
        color_continuous_scale="YlOrBr",
    )
    fig.update_layout(map_style="carto-positron", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    col_left, col_right = st.columns([1.15, 1])
    with col_left:
        trend_df = (
            monthly_df.groupby("month", as_index=False)
            .agg(avg_price_per_sqm=("avg_price_per_sqm", "mean"), listing_count=("listing_count", "sum"))
            .sort_values("month")
        )
        trend_fig = go.Figure()
        trend_fig.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["avg_price_per_sqm"],
                mode="lines+markers",
                name="Avg Price/m²",
                line=dict(color="#102542", width=3),
            )
        )
        trend_fig.update_layout(height=320, template="plotly_white", yaxis_title="VND / m²")
        st.plotly_chart(trend_fig, use_container_width=True)
    with col_right:
        st.markdown("**Điểm nóng đầu tư**")
        preview = scorecard_df[["district_name", "signal", "liquidity_score", "z_score"]].copy()
        preview["liquidity_score"] = preview["liquidity_score"].map(lambda x: f"{x:.2f}")
        preview["z_score"] = preview["z_score"].map(lambda x: f"{x:.2f}")
        st.dataframe(preview.head(8), use_container_width=True, hide_index=True)


def render_data_tab(filtered_df: pd.DataFrame, scorecard_df: pd.DataFrame) -> None:
    st.subheader("Dữ liệu gốc")
    quality_col1, quality_col2, quality_col3 = st.columns(3)
    quality_col1.metric("Thiếu pháp lý", int((filtered_df["legal_status"].astype(str).str.strip() == "").sum()))
    quality_col2.metric("Diện tích trung vị", f"{filtered_df['area_sqm'].median():.1f} m²")
    quality_col3.metric("Loại nhà", filtered_df["property_type_name"].nunique())

    st.markdown("**District Scorecard**")
    scorecard_view = scorecard_df.copy()
    for column in ["avg_price_per_sqm", "latest_month_price_per_sqm"]:
        if column in scorecard_view:
            scorecard_view[column] = scorecard_view[column].map(lambda x: f"{x/1_000_000:.1f} triệu")
    st.dataframe(scorecard_view, use_container_width=True, hide_index=True)

    st.markdown("**Listings Explorer**")
    display_df = filtered_df.copy()
    display_df["price_vnd"] = display_df["price_vnd"].map(lambda x: f"{x:,.0f}")
    display_df["price_per_sqm"] = display_df["price_per_sqm"].map(lambda x: f"{x/1_000_000:.1f} triệu")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_forecast_tab(filtered_df: pd.DataFrame, monthly_df: pd.DataFrame) -> None:
    st.subheader("Dự báo và What-if")
    district = st.selectbox("Chọn quận để dự báo", sorted(filtered_df["district_name"].unique()))
    district_monthly = monthly_df[monthly_df["district_name"] == district]
    forecast_df, residual_std = forecast_district_prices(district_monthly)

    fig = go.Figure()
    history = forecast_df[forecast_df["series_type"] == "history"]
    future = forecast_df[forecast_df["series_type"] == "forecast"]
    fig.add_trace(go.Scatter(x=history["month"], y=history["avg_price_per_sqm"], mode="lines+markers", name="Actual"))
    fig.add_trace(go.Scatter(x=forecast_df["month"], y=forecast_df["prediction"], mode="lines", name="Trend"))
    fig.add_trace(
        go.Scatter(
            x=list(forecast_df["month"]) + list(forecast_df["month"][::-1]),
            y=list(forecast_df["y_upper"]) + list(forecast_df["y_lower"][::-1]),
            fill="toself",
            fillcolor="rgba(212,160,23,0.18)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Confidence Band",
        )
    )
    fig.update_layout(height=420, yaxis_title="VND / m²", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Độ lệch chuẩn sai số ước lượng: {residual_std/1_000_000:.2f} triệu VND/m²")

    col1, col2 = st.columns([1, 1.2])
    with col1:
        preset = st.selectbox("Kịch bản demo", list(SCENARIO_PRESETS.keys()), index=1)
        defaults = SCENARIO_PRESETS[preset]
        interest_rate = st.slider("Lãi suất (%)", 5.0, 15.0, float(defaults["interest_rate"]), 0.5)
        growth_rate = st.slider("Tăng trưởng kỳ vọng (%)", -5.0, 20.0, float(defaults["growth_rate"]), 0.5)
        supply_shock = st.slider("Supply shock", 0.80, 1.20, float(defaults["supply_shock"]), 0.01)
        years = st.slider("Số năm", 1, 10, 5)
        st.caption(
            "Preset demo: Đóng băng = lãi cao, tăng trưởng thấp; "
            "Sốt đất hạ tầng = lãi thấp, tăng trưởng cao, supply căng."
        )
    with col2:
        base_price = float(district_monthly["avg_price_per_sqm"].iloc[-1]) if not district_monthly.empty else 0.0
        sim_df = simulate_price(base_price, interest_rate, years, growth_rate, supply_shock)
        sim_fig = px.line(sim_df, x="year", y="simulated_price", markers=True, color_discrete_sequence=["#102542"])
        sim_fig.update_layout(height=320, template="plotly_white", yaxis_title="VND / m²")
        st.plotly_chart(sim_fig, use_container_width=True)
        final_price = sim_df["simulated_price"].iloc[-1] / 1_000_000
        st.metric("Giá mô phỏng cuối kỳ", f"{final_price:.1f} triệu/m²")

    snapshot = (
        monthly_df.sort_values("month")
        .groupby("district_name", as_index=False)
        .tail(1)[["district_name", "avg_price_per_sqm"]]
    )
    scored = compute_undervalued_scores(snapshot)
    st.subheader("Undervalued Detection")
    st.dataframe(scored, use_container_width=True, hide_index=True)


def render_chat_tab(filtered_df: pd.DataFrame, scorecard_df: pd.DataFrame) -> None:
    st.subheader("Agentic RAG + SQL Assistant")
    with st.expander("RAG Flow", expanded=False):
        st.markdown(
            """
            1. Phân tích câu hỏi: nhận diện intent và quận/huyện.
            2. SQL grounding: lấy số liệu thật từ data mart hiện tại.
            3. Query rewrite: viết lại truy vấn theo ngôn ngữ quy hoạch/đầu tư.
            4. Retrieval + grading: lấy context từ knowledge base và lọc tài liệu yếu.
            5. Answer synthesis: ghép số liệu thị trường với context quy hoạch để tư vấn.
            """
        )
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hãy hỏi về giá quận, xu hướng, hoặc lý do nên quan tâm một khu vực cụ thể."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Ví dụ: Quận 7 có đáng chú ý không?")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    result = run_agentic_rag(prompt, filtered_df, scorecard_df)
    content = result.answer
    if result.citations:
        content += "\n\nNguồn: " + ", ".join(result.citations)

    with st.chat_message("assistant"):
        st.write(content)
        with st.expander("Reasoning Trace", expanded=False):
            st.write(f"Intent: `{result.intent}`")
            st.write(f"City: `{result.city or 'N/A'}`")
            st.write(f"District: `{result.district or 'N/A'}`")
            st.write(f"Rewritten query: `{result.rewritten_query}`")
            st.write(f"SQL summary: {result.sql_summary}")
            st.write(
                "Retrieved docs: "
                + (", ".join(doc["source"] for doc in result.retrieved_docs) if result.retrieved_docs else "None")
            )
            st.write(
                "Graded docs: "
                + (", ".join(doc["source"] for doc in result.graded_docs) if result.graded_docs else "None")
            )
    st.session_state.messages.append({"role": "assistant", "content": content})


def main() -> None:
    inject_styles()
    st.title("PropertyVision")
    st.caption("Data visualization + forecasting + lightweight RAG for real-estate demo")
    render_data_control_panel()

    listings = load_listings()
    monthly = load_monthly()

    if listings.empty:
        st.error("CSDL đang trống. Dùng sidebar để nạp synthetic data hoặc import Kaggle CSV.")
        return

    city, selected_districts, selected_types = build_sidebar(listings)
    if not selected_districts or not selected_types:
        st.warning("Hãy chọn ít nhất 1 quận và 1 loại nhà để hiển thị dữ liệu.")
        return
    filtered = listings[
        (listings["city_name"] == city)
        & (listings["district_name"].isin(selected_districts))
        & (listings["property_type_name"].isin(selected_types))
    ]
    filtered_monthly = monthly[
        (monthly["city_name"] == city) & (monthly["district_name"].isin(selected_districts))
    ]
    if filtered.empty:
        st.warning("Không có bản ghi nào khớp bộ lọc hiện tại.")
        return
    scorecard = district_scorecard(filtered, filtered_monthly)

    overview_tab, data_tab, forecast_tab, chat_tab = st.tabs(
        ["Overview", "Data", "Forecast", "Chat"]
    )
    with overview_tab:
        render_overview(filtered, filtered_monthly, scorecard)
    with data_tab:
        render_data_tab(filtered, scorecard)
    with forecast_tab:
        render_forecast_tab(filtered, filtered_monthly)
    with chat_tab:
        render_chat_tab(filtered, scorecard)


if __name__ == "__main__":
    main()
