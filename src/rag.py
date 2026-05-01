from __future__ import annotations

import json
import os
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib import error, request

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DOCS_DIR = Path(__file__).resolve().parent.parent / "knowledge"
CHROMA_DIR = Path(__file__).resolve().parent.parent / "data" / "chroma"
COLLECTION_NAME = "propertyvision_knowledge"
EMBED_MODEL_NAME = os.getenv("RAG_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
RERANK_MODEL_NAME = os.getenv("RAG_RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LOCAL_LLM_PROVIDER = os.getenv("LOCAL_LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
OPENAI_COMPAT_BASE_URL = os.getenv("OPENAI_COMPAT_BASE_URL", "")
OPENAI_COMPAT_MODEL = os.getenv("OPENAI_COMPAT_MODEL", "Qwen/Qwen2.5-14B-Instruct")
OPENAI_COMPAT_API_KEY = os.getenv("OPENAI_COMPAT_API_KEY", "EMPTY")
TONE_STYLES = {
    "analyst": {
        "label": "Analyst",
        "voice": "ngắn, chính xác, thiên về phân tích định lượng, tránh cảm tính",
    },
    "advisor": {
        "label": "Advisor",
        "voice": "giọng tư vấn đầu tư, rõ kết luận, có lý do và cảnh báo rủi ro",
    },
    "pitch": {
        "label": "Pitch",
        "voice": "thuyết phục, gọn, phù hợp demo bảo vệ, nhưng không được thổi phồng dữ liệu",
    },
}


def load_knowledge_base() -> pd.DataFrame:
    docs = []
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(DOCS_DIR.glob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        docs.append({"source": path.name, "content": path.read_text(encoding="utf-8")})
    return pd.DataFrame(docs)


def split_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def load_chunked_documents() -> list[dict[str, Any]]:
    raw_docs = load_knowledge_base()
    chunked = []
    for row in raw_docs.to_dict("records"):
        source = str(row["source"]).lower()
        if "hcm" in source:
            city_hint = "TP.HCM"
        elif "hanoi" in source or "ha_noi" in source:
            city_hint = "Hà Nội"
        else:
            city_hint = "General"
        for index, chunk in enumerate(split_text(row["content"])):
            chunked.append(
                {
                    "id": f"{row['source']}::{index}",
                    "source": row["source"],
                    "chunk_id": index,
                    "content": chunk,
                    "city_hint": city_hint,
                }
            )
    return chunked


def select_tone_style(tone: str | None) -> dict[str, str]:
    if not tone:
        return TONE_STYLES["advisor"]
    return TONE_STYLES.get(tone.lower(), TONE_STYLES["advisor"])


def city_tokens(city: str | None) -> list[str]:
    mapping = {
        "TP.HCM": ["tp.hcm", "hồ chí minh", "ho chi minh", "hcmc", "metro", "khu đông"],
        "Hà Nội": ["hà nội", "ha noi", "vành đai", "phía tây"],
    }
    return mapping.get(city or "", [])


def district_tokens(district: str | None) -> list[str]:
    if not district:
        return []
    lowered = district.lower()
    tokens = {lowered}
    tokens.update(part for part in lowered.replace("-", " ").split() if len(part) > 2)
    return list(tokens)


def infer_decision_frame(intent: str, district: str | None) -> str:
    if intent == "valuation":
        return f"đánh giá quận {district} có đang rẻ hay đắt tương đối" if district else "so sánh định giá tương đối giữa các quận"
    if intent == "trend":
        return f"đánh giá xu hướng giá tại {district}" if district else "đánh giá xu hướng giá thị trường"
    if district:
        return f"quyết định có nên ưu tiên {district} cho đầu tư hay không"
    return "đưa ra kết luận đầu tư ngắn gọn từ dữ liệu hiện có"


def build_answer_plan(
    sql_summary: str,
    contexts: list[dict],
    intent: str,
    city: str | None,
    district: str | None,
) -> dict[str, Any]:
    plan = {
        "decision_frame": infer_decision_frame(intent, district),
        "opening_focus": district or city or "thị trường hiện tại",
        "must_use_sql": sql_summary,
        "evidence_points": [],
        "risk_angle": "",
    }
    for doc in contexts[:2]:
        content = str(doc["content"]).strip().replace("\n", " ")
        plan["evidence_points"].append(content[:180])

    if intent == "valuation":
        plan["risk_angle"] = "tránh nhầm quận rẻ tương đối với quận có thanh khoản yếu hoặc pháp lý kém"
    elif intent == "trend":
        plan["risk_angle"] = "xu hướng giá chỉ đáng tin khi đi cùng tiến độ hạ tầng và nguồn cung"
    else:
        plan["risk_angle"] = "không nên kết luận chỉ từ giá tuyệt đối, cần nhìn thêm thanh khoản và catalyst"
    return plan


def derive_positioning(sql_summary: str, intent: str) -> str:
    lowered = sql_summary.lower()
    if "undervalued" in lowered:
        return "có upside định giá tốt hơn mặt bằng hiện tại"
    if "neutral/expensive" in lowered or "expensive" in lowered:
        return "không còn là lựa chọn rẻ, phù hợp hơn với chiến lược an toàn hoặc giữ giá"
    if intent == "trend":
        return "cần nhìn theo xu hướng thay vì kết luận chỉ từ mức giá hiện tại"
    return "cần đối chiếu cả giá, thanh khoản và quy hoạch trước khi quyết định"


def filter_contexts_for_focus(
    docs: list[dict],
    city: str | None,
    district: str | None,
    intent: str,
    top_k: int = 3,
) -> list[dict]:
    if not docs:
        return []

    city_keywords = city_tokens(city)
    district_keywords = district_tokens(district)
    intent_keywords = {
        "valuation": ["giá", "định giá", "thanh khoản", "mặt bằng"],
        "trend": ["xu hướng", "hạ tầng", "tăng", "giảm", "quy hoạch"],
        "price": ["giá", "m²", "triệu"],
        "overview": ["hạ tầng", "quy hoạch", "kết nối", "thanh khoản"],
    }.get(intent, [])

    enriched = []
    for doc in docs:
        content = str(doc.get("content", "")).lower()
        score = float(doc.get("rerank_score", doc.get("score", 0.0)))
        if city_keywords and any(token in content for token in city_keywords):
            score += 0.45
        elif city and doc.get("city_hint") == city:
            score += 0.35
        if district_keywords and any(token in content for token in district_keywords):
            score += 0.25
        if intent_keywords and any(token in content for token in intent_keywords):
            score += 0.18
        doc["focus_score"] = score
        enriched.append(doc)
    same_city_docs = [doc for doc in enriched if city and doc.get("city_hint") == city]
    if same_city_docs:
        enriched = same_city_docs
    return sorted(enriched, key=lambda item: item.get("focus_score", 0.0), reverse=True)[:top_k]


def package_status() -> dict[str, bool]:
    status = {
        "chromadb": False,
        "sentence_transformers": False,
        "openai": False,
        "local_llm": False,
    }
    try:
        import chromadb  # noqa: F401

        status["chromadb"] = True
    except Exception:
        pass
    try:
        import sentence_transformers  # noqa: F401

        status["sentence_transformers"] = True
    except Exception:
        pass
    try:
        import openai  # noqa: F401

        status["openai"] = True
    except Exception:
        pass
    status["local_llm"] = local_llm_available()
    return status


def rag_runtime_mode() -> str:
    status = package_status()
    if status["chromadb"] and status["sentence_transformers"]:
        if status["local_llm"]:
            return "vector + reranker + local-llm"
        if status["openai"] and os.getenv("OPENAI_API_KEY"):
            return "vector + reranker + llm"
        return "vector + reranker"
    if status["local_llm"]:
        return "tfidf + local-llm"
    return "tfidf fallback"


def local_llm_available() -> bool:
    if LOCAL_LLM_PROVIDER == "ollama":
        try:
            with request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.5) as response:
                return response.status == 200
        except Exception:
            return False
    if LOCAL_LLM_PROVIDER == "openai_compat" and OPENAI_COMPAT_BASE_URL:
        return True
    return False


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBED_MODEL_NAME)


@lru_cache(maxsize=1)
def get_reranker_model():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(RERANK_MODEL_NAME)


def reset_vector_store() -> None:
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)


