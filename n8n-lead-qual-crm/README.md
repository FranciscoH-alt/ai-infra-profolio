# n8n – AI Lead Qualification & CRM Integration

Webhook ingests leads, GPT scores/summarizes, IF gate routes high scorers to CRM and Slack. Also logs to Sheets (optional).

## How to Use
1. In n8n → **Workflows** → **Import from file** → select the JSON.
2. Configure credentials (OpenAI, Slack, HubSpot/Notion/Email etc.).
3. Test with sample payloads, then set a Trigger (Webhook/Cron).

### Environment Variables
- `OPENAI_API_KEY`
- `SLACK_TOKEN`
- `HUBSPOT_API_KEY (or Notion token)`
## High-Level Steps
1) Webhook → 2) OpenAI Chat → 3) IF (score>70) → 4) Create Contact (CRM) → 5) Slack alert
