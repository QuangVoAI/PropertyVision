from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.query_engine import build_sql_summary, detect_district_mention, extract_metric_intent, extract_requested_district
from src.rag import answer_with_context, retrieve_context


@dataclass
class AgenticRAGResult:
    question: str
    intent: str
    city: str | None
    district: str | None
    mentioned_district: str | None
    tone: str
    sql_summary: str
    rewritten_query: str
    retrieved_docs: list[dict]
    graded_docs: list[dict]
    answer: str
    citations: list[str]


def analyze_question(question: str, filtered_df: pd.DataFrame) -> tuple[str, str | None, str | None, str | None]:
    available_districts = sorted(filtered_df["district_name"].unique()) if not filtered_df.empty else []
    intent = extract_metric_intent(question)
    district = extract_requested_district(question, available_districts)
    mentioned_district = detect_district_mention(question)
    city = filtered_df["city_name"].iloc[0] if "city_name" in filtered_df.columns and not filtered_df.empty else None
    return intent, district, city, mentioned_district


def rewrite_query(question: str, intent: str, district: str | None, city: str | None) -> str:
    if district and intent == "trend":
        return f"Xu hướng giá bất động sản và hạ tầng ảnh hưởng tới {district} tại {city or 'Việt Nam'}"
    if district and intent == "valuation":
        return f"Lý do định giá bất động sản tại {district} {city or ''} thấp hoặc cao hơn mặt bằng".strip()
    if district:
        return f"Tư vấn đầu tư bất động sản tại {district} {city or ''} dựa trên quy hoạch và giá".strip()
    if intent == "valuation":
        return f"Các khu vực bất động sản đang định giá thấp tương đối tại {city or 'Việt Nam'} và nguyên nhân"
    if intent == "trend":
        return f"Xu hướng giá bất động sản đô thị tại {city or 'Việt Nam'} theo hạ tầng và quy hoạch"
    return question


def grade_docs(docs: list[dict], city: str | None, min_score: float = 0.08) -> list[dict]:
    graded = []
    city_keywords = {
        "TP.HCM": ["tp.hcm", "hồ chí minh", "hcmc", "metro", "khu đông"],
        "Hà Nội": ["hà nội", "ha noi", "vành đai", "phía tây"],
    }.get(city or "", [])
    for doc in docs:
        base_score = float(doc.get("rerank_score", doc.get("score", 0.0)))
        content = str(doc.get("content", "")).lower()
        city_bonus = 0.12 if any(keyword in content for keyword in city_keywords) else 0.0
        final_score = base_score + city_bonus
        doc["final_score"] = final_score
        if final_score >= min_score:
            graded.append(doc)
    return sorted(graded, key=lambda item: item.get("final_score", 0.0), reverse=True)


def run_agentic_rag(
    question: str,
    filtered_df: pd.DataFrame,
    scorecard_df: pd.DataFrame,
    tone: str = "advisor",
) -> AgenticRAGResult:
    intent, district, city, mentioned_district = analyze_question(question, filtered_df)
    sql_summary = build_sql_summary(question, filtered_df, scorecard_df)

    if mentioned_district and not district:
        rewritten_query = question
        retrieved_docs = []
        graded_docs = []
    else:
        rewritten_query = rewrite_query(question, intent, district, city)
        retrieved_docs = retrieve_context(rewritten_query, top_k=4)
        graded_docs = grade_docs(retrieved_docs, city=city)

        if not graded_docs and rewritten_query != question:
            retrieved_docs = retrieve_context(question, top_k=4)
            graded_docs = grade_docs(retrieved_docs, city=city, min_score=0.05)

    answer_payload = answer_with_context(
        question=rewritten_query,
        sql_summary=sql_summary,
        intent=intent,
        city=city,
        district=district,
        tone=tone,
        contexts=graded_docs if graded_docs else retrieved_docs,
    )
    answer = answer_payload["answer"]
    citations = answer_payload["citations"]
    return AgenticRAGResult(
        question=question,
        intent=intent,
        city=city,
        district=district,
        mentioned_district=mentioned_district,
        tone=tone,
        sql_summary=sql_summary,
        rewritten_query=rewritten_query,
        retrieved_docs=retrieved_docs,
        graded_docs=graded_docs,
        answer=answer,
        citations=citations,
    )
