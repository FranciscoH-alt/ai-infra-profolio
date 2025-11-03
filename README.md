# AI Infrastructure & Automation Portfolio (n8n + LLM)

Six showcase projects for GitHub + Upwork.
1) review-summarizer-dashboard
2) excel-ai-assistant
3) faq-chatbot-rag
4) n8n-lead-qual-crm
5) n8n-content-pipeline
6) n8n-ai-reporting
# AI Infrastructure Portfolio

This repository showcases a collection of AI and data automation projects built using **Streamlit** and **n8n**.  
Each project demonstrates practical AI use cases, from natural language dashboards to workflow automation.

---

## Live Apps

| Project | Description | Live Demo |
|----------|--------------|-----------|
| **FAQ Chatbot (RAG)** | A retrieval-based chatbot that answers company FAQs using semantic search. | [Open App](https://ai-infra-profolio-qcamtitn4hrhdtl85w8dpi.streamlit.app/) |
| **Excel AI Assistant** | An AI-powered Excel analyzer that summarizes, cleans, and detects anomalies in uploaded sheets. | [Open App](https://ai-infra-profolio-gpbvhzahbriknsxoszbn8a.streamlit.app/) |
| **n8n AI Reporting** | A Streamlit dashboard for automated business analytics powered by SQL + GPT. | *(Deploy locally or add your own Streamlit link)* |
| **Review Summarizer Dashboard** | An NLP dashboard that analyzes and visualizes customer reviews using sentiment and keyword extraction. | *(Deploy locally or add your own Streamlit link)* |

---

## 🧠 About the Project

This portfolio ties together a complete AI infrastructure:
- **Streamlit** for interactive front-ends  
- **n8n** for workflow automation (lead qualification, content pipelines, etc.)  
- **PostgreSQL / SQLAlchemy** for structured analytics  
- **OpenAI GPT models** for intelligent data interpretation  

Each project folder is self-contained and includes its own `README.md` and `requirements.txt`.

---

## 🛠️ How to Run Locally

```bash
git clone https://github.com/FranciscoH-alt/ai-infra-profolio.git
cd ai-infra-profolio
pip install -r requirements.txt
streamlit run <path_to_app>.py