def build_vector_store(force_rebuild: bool = False) -> dict[str, Any]:
    status = package_status()
    if not (status["chromadb"] and status["sentence_transformers"]):
        return {"enabled": False, "reason": "Missing chromadb or sentence-transformers"}

    import chromadb

    docs = load_chunked_documents()
    if not docs:
        return {"enabled": False, "reason": "No knowledge documents found"}

    if force_rebuild:
        reset_vector_store()

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    if force_rebuild or collection.count() != len(docs):
        if collection.count() > 0:
            client.delete_collection(COLLECTION_NAME)
            collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

        embedder = get_embedding_model()
        documents = [doc["content"] for doc in docs]
        embeddings = embedder.encode(documents, convert_to_numpy=True, show_progress_bar=False).tolist()
        metadatas = [{"source": doc["source"], "chunk_id": doc["chunk_id"]} for doc in docs]
        ids = [doc["id"] for doc in docs]
        collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    return {"enabled": True, "chunks": len(docs)}


def retrieve_context_tfidf(question: str, top_k: int = 4) -> list[dict]:
    docs = load_chunked_documents()
    if not docs:
        return []

    docs_df = pd.DataFrame(docs)
    vectorizer = TfidfVectorizer(stop_words=None)
    matrix = vectorizer.fit_transform(docs_df["content"])
    query_vector = vectorizer.transform([question])
    scores = cosine_similarity(query_vector, matrix).flatten()
    docs_df["score"] = scores
    docs_df["rerank_score"] = docs_df["score"]
    return docs_df.sort_values("score", ascending=False).head(top_k).to_dict("records")


