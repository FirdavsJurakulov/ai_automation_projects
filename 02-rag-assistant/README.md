# Demo 2 — Agency Knowledge Assistant (RAG)

**Pitch:** «Сотрудники агентства тратят время, ища цены, бренд-гайды клиентов и правила в разных документах.
Этот ассистент отвечает на вопросы по внутренним документам за секунды, на русском, узбекском или английском,
со ссылкой на источник — и честно говорит "этого нет", вместо того чтобы выдумывать.»

```
docs/*.md|pdf ─► chunk (500 chars, 100 overlap) ─► Gemini embeddings ─► ChromaDB (cosine)
question ─► embed ─► top-4 chunks ─► Gemini (grounded prompt + citations) ─► answer + sources
```

## Setup (≈30 min, free)
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # paste your GEMINI_API_KEY
python ingest.py            # → "Indexed N chunks"
streamlit run app.py        # opens http://localhost:8501
```
Free hosting for a live link: push to GitHub → https://share.streamlit.io → add `GEMINI_API_KEY` in *Secrets*
(and run `python ingest.py` once in the app via the sidebar "Переиндексировать" button).

## Demo script (60 sec recording)
1. «Сколько стоит пакет «Рост» и есть ли скидка при оплате за полгода?» → 11 млн сум, 15% [01-uslugi-i-ceny.md]
2. «Какие цвета и тон у Chaikhana Lounge?» → brand guide answer with citation
3. «Qancha oldindan to'lov kerak?» (Uzbek) → 50% prepayment, answered in Uzbek
4. «Можно взять клиента — пивной бар?» → No, policy [04-politiki-i-faq.md]
5. «Сколько стоит SEO?» → «В документах агентства этого нет» ← **shows it doesn't hallucinate**
6. Upload a new PDF in the sidebar → re-index → ask about it.

## The sample docs
`docs/` holds a fictional agency "Nova Digital" (prices, onboarding, a client brand guide, policies) so the demo
looks like *their* world. Swap in any real public docs you like.

## What to explain if asked
- **Why chunk + overlap:** small chunks = precise retrieval; overlap keeps facts that cross a boundary.
- **Why cosine similarity / ChromaDB:** local, free, persistent; swap for Qdrant/pgvector/Pinecone in production.
- **Grounding:** system prompt forces answers only from context + citations; temperature 0.1.
- **Evaluation:** keep a list of 20 Q&A pairs, check retrieval hit-rate (is the right file in top-4?) and answer correctness.
- **Upgrades:** hybrid search (BM25 + vectors), re-ranking, metadata filters per client, a Telegram front-end via n8n
  (connect to Demo 1!), auto re-index when a Google Drive folder changes.
