"""Minimal, dependency-light RAG: Gemini embeddings + ChromaDB + Gemini answer with citations."""
import logging
import os
import re
import time
from pathlib import Path

import chromadb
import requests
from dotenv import load_dotenv

load_dotenv()
API = "https://generativelanguage.googleapis.com/v1beta/models"
KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.8-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-2")
DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION = "agency_docs"


log = logging.getLogger(__name__)


class RagError(Exception):
    """Error with a short, user-facing message. Technical details go to the log."""


def _api_error(r: requests.Response, url: str) -> RagError:
    try:
        err = r.json().get("error", {})
        detail = err.get("message", "")
    except ValueError:
        detail = r.text[:500]
    log.error("Gemini API %s for %s: %s", r.status_code, url.split("?")[0], detail)
    model = url.rsplit("/", 1)[-1].split(":")[0]
    if r.status_code == 400 and "api key" in detail.lower():
        return RagError("Неверный GEMINI_API_KEY. Проверьте ключ в файле .env.")
    if r.status_code in (401, 403):
        return RagError("Нет доступа к Gemini API: ключ недействителен или у него нет прав на эту модель.")
    if r.status_code == 404:
        return RagError(f"Модель «{model}» не найдена. Проверьте LLM_MODEL / EMBED_MODEL в .env.")
    if r.status_code == 429:
        return RagError("Превышен лимит запросов к Gemini API. Подождите минуту и попробуйте снова.")
    if r.status_code >= 500:
        return RagError("Сервис Gemini временно недоступен. Попробуйте ещё раз чуть позже.")
    return RagError(f"Gemini API отклонил запрос (код {r.status_code}).")


def _post(url: str, body: dict, retries: int = 3) -> dict:
    if not KEY:
        raise RagError("Не задан GEMINI_API_KEY. Добавьте его в файл .env и перезапустите приложение.")
    for attempt in range(retries):
        try:
            r = requests.post(url, json=body, headers={"x-goog-api-key": KEY}, timeout=60)
        except requests.Timeout:
            log.exception("Gemini API timeout")
            raise RagError("Gemini API не ответил вовремя. Попробуйте ещё раз.") from None
        except requests.RequestException:
            log.exception("Gemini API connection error")
            raise RagError("Не удалось связаться с Gemini API. Проверьте подключение к интернету.") from None
        # free-tier rate limit / transient server errors
        if r.status_code in (429, 500, 503) and attempt < retries - 1:
            time.sleep(5 * (attempt + 1))
            continue
        if not r.ok:
            raise _api_error(r, url)
        try:
            return r.json()
        except ValueError:
            log.error("Non-JSON response from Gemini API: %s", r.text[:500])
            raise RagError("Gemini API вернул некорректный ответ.") from None
    raise RagError("Gemini API не отвечает. Попробуйте позже.")


# ---------- 1. Load & chunk ----------
def load_documents(folder: str) -> list[dict]:
    docs = []
    for path in sorted(Path(folder).glob("*")):
        if path.suffix.lower() in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8")
        elif path.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            text = "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
        else:
            continue
        docs.append({"source": path.name, "text": text})
    return docs


def chunk_text(text: str, max_chars: int = 500, overlap: int = 100) -> list[str]:
    """Split on paragraphs/headings first, then pack into ~max_chars chunks with overlap."""
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=#)", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 1 <= max_chars:
            cur = f"{cur}\n{p}".strip()
        else:
            if cur:
                chunks.append(cur)
            tail = cur[-overlap:] if cur else ""
            cur = f"{tail}\n{p}".strip() if len(p) < max_chars else p
            while len(cur) > max_chars:
                chunks.append(cur[:max_chars])
                cur = cur[max_chars - overlap:]
    if cur:
        chunks.append(cur)
    return chunks


# ---------- 2. Embed ----------
def embed(texts: list[str]) -> list[list[float]]:
    out = []
    for i in range(0, len(texts), 50):
        batch = texts[i:i + 50]
        body = {"requests": [{"model": f"models/{EMBED_MODEL}",
                              "content": {"parts": [{"text": t}]}} for t in batch]}
        data = _post(f"{API}/{EMBED_MODEL}:batchEmbedContents", body)
        out.extend(e["values"] for e in data["embeddings"])
    return out


# ---------- 3. Store ----------
def get_collection():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def build_index(folder: str = "docs", embed_fn=embed) -> int:
    ids, texts, metas = [], [], []
    for doc in load_documents(folder):
        for j, ch in enumerate(chunk_text(doc["text"])):
            ids.append(f"{doc['source']}::{j}")
            texts.append(ch)
            metas.append({"source": doc["source"], "chunk": j})
    if not ids:
        raise RagError(f"В папке «{folder}» нет документов (.md / .txt / .pdf) для индексации.")
    embeddings = embed_fn(texts)  # embed first, so an API failure doesn't wipe the existing index
    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    col = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    col.add(ids=ids, documents=texts, metadatas=metas, embeddings=embeddings)
    return len(ids)


# ---------- 4. Retrieve ----------
def retrieve(question: str, k: int = 4, embed_fn=embed) -> list[dict]:
    col = get_collection()
    if col.count() == 0:
        raise RagError("Индекс документов пуст. Нажмите «Переиндексировать» в боковой панели.")
    res = col.query(query_embeddings=embed_fn([question]), n_results=min(k, col.count()))
    return [{"text": d, "source": m["source"], "score": round(1 - dist, 3)}
            for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])]


# ---------- 5. Generate ----------
SYSTEM = """Ты — внутренний AI-ассистент маркетингового агентства. Отвечай ТОЛЬКО на основе фрагментов документов ниже.
Если ответа в документах нет — честно скажи: «В документах агентства этого нет» и предложи, у кого уточнить.
Отвечай на языке вопроса (русский, узбекский или английский), коротко и по делу.
После каждого факта ставь ссылку на источник в квадратных скобках, например [01-uslugi-i-ceny.md]."""


def answer(question: str, history: list[dict] | None = None, k: int = 4) -> dict:
    hits = retrieve(question, k)
    context = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    contents = []
    for turn in (history or [])[-6:]:  # short conversation memory
        contents.append({"role": "user" if turn["role"] == "user" else "model",
                         "parts": [{"text": turn["content"]}]})
    contents.append({"role": "user", "parts": [{"text": f"Документы:\n{context}\n\nВопрос: {question}"}]})
    body = {"systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.1}}
    data = _post(f"{API}/{LLM_MODEL}:generateContent", body)
    return {"answer": _extract_text(data), "sources": hits}


def _extract_text(data: dict) -> str:
    if reason := data.get("promptFeedback", {}).get("blockReason"):
        log.warning("Prompt blocked: %s", reason)
        raise RagError("Модель отказалась обрабатывать этот запрос. Попробуйте переформулировать вопрос.")
    candidates = data.get("candidates") or []
    if not candidates:
        log.error("No candidates in Gemini response: %s", data)
        raise RagError("Модель не вернула ответ. Попробуйте ещё раз.")
    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        reason = candidates[0].get("finishReason", "UNKNOWN")
        log.warning("Empty answer, finishReason=%s", reason)
        if reason in ("SAFETY", "RECITATION", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII"):
            raise RagError("Ответ был заблокирован фильтрами модели. Попробуйте переформулировать вопрос.")
        raise RagError("Модель вернула пустой ответ. Попробуйте ещё раз.")
    return text
