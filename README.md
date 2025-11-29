# 📘 EagleEyed — AI-Powered Collaborative Bookkeeping Assistant

EagleEyed is a next-generation financial compliance platform designed to eliminate the manual, error-prone process of entering financial data from passbooks and bank statements.
Using advanced OCR, AI categorization, vector search, and a real-time CA collaboration layer, EagleEyed converts raw paper data into structured, verified, and audit-ready financial records.

---

## 🚀 Overview

In many markets, individuals and small businesses still rely on paper passbooks, printed bank statements, or screenshots to manage their finances. This leaves Chartered Accountants (CAs) drowning in disorganized inputs, manual entry work, and last-minute audit pressure.

EagleEyed solves this by providing a continuous, AI-assisted, real-time bookkeeping ecosystem where clients and CAs collaborate effortlessly.

---

## 🦅 Key Features

### 1️⃣ On-Device & Server-Side OCR

Capture a passbook/statement photo or upload a PDF/Excel file and convert it instantly into structured digital data.

**Benefits for CAs:**
- Removes 60–70% of manual data entry workload.
- Reduces transcription errors caused by unclear handwriting or faded statements.
- Speeds up monthly/quarterly bookkeeping cycles.

---

### 2️⃣ AI-Driven Transaction Structuring

Smart parsing engine cleans OCR text and extracts:
- Date
- Description
- Debit
- Credit
- Balance
- Page references

**Benefits for CAs:**
- Data arrives clean, standardized, and formatted for review.
- No more sorting through mismatched formats or column inconsistencies.
- Sets the stage for automated reconciliation.

---

### 3️⃣ AI Categorization (Gemini + LLM + Vector Search)

Each transaction is extracted from the sheets using OCR and assigned a category using:
- Supabase vector similarity
- Heuristics + Gemini
- LLM validation when confidence is low

**Benefits for CAs:**
- Minimal category correction work.
- Faster month-end closing and tax preparation.
- Personalised categorisation improves over time.
- Fast lookup of transactions and flagging suspicious ones.
- Report and summary generation for better understanding and enhanced workflow.

---

### 4️⃣ Anomaly Detection Engine

Automatically flags:
- Duplicate entries
- Suspicious transaction spikes
- Balance mismatches
- Out-of-pattern spending
- Missing entries or OCR misreads

**Benefits for CAs:**
- Early identification of errors before audit deadlines.
- Ensures cleaner books with fewer manual checks.
- Reduces compliance risks.

---

### 5️⃣ Real-Time Collaboration Dashboard (Supabase Realtime)

CAs get a live, synchronized dashboard where they can:
- Review client entries
- Add comments
- Place audit flags
- Approve corrections
- Request missing documents

**Benefits for CAs:**
- Eliminates back-and-forth WhatsApp and email threads.
- Gets all the client's documents year-wise and month-wise, organised and gathered at a single point.
- Uses secure share links that open only on the site and nowhere else.
- Enables continuous auditing instead of year-end chaos.
- Boosts transparency and traceability.

---

### 6️⃣ AI Advisory Chat Interface

A built-in chat assistant summarises financial patterns and answers questions like:
- “What category saw the highest increase this month?”
- “Show me all anomalies in April.”
- “Why is the electricity expense flagged?”

**Benefits for CAs:**
- Instant financial summaries without manual number crunching.
- Accelerates client advisory and decision-making.
- Converts raw ledger data into actionable insight.

---

### 7️⃣ Privacy by Design — Secure Intelligence

OCR and basic classification run in secure environments.

**Benefits for CAs:**
- Client data remains confidential.
- No raw statements are exposed unnecessarily.
- Adds trust, especially in regulated environments.

---

## 📊 How EagleEyed Transforms a CA’s Workflow

| Traditional Workflow | With EagleEyed |
| :--- | :--- |
| Client sends photos/PDFs at the last minute | Data syncs continuously as client uploads |
| CA manually types 1000s of entries | OCR + AI structuring handles the bulk |
| Category tagging is repetitive | AI auto-categorizes with high confidence |
| Errors found late during audits | Anomaly detection flags them early |
| No version control or audit transparency | Every change logged with time, user, reason |
| Communication via scattered chats | Integrated comment + flagging system |

**Result:**
CAs shift from data clerks → financial strategists.
They spend less time fixing messy inputs and more time providing value to clients.

---

## 🏗 Tech Stack Overview

- **Frontend**: React 18 (Vite) + Tailwind CSS
- **OCR**: Tesseract / EasyOCR / Cloud Vision
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL + pgvector)
- **AI Categorization**: Hybrid (In-house ML + Vector Search + LLM)
- **Realtime Sync**: Supabase Realtime
- **Anomaly Detection**: Rule Engine + Statistical Models
- **Deployment**: Vercel (frontend), Render (backend)

---

## 🔒 Security & Trust

- **Secure Storage**: Documents are encrypted and stored in private buckets.
- **Supabase Auth**: Secures role-based access (client vs CA).
- **Audit Trails**: Every modification is versioned for full transparency.

---

## 📦 Future Roadmap

- [ ] Automated GST categorisation
- [ ] Bank API / UPI integration for live feeds
- [ ] AI-powered audit reports (PDF)
- [ ] Multi-client CA dashboards
- [ ] Cross-device sync
