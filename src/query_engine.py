from __future__ import annotations

import re

import pandas as pd


def detect_district_mention(question: str) -> str | None:
    text = str(question).strip()
    patterns = [
        r"(Quận\s+\d+)",
        r"(Huyện\s+[A-Za-zÀ-ỹ0-9\s]+?)(?=[,.?!]|$)",
        r"(Bình Thạnh|Phú Nhuận|Gò Vấp|Tân Bình|Thủ Đức|Ba Đình|Cầu Giấy|Đống Đa|Hai Bà Trưng|Hoàng Mai|Hà Đông|Thanh Xuân|Hoàn Kiếm|Long Biên|Tây Hồ|Nam Từ Liêm|Bắc Từ Liêm)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            return value[0].upper() + value[1:] if value else None
    return None


def extract_requested_district(question: str, available_districts: list[str]) -> str | None:
    lowered = question.lower()
    for district in available_districts:
        if district.lower() in lowered:
            return district
    mentioned = detect_district_mention(question)
    if mentioned:
        for district in available_districts:
            if district.lower() == mentioned.lower():
                return district
    return None


def extract_metric_intent(question: str) -> str:
    lowered = question.lower()
    if any(token in lowered for token in ["rẻ", "undervalued", "định giá", "z-score"]):
        return "valuation"
    if any(token in lowered for token in ["xu hướng", "forecast", "dự báo", "tăng", "giảm"]):
        return "trend"
    if any(token in lowered for token in ["giá", "price", "m2", "m²"]):
        return "price"
    return "overview"


def build_sql_summary(question: str, filtered_df: pd.DataFrame, scorecard_df: pd.DataFrame) -> str:
    if filtered_df.empty:
        return "Không có dữ liệu theo bộ lọc hiện tại."

    available_districts = sorted(filtered_df["district_name"].unique())
    district = extract_requested_district(question, available_districts)
    mentioned_district = detect_district_mention(question)
    intent = extract_metric_intent(question)

    if mentioned_district and not district:
        available_text = ", ".join(available_districts[:8])
        return (
            f"Câu hỏi đang nhắc tới {mentioned_district}, nhưng quận/huyện này không nằm trong bộ lọc dữ liệu hiện tại. "
            f"Các quận đang có trong bộ lọc gồm: {available_text}."
        )

    if district:
        district_df = filtered_df[filtered_df["district_name"] == district]
        avg_price = district_df["price_per_sqm"].mean() / 1_000_000
        median_area = district_df["area_sqm"].median()
        listing_count = len(district_df)
        message = (
            f"{district} hiện có khoảng {listing_count} tin theo bộ lọc, "
            f"giá trung bình {avg_price:.1f} triệu/m², diện tích trung vị {median_area:.1f} m²."
        )
        match = scorecard_df[scorecard_df["district_name"] == district]
        if not match.empty:
            row = match.iloc[0]
            message += f" Tín hiệu định giá: {row['signal']} với z-score {row['z_score']:.2f}."
        return message

    if intent == "valuation" and not scorecard_df.empty:
        undervalued = scorecard_df.nsmallest(3, "z_score")[["district_name", "z_score"]]
        parts = [f"{row.district_name} ({row.z_score:.2f})" for row in undervalued.itertuples()]
        return "Các quận đang rẻ tương đối theo z-score: " + ", ".join(parts) + "."

    if intent == "trend":
        market_avg = filtered_df["price_per_sqm"].mean() / 1_000_000
        leaders = (
            filtered_df.groupby("district_name")["price_per_sqm"]
            .mean()
            .sort_values(ascending=False)
            .head(3)
        )
        parts = [f"{district}: {value/1_000_000:.1f} triệu/m²" for district, value in leaders.items()]
        return f"Giá trung bình toàn bộ bộ lọc là {market_avg:.1f} triệu/m². Nhóm dẫn đầu: " + ", ".join(parts) + "."

    top_districts = (
        filtered_df.groupby("district_name")["price_per_sqm"]
        .mean()
        .sort_values(ascending=False)
        .head(5)
    )
    parts = [f"{district}: {value/1_000_000:.1f} triệu/m²" for district, value in top_districts.items()]
    return "Tóm tắt SQL hiện tại: " + ", ".join(parts) + "."
