import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ===== LOAD DATA =====
df = pd.read_csv("clean_data.csv")

st.title("🏠 REAL ESTATE CEO DASHBOARD")

# ===== KPI =====
total_value = df["price_vnd"].sum()
avg_roi = df["ROI"].mean()
avg_price_m2 = df["price_per_m2"].mean()

col1, col2, col3 = st.columns(3)

col1.metric("💰 Total Value", f"{total_value:,.0f}")
col2.metric("📈 ROI", f"{avg_roi*100:.2f}%")
col3.metric("🏠 Avg Price/m2", f"{avg_price_m2:,.0f}")

# ===== LINE CHART =====
st.subheader("📉 Xu hướng tài sản")

df["date"] = pd.date_range(start="2022-01-01", periods=len(df))
df_sorted = df.sort_values("date")

fig1, ax1 = plt.subplots()
ax1.plot(df_sorted["date"], df_sorted["price_vnd"])
plt.xticks(rotation=45)

st.pyplot(fig1)

# ===== PIE + BAR =====
col1, col2 = st.columns(2)

# PIE
with col1:
    st.subheader("🥧 Phân bổ vốn")
    
    data = df.groupby("district")["price_vnd"].sum()

    def autopct_func(pct):
        return ('%1.1f%%' % pct) if pct > 5 else ''

    fig2, ax2 = plt.subplots()
    ax2.pie(data, labels=None, autopct=autopct_func, startangle=140)
    ax2.legend(data.index, loc="center left", bbox_to_anchor=(1, 0.5))

    st.pyplot(fig2)

# BAR
with col2:
    st.subheader("📊 ROI theo khu")
    
    roi = df.groupby("district")["ROI"].mean().sort_values()

    fig3, ax3 = plt.subplots()
    roi.plot(kind="bar", ax=ax3)
    plt.xticks(rotation=45)

    st.pyplot(fig3)

# ===== RECOMMENDATION =====
st.subheader("🎯 Top khu nên đầu tư")

score = df.groupby("district").agg({
    "ROI": "mean",
    "price_per_m2": "mean"
})

score["score"] = score["ROI"] / score["price_per_m2"]

top3 = score.sort_values("score", ascending=False).head(3)

st.dataframe(top3)

# ===== RISK =====
st.subheader("⚠️ Khu rủi ro")

risk = df.groupby("district")["ROI"].mean().sort_values().head(3)

st.dataframe(risk)