# n8n – AI Reporting Infrastructure

Pulls metrics from APIs/Sheets/DB, summarizes with GPT, and emails the report automatically.

## How to Use
1. In n8n → **Workflows** → **Import from file** → select the JSON.
2. Configure credentials (OpenAI, Slack, HubSpot/Notion/Email etc.).
3. Test with sample payloads, then set a Trigger (Webhook/Cron).

### Environment Variables
- `OPENAI_API_KEY`
- `EMAIL_CREDENTIALS`
- `SOURCE_API_KEYS`
## High-Level Steps
1) Cron → 2) Fetch metrics → 3) GPT summary → 4) Email
