



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

https://github.com/user-attachments/assets/f0bbc7ce-a644-4a43-bbbf-53c1817e4d57

https://github.com/user-attachments/assets/d47c8f00-b294-4a85-a720-a864902bebe8


