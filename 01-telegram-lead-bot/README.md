# Demo 1 — AI Lead Qualifier (Telegram → Gemini → Google Sheets)

**Pitch (say this in the interview):** «Клиент пишет в Telegram — AI-агент понимает запрос на любом из трёх языков,
вытаскивает услугу, бюджет и контакты в JSON, оценивает лида от 1 до 10, пишет ответ клиенту,
логирует всё в Google Sheets и присылает менеджеру алерт, если лид горячий. Ноль ручной работы.»

```
Telegram Trigger ─► Gemini (structured JSON) ─► Code: parse ─┬─► Google Sheets (log) ─► IF score≥7 ─► Alert manager
                                                             └─► Reply to client
```

## Setup (≈1–2 hours, all free)

### 1. Telegram bot (5 min)
- In Telegram open **@BotFather** → `/newbot` → pick a name → copy the **token**.
- Get your own chat id: message **@userinfobot** → copy the number → this is `MANAGER_CHAT_ID`.

### 2. Google Sheet (5 min)
- Create a sheet, rename the tab to **Leads**, put these headers in row 1:
  `date | chat_id | username | message | name | phone | service | budget_uzs | urgency | language | lead_score | summary`

### 3. Run n8n locally (15 min)
Telegram webhooks need a public HTTPS URL, so use a free tunnel:
```bash
# terminal 1 — free tunnel (pick one)
ngrok http 5678            # https://ngrok.com (free account)
# or: cloudflared tunnel --url http://localhost:5678

# terminal 2
cp .env.example .env       # fill GEMINI_API_KEY, MANAGER_CHAT_ID, WEBHOOK_URL (the https URL from the tunnel)
docker compose up -d
```
Open http://localhost:5678 and create the owner account.

> No Docker? `npx n8n` also works (Node 20+), set the same env vars in your shell.

### 4. Import the workflow (15 min)
- n8n → **Workflows → Import from file** → `lead-bot-workflow.json`.
- **Telegram Trigger / Reply / Alert** nodes → Credentials → *Create new* → paste the BotFather token.
- **Log to Google Sheets** → Credentials → Google Sheets OAuth2 (follow n8n's in-app guide) → paste your sheet URL.
- Click **Execute workflow**, send a test message from `sample-messages.md`, check each node's output.
- Toggle **Active** — now it runs 24/7 while your laptop + tunnel are on.

### 5. Record the demo (10 min)
Screen-record: send message #1 in Telegram → bot replies → new row appears in Sheets → manager alert arrives.
30–60 seconds. Put the video + screenshots of the n8n canvas in the GitHub README.

## What to explain if asked
- **Why JSON mode:** `responseMimeType: application/json` + low temperature (0.2) = predictable, parseable output.
- **Error handling:** the Code node falls back to a safe reply if parsing fails. Upgrade: n8n *Error Trigger* workflow that pings you on failures.
- **Prompt design:** strict schema, enum for `service`, explicit scoring rubric, "never invent data" to limit hallucinations.
- **Upgrades you can mention:** conversation memory per `chat_id` (n8n AI Agent node + Window Buffer Memory), push to a CRM (amoCRM/Bitrix24 via their REST API), voice messages via Gemini audio transcription, swap Gemini for Claude/OpenAI by changing one HTTP node.
