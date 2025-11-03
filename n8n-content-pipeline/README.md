# n8n – End-to-End AI Content Pipeline

Pulls topics, drafts posts, generates image prompts, publishes to Notion (or CMS) and emails a review link.

## How to Use
1. In n8n → **Workflows** → **Import from file** → select the JSON.
2. Configure credentials (OpenAI, Slack, HubSpot/Notion/Email etc.).
3. Test with sample payloads, then set a Trigger (Webhook/Cron).

### Environment Variables
- `OPENAI_API_KEY`
- `NOTION_TOKEN`
- `EMAIL_CREDENTIALS`
## High-Level Steps
1) Cron/RSS → 2) OpenAI draft → 3) Image prompt → 4) Notion publish → 5) Email reviewer