def rerank_documents(question: str, docs: list[dict], top_k: int = 3) -> list[dict]:
    if not docs:
        return []

    try:
        reranker = get_reranker_model()
        pairs = [(question, doc["content"]) for doc in docs]
        rerank_scores = reranker.predict(pairs).tolist()
        for doc, score in zip(docs, rerank_scores):
            doc["rerank_score"] = float(score)
        return sorted(docs, key=lambda item: item.get("rerank_score", 0.0), reverse=True)[:top_k]
    except Exception:
        for doc in docs:
            doc["rerank_score"] = float(doc.get("score", 0.0))
        return sorted(docs, key=lambda item: item.get("rerank_score", 0.0), reverse=True)[:top_k]


def retrieve_context(question: str, top_k: int = 6, rerank_top_k: int = 3) -> list[dict]:
    status = package_status()
    docs = []

    if status["chromadb"] and status["sentence_transformers"]:
        build_vector_store(force_rebuild=False)
        import chromadb

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        embedder = get_embedding_model()
        query_embedding = embedder.encode([question], convert_to_numpy=True, show_progress_bar=False).tolist()[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for content, metadata, distance in zip(documents, metadatas, distances):
            docs.append(
                {
                    "source": metadata["source"],
                    "chunk_id": metadata["chunk_id"],
                    "content": content,
                    "score": 1 - float(distance),
                }
            )
    else:
        docs = retrieve_context_tfidf(question, top_k=top_k)

    return rerank_documents(question, docs, top_k=rerank_top_k)


def generate_fallback_answer(
    sql_summary: str,
    contexts: list[dict],
    intent: str,
    city: str | None,
    district: str | None,
    tone: str = "advisor",
) -> str:
    tone_style = select_tone_style(tone)
    plan = build_answer_plan(sql_summary, contexts, intent, city, district)
    positioning = derive_positioning(sql_summary, intent)
    if not contexts:
        return (
            f"Kết luận nhanh: chưa đủ context quy hoạch để kết luận sắc hơn về {plan['opening_focus']}.\n\n"
            f"Số liệu chắc chắn đang có: {sql_summary}\n\n"
            f"Lưu ý: {plan['risk_angle']}."
        )

    recommendation = "Khuyến nghị:"
    if intent == "valuation":
        recommendation += " nếu mục tiêu là tìm upside, hãy ưu tiên quận có định giá chưa cao nhưng vẫn có động lực hạ tầng rõ."
    elif intent == "trend":
        recommendation += " theo dõi giá/m² cùng tiến độ hạ tầng và nguồn cung mới, không nên nhìn mỗi một nhịp tăng giá."
    elif district:
        recommendation += f" với {district}, nên nhìn đồng thời mức giá, thanh khoản và catalyst quy hoạch trước khi xuống tiền."
    else:
        recommendation += " kết hợp dữ liệu định lượng với bối cảnh quy hoạch để tránh kết luận cảm tính."

    if tone == "analyst":
        answer = [
            f"Kết luận: {district or city or 'Khu vực này'} {positioning}.",
            "",
            f"Dữ liệu cốt lõi: {sql_summary}",
            "",
            "Luận điểm chính:",
        ]
        answer.extend([f"- {point}" for point in plan["evidence_points"][:2]])
        answer.extend(["", f"Rủi ro: {plan['risk_angle']}.", recommendation])
        return "\n".join(answer)

    if tone == "pitch":
        answer = [
            f"{district or city or 'Khu vực này'} có câu chuyện đầu tư, nhưng kết luận nhanh là khu vực này {positioning}.",
            f"Hiện tại, {sql_summary}",
            f"Điểm hỗ trợ mạnh nhất là {plan['evidence_points'][0].lower()}.",
        ]
        if len(plan["evidence_points"]) > 1:
            answer.append(f"Luận điểm bổ sung là {plan['evidence_points'][1].lower()}.")
        answer.append(f"Tuy nhiên, {plan['risk_angle']}.")
        answer.append(recommendation)
        return "\n".join(answer)

    answer = [
        f"Kết luận nhanh: {district or city or 'Khu vực này'} {positioning}.",
        "",
        f"Số liệu chắc chắn: {sql_summary}",
        "",
        "Vì sao:",
    ]
    answer.extend([f"- {point}" for point in plan["evidence_points"][:2]])
    answer.extend(["", f"Cần lưu ý: {plan['risk_angle']}.", recommendation])
    answer.append(f"Giọng trả lời hiện tại: {tone_style['label']} - {tone_style['voice']}.")
    return "\n".join(answer)


def generate_llm_answer(
    question: str,
    sql_summary: str,
    contexts: list[dict],
    intent: str,
    city: str | None,
    district: str | None,
    tone: str = "advisor",
) -> str | None:
    local_answer = generate_local_llm_answer(question, sql_summary, contexts, intent, city, district, tone)
    if local_answer:
        return local_answer

    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None


def generate_local_llm_answer(
    question: str,
    sql_summary: str,
    contexts: list[dict],
    intent: str,
    city: str | None,
    district: str | None,
    tone: str = "advisor",
) -> str | None:
    if LOCAL_LLM_PROVIDER == "ollama":
        return generate_ollama_answer(question, sql_summary, contexts, intent, city, district, tone)
    if LOCAL_LLM_PROVIDER == "openai_compat" and OPENAI_COMPAT_BASE_URL:
        return generate_openai_compatible_answer(question, sql_summary, contexts, intent, city, district, tone)
    return None


def _build_generation_messages(
    question: str,
    sql_summary: str,
    contexts: list[dict],
    intent: str,
    city: str | None,
    district: str | None,
    tone: str,
) -> tuple[str, str]:
    tone_style = select_tone_style(tone)
    plan = build_answer_plan(sql_summary, contexts, intent, city, district)
    context_text = "\n\n".join(
        f"[{index + 1}] Source={doc['source']} | Score={doc.get('focus_score', doc.get('rerank_score', doc.get('score', 0.0))):.3f}\n{doc['content']}"
        for index, doc in enumerate(contexts[:3])
    )
    system_prompt = (
        "Bạn là chuyên gia phân tích bất động sản Việt Nam. "
        "Luôn ưu tiên số liệu SQL được cung cấp, dùng context truy hồi để giải thích nguyên nhân, "
        "không bịa thông tin ngoài context, và trả lời ngắn gọn nhưng có lập luận. "
        f"Giọng điệu phải {tone_style['voice']}."
    )
    user_prompt = (
        f"Câu hỏi: {question}\n"
        f"Intent: {intent}\n"
        f"City: {city or 'N/A'}\n"
        f"District: {district or 'N/A'}\n"
        f"Số liệu SQL: {sql_summary}\n\n"
        f"Decision frame: {plan['decision_frame']}\n"
        f"Risk angle: {plan['risk_angle']}\n\n"
        f"Context truy hồi:\n{context_text}\n\n"
        "Hãy trả lời bằng tiếng Việt với cấu trúc:\n"
        "1. Kết luận đi thẳng vào quyết định của người hỏi\n"
        "2. 2-3 luận điểm thật sự bám số liệu và context\n"
        "3. 1 cảnh báo/rủi ro\n"
        "Không được mở đầu lan man, không được nhắc lại toàn bộ prompt."
    )
    return system_prompt, user_prompt


def generate_ollama_answer(
    question: str,
    sql_summary: str,
    contexts: list[dict],
    intent: str,
    city: str | None,
    district: str | None,
    tone: str = "advisor",
) -> str | None:
    system_prompt, user_prompt = _build_generation_messages(
        question, sql_summary, contexts, intent, city, district, tone
    )
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "temperature": 0.2,
        },
    }
    req = request.Request(
        f"{OLLAMA_BASE_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=90) as response:
            if response.status != 200:
                return None
            body = json.loads(response.read().decode("utf-8"))
            return body.get("message", {}).get("content", "").strip() or None
    except (error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def generate_openai_compatible_answer(
    question: str,
    sql_summary: str,
    contexts: list[dict],
    intent: str,
    city: str | None,
    district: str | None,
    tone: str = "advisor",
) -> str | None:
    system_prompt, user_prompt = _build_generation_messages(
        question, sql_summary, contexts, intent, city, district, tone
    )
    payload = {
        "model": OPENAI_COMPAT_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = request.Request(
        f"{OPENAI_COMPAT_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_COMPAT_API_KEY}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=90) as response:
            if response.status != 200:
                return None
            body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
    except (error.URLError, TimeoutError, OSError, KeyError, IndexError, json.JSONDecodeError):
        return None

    tone_style = select_tone_style(tone)
    plan = build_answer_plan(sql_summary, contexts, intent, city, district)
    context_text = "\n\n".join(
        f"[{index + 1}] Source={doc['source']} | Score={doc.get('rerank_score', doc.get('score', 0.0)):.3f}\n{doc['content']}"
        for index, doc in enumerate(contexts[:3])
    )
    client = OpenAI()
    system_prompt = (
        "Bạn là chuyên gia phân tích bất động sản Việt Nam. "
        "Luôn ưu tiên số liệu SQL được cung cấp, dùng context truy hồi để giải thích nguyên nhân, "
        "không bịa thông tin ngoài context, và trả lời ngắn gọn nhưng có lập luận. "
        f"Giọng điệu phải {tone_style['voice']}."
    )
    user_prompt = (
        f"Câu hỏi: {question}\n"
        f"Intent: {intent}\n"
        f"City: {city or 'N/A'}\n"
        f"District: {district or 'N/A'}\n"
        f"Số liệu SQL: {sql_summary}\n\n"
        f"Decision frame: {plan['decision_frame']}\n"
        f"Risk angle: {plan['risk_angle']}\n\n"
        f"Context truy hồi:\n{context_text}\n\n"
        "Hãy trả lời bằng tiếng Việt với cấu trúc:\n"
        "1. Kết luận đi thẳng vào quyết định của người hỏi\n"
        "2. 2-3 luận điểm thật sự bám số liệu và context\n"
        "3. 1 cảnh báo/rủi ro\n"
        "Không được mở đầu lan man, không được nhắc lại toàn bộ prompt."
    )
    try:
        response = client.chat.completions.create(
            model=DEFAULT_LLM_MODEL,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def answer_with_context(
    question: str,
    sql_summary: str,
    intent: str = "overview",
    city: str | None = None,
    district: str | None = None,
    tone: str = "advisor",
    contexts: list[dict] | None = None,
) -> dict:
    contexts = contexts if contexts is not None else retrieve_context(question)
    focused_contexts = filter_contexts_for_focus(contexts, city=city, district=district, intent=intent)
    llm_answer = generate_llm_answer(question, sql_summary, focused_contexts, intent, city, district, tone)
    answer = llm_answer or generate_fallback_answer(sql_summary, focused_contexts, intent, city, district, tone)
    return {"answer": answer, "citations": [item["source"] for item in focused_contexts], "contexts": focused_contexts}
