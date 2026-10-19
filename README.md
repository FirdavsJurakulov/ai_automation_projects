# AI Automation Demos — Firdavs Jurakulov

Two portfolio demos for an AI Automation Engineer role. Both run **100% free**
(Gemini API free tier + self-hosted n8n + local vector DB).

| Demo                   | What it shows                                                                        | Stack                                                                        |
| ---------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `01-telegram-lead-bot` | AI agent that qualifies leads from Telegram and logs them to Google Sheets           | n8n, Telegram Bot API, Gemini API (structured JSON), Google Sheets, Webhooks |
| `02-rag-assistant`     | Chatbot that answers questions about an agency's internal docs with source citations | Python, Gemini embeddings + LLM, ChromaDB, Streamlit                         |

## Free API key (needed for both)

1. Go to https://aistudio.google.com/apikey → **Create API key** (sign in with Google, no card).
2. Keep it secret. Never commit it to GitHub (use `.env`, already in `.gitignore`).

Models used (free tier, Oct 2026): `gemini-3.8-flash` (LLM), `gemini-embedding-2` (embeddings).
If a model name changes, update it in one place: `.env` / the n8n HTTP node URL.

## Put them on GitHub

1. New repo `ai-automation-demos` → upload this folder (the `.gitignore` keeps keys out).
2. Add each demo's screen recording (GIF or MP4) at the top of its README.
3. Pin the repo on your GitHub profile and add both to your CV under _Selected Projects_:
   - **AI Lead Qualifier** — n8n workflow: Telegram bot + Gemini structured output + Google Sheets + hot-lead alerts.
   - **Agency Knowledge Assistant (RAG)** — Python, Gemini embeddings, ChromaDB, Streamlit; grounded answers with citations in RU/UZ/EN.
