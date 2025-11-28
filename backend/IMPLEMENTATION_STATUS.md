# Eagle Eyed Backend - The Bible 📖

This document serves as the single source of truth for the Eagle Eyed backend implementation, status, configuration, and architecture.

---

## 1. ✅ Implemented Services & Logic (Core Idea)

The following components are fully implemented and production-ready (logic-wise).

### **Core Services**
-   **Authentication**: `AuthService` (Supabase integration), `UserService`, `ClientService`.
-   **Transactions**: `TransactionService` (CRUD, bulk ops, filtering), `SheetService` (Import from Excel/CSV/JSON).
-   **Ledger Classification**: `LedgerClassifierService` (Rule-based), `LedgerRulesEngine` (30+ categories, GST/TDS logic).
-   **Query Engine**: `QueryService` (Natural Language to SQL, RAG integration for compliance context).
-   **Recycle Bin**: `RecycleBinService` (Soft delete, restore, permanent delete, auto-cleanup).

### **Compliance & Reporting**
-   **GST Compliance**: `GSTComplianceService` (ITC eligibility, Section 17(5) checks, RCM detection, Purchase Register Analysis).
-   **TDS Engine**: `TDSEngine` (Threshold checks for 194C/J/I/H/A, rate calculation).
-   **Financial Reports**:
    -   `PnLGenerator` (Profit & Loss).
    -   `BalanceSheetGenerator` (Assets/Liabilities/Equity).
    -   `TrialBalanceGenerator` (Ledger verification).
    -   `CashflowGenerator` (Operating/Investing/Financing).
-   **Periodic Tasks**:
    -   `MonthlyClosingService` (Bank Reconciliation, GST Summary, Debtors/Creditors).
    -   `QuarterlyTaskService` (TDS/Advance Tax estimation).
    -   `YearEndWorkingPapersService` (Depreciation, FAR, Audit Trail).

### **Document Processing**
-   **Document Management**: `DocumentService` (Upload, storage, type detection).
-   **Parsers**: `BankStatementParser` (CSV/Excel), `InvoiceParser` (PDF text), `GSTJSONParser`.
-   **OCR**: `OCRService` (Tesseract/PDF2Image integration for text/tables).

### **Utilities & Middleware**
-   **Security**: `JWTVerificationMiddleware`, `RoleEnforcementMiddleware`, `MultiTenantRLSMiddleware`.
-   **Helpers**: `PDFUtils`, `SQLBuilder`, `DateUtils`, `AmountUtils`, `SystemMonitor`.

---

## 2. ⚠️ Partial / Future Implementations

These features have placeholder logic or require external API integration to be fully effective.

| Component | Status | Missing / Future Work |
| :--- | :--- | :--- |
| **GSTR-2B Sync** | Partial | `reconcile_gstr2b` in `GSTComplianceService` analyzes local books but needs **GST Portal API** integration to fetch actual GSTR-2B data. |
| **RAG Embeddings** | Partial | `EmbeddingService` has the logic but requires an **OpenAI API Key** to generate real vectors. Currently returns zero-vectors if no key is present. |
| **OCR Engine** | Partial | `OCRService` requires **Tesseract** and **Poppler** installed on the host OS to function. |
| **Return Filing** | Future | `ReturnFilingService` orchestrates logic but does not actually push data to the GST portal (requires GSP integration). |
| **Advanced Compliance** | Future | `CompaniesActChecker`, `MSMECompliance` are skeleton structures for future expansion. |

---

## 3. 🔑 User Input Required (Configuration)

You must provide the following inputs for the system to function correctly.

### **A. Environment Variables (`.env` / `backend/config.py`)**
| Variable | Description | Required? |
| :--- | :--- | :--- |
| `SUPABASE_URL` | Your Supabase Project URL | **YES** |
| `SUPABASE_KEY` | Your Supabase Anon/Service Role Key | **YES** |
| `JWT_SECRET_KEY` | Secret for signing auth tokens | **YES** |
| `OPENAI_API_KEY` | Key for RAG/Embeddings (OpenAI) | Optional (for AI features) |
| `DATABASE_URL` | PostgreSQL Connection String | Optional (if using direct DB) |
| `REDIS_URL` | Redis Connection String | Optional (for caching) |

