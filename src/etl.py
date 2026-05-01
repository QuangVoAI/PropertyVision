from __future__ import annotations

import re
from typing import Any


def clean_price(value: str) -> float:
    text = value.strip().lower().replace(",", ".")
    text = re.sub(r"\s+", " ", text)
    if not text:
        raise ValueError("price text is empty")

    million = 1_000_000
    billion = 1_000_000_000

    ty_match = re.search(r"(\d+(?:\.\d+)?)\s*tỷ(?:\s*(\d+(?:\.\d+)?))?", text)
    if ty_match:
        major = float(ty_match.group(1))
        minor = float(ty_match.group(2)) if ty_match.group(2) else 0.0
        if minor >= 10:
            minor /= 1000
        else:
            minor /= 10
        return (major + minor) * billion

    if "triệu" in text:
        number = float(re.search(r"(\d+(?:\.\d+)?)", text).group(1))
        return number * million

    if "tỷ" in text:
        number = float(re.search(r"(\d+(?:\.\d+)?)", text).group(1))
        return number * billion

    digits = re.sub(r"[^\d.]", "", text)
    if digits:
        return float(digits)

    raise ValueError(f"Unsupported price format: {value}")


def clean_area_sqm(value: Any) -> float:
    text = str(value).strip().lower().replace(",", ".")
    if not text or text == "nan":
        raise ValueError("area is empty")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        raise ValueError(f"Unsupported area format: {value}")
    return float(match.group(1))


def clean_integer(value: Any, default: int = 0) -> int:
    text = str(value).strip().lower()
    if not text or text == "nan":
        return default
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else default


def extract_district(address: str, city_name: str) -> str:
    text = str(address).strip()
    patterns = [
        r"(Quận\s+\d+)",
        r"(Huyện\s+[A-Za-zÀ-ỹ0-9\s]+)",
        r"(Thành phố\s+Thủ Đức)",
        r"(Thủ Đức)",
        r"(Bình Thạnh)",
        r"(Phú Nhuận)",
        r"(Gò Vấp)",
        r"(Tân Bình)",
        r"(Ba Đình)",
        r"(Cầu Giấy)",
        r"(Đống Đa)",
        r"(Hai Bà Trưng)",
        r"(Hoàng Mai)",
        r"(Hà Đông)",
        r"(Thanh Xuân)",
        r"(Hoàn Kiếm)",
        r"(Long Biên)",
        r"(Tây Hồ)",
        r"(Nam Từ Liêm)",
        r"(Bắc Từ Liêm)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    if city_name == "TP.HCM":
        return "Khác - TP.HCM"
    return "Khác - Hà Nội"