### **B. System Dependencies**
These must be installed on the server/machine running the backend:
1.  **Tesseract OCR**:
    -   Windows: [Installer](https://github.com/UB-Mannheim/tesseract/wiki) (Add to PATH)
    -   Linux: `sudo apt-get install tesseract-ocr`
2.  **Poppler** (for PDF processing):
    -   Windows: [Binary](http://blog.alivate.com.au/poppler-windows/) (Add `bin` to PATH)
    -   Linux: `sudo apt-get install poppler-utils`

### **C. Python Packages**
-   `pip install openai` (Required for RAG features)

---

## 4. 🏗️ Overall Backend Structure

```
backend/
│
├── main.py                 # Application entry point. Initializes FastAPI, CORS, Middleware, and Routers.
├── config.py               # Environment configuration. Loads .env variables (Supabase URL, Keys, etc.).
├── requirements.txt        # Python dependencies list.
├── schema.sql              # Database schema definitions (Tables, RLS policies, Indexes).
├── updates.sql             # SQL script for applying recent schema updates/migrations.
├── drop_tables.sql         # Utility script to drop all tables (for reset).
│
├── routers/                # API Route definitions (Controllers)
│   ├── auth_router.py              # Endpoints for Login, Signup, Token Refresh.
│   ├── user_router.py              # User profile management endpoints.
│   ├── client_router.py            # Client entity CRUD endpoints.
│   ├── sheet_router.py             # Financial sheet management endpoints.
│   ├── transaction_router.py       # Transaction CRUD, filtering, and bulk operations.
│   ├── document_router.py          # Document upload, listing, and metadata management.
│   ├── import_router.py            # Endpoints for importing data from external sources.
│   ├── ocr_router.py               # OCR processing trigger endpoints.
│   ├── ledger_classifier_router.py # Ledger classification trigger and review endpoints.
│   ├── compliance_router.py        # Compliance check triggers (GST, TDS, etc.).
│   ├── redflag_router.py           # Red flag (anomaly) management endpoints.
│   ├── query_router.py             # Natural Language Query interface endpoints.
│   ├── rag_router.py               # RAG context retrieval and management endpoints.
│   ├── report_router.py            # Financial report generation (P&L, BS) endpoints.
│   ├── return_filing_router.py     # GSTR and TDS return preparation endpoints.
│   ├── share_router.py             # Secure document sharing endpoints.
│   ├── admin_router.py             # System administration and monitoring endpoints.
│   ├── health_router.py            # Health check endpoint for system status.
│   ├── settings_router.py          # User and Application settings endpoints.
│   └── recycle_bin_router.py       # Soft-delete management (restore/permanent delete).
│
├── services/               # Business logic & Database interactions
│   ├── auth_service.py             # Logic for authentication and token management.
│   ├── user_service.py             # Logic for user profile handling.
│   ├── client_service.py           # Logic for client creation and management.
│   ├── sheet_service.py            # Logic for sheet organization and lifecycle.
│   ├── transaction_service.py      # Core transaction logic (CRUD, Bulk Insert).
│   ├── transaction_extraction_service.py # Logic for extracting transactions from documents.
│   │
│   ├── document_intake/            # Document processing pipeline
│   │   ├── document_service.py         # Orchestrates document upload and storage.
│   │   ├── document_classifier.py      # Determines document type (Invoice, Bank Stmt, etc.).
│   │   ├── file_sorter.py              # Organizes files into appropriate folders.
│   │   ├── metadata_extractor.py       # Extracts basic metadata (Date, Vendor) from files.
│   │   ├── bank_statement_parser.py    # Parses CSV/Excel bank statements.
│   │   ├── invoice_parser.py           # Parses PDF invoices (Text-based).
│   │   ├── gst_json_parser.py          # Parses GST Portal JSON files.
│   │   └── payment_gateway_parser.py   # Parses payment gateway reports.
│   │
│   ├── ocr/                        # OCR capabilities
│   │   ├── ocr_service.py              # Interface for Tesseract/Textract OCR.
│   │   └── table_extractor.py          # Specialized logic for extracting tables from PDFs.
│   │
│   ├── ledger_classifier/          # AI & Rule-based Classification
│   │   ├── ledger_classifier_service.py # Main service for assigning ledgers to transactions.
│   │   ├── ledger_rules_engine.py      # Rule-based classification logic (Regex/Keyword).
│   │   └── recurrence_detector.py      # Detects recurring transactions for auto-classification.
│   │
│   ├── compliance_engine/          # Regulatory Compliance Logic
│   │   ├── gst_compliance.py           # GST Rules (ITC, RCM, Mismatches).
│   │   ├── tds_engine.py               # TDS Rules (Thresholds, Rates).
│   │   ├── income_tax_compliance.py    # Income Tax Rules (Disallowances).
│   │   ├── depreciation_engine.py      # Fixed Asset Depreciation calculation.
│   │   ├── disallowance_checker.py     # Checks for specific disallowance sections (40A(3)).
│   │   ├── companies_act_checker.py    # Companies Act compliance checks.
│   │   └── msme_compliance.py          # MSME 45-day payment rule checks.
│   │
│   ├── red_flag_engine/            # Anomaly Detection
│   │   ├── anomaly_detector.py         # General anomaly detection logic.
│   │   ├── duplicate_detector.py       # Identifies duplicate transactions.
│   │   ├── gst_mismatch_detector.py    # Checks for GST vs Books mismatches.
│   │   ├── missing_invoice_detector.py # Identifies transactions missing supporting docs.
│   │   ├── suspicious_vendor_detector.py # Flags unknown or risky vendors.
│   │   ├── cash_transaction_checker.py # Flags cash transactions exceeding limits.
│   │   └── pattern_analysis.py         # Analyzes transaction patterns for irregularities.
│   │
│   ├── query_engine/               # AI Query System
│   │   ├── query_service.py            # Orchestrates NL to SQL/Answer flow.
│   │   ├── query_llm.py                # Interface with LLM for query understanding.
│   │   ├── query_validator.py          # Validates generated SQL/Answers.
│   │   ├── query_templates.py          # Pre-defined SQL templates for common queries.
│   │   └── query_translator.py         # Converts Natural Language to SQL.
│   │
│   ├── rag_service/                # Retrieval Augmented Generation
│   │   ├── rag_manager.py              # Manages the RAG pipeline.
│   │   ├── embedding_service.py        # Generates vector embeddings for text.
│   │   ├── retrieval_service.py        # Retrieves relevant chunks from vector store.
│   │   └── prompt_builder.py           # Constructs prompts with retrieved context.
│   │
│   ├── report_engine/              # Financial Reporting
│   │   ├── pnl_generator.py            # Generates Profit & Loss statement.
│   │   ├── balance_sheet_generator.py  # Generates Balance Sheet.
│   │   ├── trial_balance_generator.py  # Generates Trial Balance.
│   │   ├── monthly_closing.py          # Logic for monthly book closing.
│   │   ├── quarterly_tasks.py          # Logic for quarterly compliance tasks.
│   │   ├── year_end_working_papers.py  # Generates year-end audit working papers.
│   │   ├── cashflow_report.py          # Generates Cashflow Statement.
│   │   ├── cashflow_generator.py       # Helper for cashflow calculations.
│   │   └── working_paper_generator.py  # Generic working paper generation logic.
│   │
│   ├── return_filing/              # Tax Return Preparation
│   │   ├── gstr1_prepare.py            # Prepares GSTR-1 data.
│   │   ├── gstr1_service.py            # Service for GSTR-1 operations.
│   │   ├── gstr3b_prepare.py           # Prepares GSTR-3B data.
│   │   ├── gstr3b_service.py           # Service for GSTR-3B operations.
│   │   ├── tds_summary.py              # Generates TDS summary.
│   │   ├── tds_return_service.py       # Service for TDS return operations.
│   │   ├── advance_tax_calc.py         # Calculates Advance Tax liability.
│   │   ├── advance_tax_service.py      # Service for Advance Tax operations.
│   │   ├── reconciliation_service.py   # Reconciles books with returns.
│   │   └── return_filing_service.py    # Orchestrator for return filing workflows.
│   │
│   ├── sharing/                    # Sharing Logic
│   │   ├── share_token_service.py      # Manages generation/validation of share tokens.
│   │   └── link_resolver_service.py    # Resolves shared links to resources.
│   │
│   └── admin/                      # Admin Services
│       ├── admin_service.py            # General admin operations.
│       └── system_monitor.py           # System health and performance monitoring.
│
├── models/                 # Pydantic data models (Schemas)
│   ├── auth_models.py              # Auth request/response schemas.
│   ├── user_models.py              # User data schemas.
│   ├── client_models.py            # Client data schemas.
│   ├── sheet_models.py             # Sheet data schemas.
│   ├── transaction_models.py       # Transaction data schemas.
│   ├── document_models.py          # Document metadata schemas.
│   ├── ledger_models.py            # Ledger classification schemas.
│   ├── compliance_models.py        # Compliance check result schemas.
│   ├── redflag_models.py           # Red flag schemas.
│   ├── query_models.py             # Query engine schemas.
│   ├── rag_models.py               # RAG embedding/retrieval schemas.
│   ├── report_models.py            # Financial report schemas.
│   ├── return_filing_models.py     # Return filing data schemas.
│   ├── share_models.py             # Share token schemas.
│   ├── admin_models.py             # Admin log schemas.
│   ├── response_models.py          # Standard API response schemas.
│   └── recycle_bin_models.py       # Recycle bin item schemas.
│
├── middleware/             # Custom middleware
│   ├── jwt_verification.py         # Validates JWT tokens.
│   ├── role_enforcement.py         # Enforces RBAC (Role Based Access Control).
│   └── multi_tenant_rls.py         # Sets RLS context for multi-tenancy.
│
├── workers/                # Background Workers (Celery/Async)
│   ├── ocr_worker.py               # Handles async OCR tasks.
│   ├── embedding_worker.py         # Handles async text embedding tasks.
│   ├── document_intake_worker.py   # Handles async document processing.
│   ├── law_crawler_worker.py       # Crawls legal websites for updates.
│   ├── scheme_crawler_worker.py    # Crawls govt scheme websites.
│   ├── redflag_worker.py           # Runs anomaly detection in background.
│   ├── batch_classification_worker.py # Runs bulk ledger classification.
│   └── return_filing_worker.py     # Prepares return data in background.
│
├── crawlers/               # Web Crawlers for Legal Data
│   ├── gst_crawler.py              # Crawls GST notifications/circulars.
│   ├── income_tax_crawler.py       # Crawls Income Tax updates.
│   ├── companies_act_crawler.py    # Crawls MCA updates.
│   ├── rbi_crawler.py              # Crawls RBI notifications.
│   ├── fema_crawler.py             # Crawls FEMA updates.
│   ├── msme_crawler.py             # Crawls MSME updates.
│   ├── epf_esic_crawler.py         # Crawls EPF/ESIC updates.
│   ├── icai_guidance_crawler.py    # Crawls ICAI guidance notes.
│   └── govt_schemes_crawler.py     # Crawls government schemes.
│
├── rag/                    # RAG Core Logic
│   ├── embedder.py                 # Core embedding logic (OpenAI wrapper).
│   ├── retriever.py                # Core retrieval logic (Vector search).
│   ├── chunker.py                  # Text chunking logic.
│   ├── vector_store.py             # Database interface for vector operations.
│   ├── prompt_templates.py         # Templates for LLM prompts.
│   └── law_scheme_indexer.py       # Indexes legal documents into vector store.
│
├── scripts/                # Utility Scripts
│   └── init_storage.py             # Initializes Supabase storage buckets.
│
└── utils/                  # Shared Utility Functions
    ├── file_utils.py               # File handling helpers.
    ├── date_utils.py               # Date parsing/formatting helpers.
    ├── amount_utils.py             # Currency formatting/parsing helpers.
    ├── gst_utils.py                # GSTIN validation/parsing helpers.
    ├── income_tax_utils.py         # PAN validation/parsing helpers.
    ├── logger.py                   # Centralized logging configuration.
    ├── decorators.py               # Common decorators (timing, retry).
    ├── supabase_client.py          # Singleton Supabase client instance.
    ├── pdf_utils.py                # PDF manipulation helpers.
    └── sql_builder.py              # Dynamic SQL generation helpers.
```

---

## 5. �️ Frontend Architecture

```
frontend/
├── .gitignore              # Git ignore rules.
├── README.md               # Frontend specific documentation.
├── eslint.config.js        # ESLint configuration.
├── index.html              # HTML entry point.
├── package.json            # NPM dependencies and scripts.
├── postcss.config.js       # PostCSS configuration.
├── tailwind.config.js      # Tailwind CSS configuration.
├── vite.config.js          # Vite build configuration.
│
├── src/
│   ├── App.css             # Component-specific styles.
│   ├── App.tsx             # Main Application component & Routing logic.
│   ├── index.css           # Global styles & Tailwind directives.
│   ├── main.tsx            # React entry point.
│   │
│   ├── assets/             # Static assets
│   │   └── react.svg       # React logo.
│   │
│   ├── context/            # Global State Management
│   │   └── AuthContext.tsx # Authentication state (User, Session, Login/Logout).
│   │
│   ├── layouts/            # Page Layouts
│   │   └── MainLayout.tsx  # Primary layout with Sidebar, Header, and Content area.
│   │
│   ├── pages/              # Application Views
│   │   ├── Dashboard.tsx           # Main dashboard with stats and quick actions.
│   │   ├── Login.tsx               # User login page.
│   │   ├── Signup.tsx              # User registration page.
│   │   ├── ClientManager.tsx       # Client list and management interface.
│   │   ├── ClientDashboard.tsx     # Specific client overview.
│   │   ├── SheetsView.tsx          # Financial sheets hierarchical view (Client->Year->Month).
│   │   ├── TransactionsView.tsx    # Detailed transaction list (placeholder/component).
│   │   ├── DocumentUpload.tsx      # File upload interface with drag-and-drop.
│   │   ├── AIChat.tsx              # AI Assistant chat interface.
│   │   ├── Settings.tsx            # User settings page.
│   │   ├── SharedDocumentsList.tsx # List of documents shared with the user.
│   │   ├── SharedDocumentView.tsx  # Public/Private view for shared documents.
│   │   └── AcceptInvite.tsx        # Page to accept shared document invites.
│   │
│   └── services/           # API Integration
│       └── api.ts          # Axios instance with interceptors for Auth headers.
```

---

## 6. �🗄️ Database Structure (Supabase/PostgreSQL)

### **Core Tables**
-   **`users`**: Synced with Supabase Auth. Roles: `admin`, `ca`, `client`.
-   **`clients`**: Business profiles managed by CAs.
-   **`sheets`**: Financial datasets (e.g., "FY 2023-24 Bank Statement").
-   **`transactions`**: The central ledger. Stores date, amount, description, ledger category, GSTIN, etc.
-   **`documents`**: Metadata for uploaded files (linked to Storage).

### **Compliance & Audit**
-   **`red_flags`**: Anomalies detected (duplicates, cash limits).
-   **`recycle_bin`**: Soft-deleted items (30-day retention).
-   **`admin_logs`**: Audit trail of system actions.

### **RAG & AI**
-   **`embeddings`**: Stores vector embeddings of legal texts/documents (pgvector).

### **Access Control**
-   **`share_tokens`**: Secure links for sharing reports.
-   **`share_access_logs`**: Access history for shared links.

---

## 7. 🔄 Data Flow Architecture

```mermaid
graph TD
    User[User (Client/CA)] -->|API Request (JWT)| API[FastAPI Backend]
    
    subgraph "Middleware Layer"
        API --> Auth[Auth Middleware]
        Auth --> RBAC[Role Check]
        RBAC --> RLS[RLS Context]
    end
    
    subgraph "Service Layer"
        RLS --> DocService[Document Service]
        RLS --> TxnService[Transaction Service]
        RLS --> ReportService[Report Engine]
        RLS --> QueryService[Query Engine]
    end
    
    subgraph "Processing Engines"
        DocService -->|File| OCR[OCR / Parsers]
        TxnService -->|Data| Classifier[Ledger Classifier]
        TxnService -->|Data| Compliance[Compliance Engine]
        TxnService -->|Data| Anomaly[Red Flag Engine]
        QueryService -->|Query| RAG[RAG / Embeddings]
    end
    
    subgraph "Data Layer (Supabase)"
        OCR -->|Extracted Data| DB[(PostgreSQL)]
        Classifier -->|Categorized Txns| DB
        Compliance -->|Flags/Reports| DB
        ReportService -->|Fetch Data| DB
        RAG -->|Vector Search| DB
    end
    
    subgraph "External"
        RAG -->|Generate Vector| OpenAI[OpenAI API]
        Compliance -.->|Future| GSTPortal[GST Portal API]
    end
```

### **Flow Description**
1.  **Input**: User uploads a document (Bank Statement/Invoice).
2.  **Processing**:
    -   `DocumentService` saves file to Storage.
    -   `OCR/Parser` extracts text/tables.
    -   `TransactionService` normalizes data into the `transactions` table.
3.  **Enrichment**:
    -   `LedgerClassifier` assigns categories (e.g., "Rent", "Sales").
    -   `ComplianceEngine` checks for GST/TDS violations.
    -   `AnomalyDetector` scans for red flags.
4.  **Consumption**:
    -   User requests a **Report** (P&L, GST Summary).
    -   `ReportEngine` aggregates data from `transactions`.
    -   User asks a **Query** ("Show high value expenses").
    -   `QueryService` parses intent, fetches data, and uses RAG for legal context.
