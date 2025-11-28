 Supabase password - eagleeyed1234$
 

Override ledger categories

Flag incorrect entries

Run GST, TDS, IT disallowance checks

Audit monthly, quarterly, yearly books

Run reconciliation (GST 2B, GSTR-1, Bank reco)

Run AI queries on the books

Generate working papers

Generate P&L, BS, TB, Cashflow

Inspect anomalies and red flags

CA is always the final decision-maker.

 3. COMPLIANCE RULES

Built into /compliance_engine/:

GST ITC rules

TDS applicability rules

40(a)(ia), 40A(3) disallowances

Depreciation block rules

MSME interest obligations

Companies Act compliance

Payment mode restrictions

GST mismatch detection (2B vs books)

 4. DOCUMENT INTAKE PIPELINE
Steps:

File uploaded (PDF/XLSX/CSV/IMG/JSON)

File-type validated via middleware

File sorted into correct folder automatically

Document classifier identifies:

Bank statement

Invoice

GST JSON

Expense bill

Payroll

Sales/Purchase register

Parser extracts structured data

Metadata extractor pulls GSTIN, invoice numbers, vendor names, dates

OCR fallback for non-text PDFs

Output transactions stored in DB

Ledger classifier enriches each transaction

Compliance engine analyses items

Red flag engine scans anomalies

CA reviews and overrides

All modules must follow this exact flow.

 5. RAG RULES
RAG uses:

Law documents

Govt scheme documents

ICAI guidance

Compliance rules

Historical client data

RAG behavior:

Retrieve top-k chunks

Reject low-similarity chunks

Never hallucinate laws

Always cite clause/source

Always embed retrieved context into prompts

AI response must be grounded and safe

 6. QUERY ENGINE BEHAVIOR

Supports queries like:

“Expenses above 50k this month”

“Missing GST numbers”

“Cash transactions”

“40(a)(ia) risky entries”

“Capital purchases > 10k”

“GST mismatch summary”

“Vendors with missing invoices”

Query Engine =
Natural Language → SQL + Filters + RAG + Summarized Answer

Responses must include:

Table

Summary

Law references

CA validation note

Compliance caution

 7. RETURN FILING BEHAVIOR
GSTR-1:

Summarize outward supplies

Classify B2B/B2C/NIL/EXP

Generate JSON for upload

Flag mismatches

GSTR-3B:

Outward tax

ITC available

RCM applicability

Net payable

TDS Summary:

194 C/J/I rules

Vendor validation

Threshold checks

Advance Tax:

Quarterly estimates

Everything is advisory, not automated filing.

 8. SECURITY + RLS CONSTRAINTS
Rules:

All endpoints require Supabase JWT

CA can only access assigned clients

Client can only access their own data

All soft-deleted items hidden unless trash requested

Share links must respect permissions

No endpoint exposes unprotected client financial data

 9. SUPABASE USAGE GUIDELINES

Used for:

Auth

RLS

Realtime (CA dashboard updates)

Object Storage (documents)

Postgres DB

pgvector embeddings

Backend must use Supabase client for:

Insert / Select / Update

RLS safe access

Signed URLs

 10. “NEVER DO THIS” SAFETY RULES (CRITICAL)

The backend and AI MUST NOT:

Auto-file GST returns

Auto-file TDS

Auto-file ITR

Invent law rules

Generate legal advice

Produce ungrounded answers

Output financial decisions without CA approval

Override CA edits

Leak client data across tenants

Store plaintext sensitive info

Modify financial values autonomously

THIS FILE IS THE OFFICIAL GROUND TRUTH

Every router, service, model, middleware, worker, and AI function MUST follow this spec.
 
 11. Model Definitions (AUTHORITATIVE PYDANTIC SCHEMA) 
 auth_models.py
class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["client", "ca"]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

🟦 user_models.py
class UserBase(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Literal["client", "ca"]
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    name: Optional[str] = None

class UserResponse(UserBase):
    pass

🟩 client_models.py
class ClientBase(BaseModel):
    id: str
    user_id: str               # owner (client user)
    assigned_ca_id: str        # chartered accountant user id
    business_name: Optional[str]
    gstin: Optional[str]
    created_at: datetime
    updated_at: datetime

class ClientCreate(BaseModel):
    business_name: str
    gstin: Optional[str]

class ClientResponse(ClientBase):
    pass

🟨 sheet_models.py
class Sheet(BaseModel):
    id: str
    client_id: str
    month: int
    year: int
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class SheetCreate(BaseModel):
    month: int
    year: int
    name: str

🟥 transaction_models.py
class Transaction(BaseModel):
    id: str
    sheet_id: str
    client_id: str
    date: date
    description: str
    amount: float
    type: Literal["credit", "debit"]
    vendor: Optional[str]
    gstin: Optional[str]
    mode: Optional[str]  # UPI, CASH, NEFT, POS, CARD
    ledger: Optional[str]
    gst_applicable: Optional[bool]
    tds_applicable: Optional[bool]
    capital_expense: Optional[bool]
    recurring: Optional[bool]
    ai_confidence: Optional[float]
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class TransactionCreate(BaseModel):
    date: date
    description: str
    amount: float
    type: Literal["credit", "debit"]

🟪 document_models.py
class Document(BaseModel):
    id: str
    client_id: str
    file_path: str
    file_type: Literal["bank_statement", "invoice", "gst_json", "expense", "sales", "purchase", "payroll"]
    original_filename: str
    metadata: Optional[dict]           # extracted vendor name, invoice no, dates, gstin etc
    folder_category: Optional[str]     # Bank/Expenses/GST/...
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class DocumentUploadResponse(BaseModel):
    id: str
    file_path: str
    file_type: str

🟧 ledger_models.py
class LedgerClassification(BaseModel):
    transaction_id: str
    ledger: str
    gst_applicable: bool
    tds_applicable: bool
    capital_expense: bool
    recurring: bool
    ai_confidence: float
    law_references: Optional[List[str]]
    created_at: datetime

🟫 compliance_models.py
class GSTComplianceResult(BaseModel):
    transaction_id: str
    itc_eligible: bool
    rcm_applicable: bool
    mismatch_reason: Optional[str]
    law_reference: Optional[str]

class TDSCheckResult(BaseModel):
    transaction_id: str
    tds_applicable: bool
    section: Optional[str]
    threshold: Optional[float]
    reason: Optional[str]

class DisallowanceResult(BaseModel):
    transaction_id: str
    section: str
    reason: str

🟦 redflag_models.py
class RedFlag(BaseModel):
    id: str
    transaction_id: str
    flag_type: Literal[
        "large_cash",
        "duplicate_invoice",
        "gst_mismatch",
        "missing_invoice",
        "suspicious_vendor",
        "anomaly"
    ]
    severity: Literal["low", "medium", "high"]
    message: str
    created_at: datetime
    resolved: bool = False

🟩 query_models.py
class QueryRequest(BaseModel):
    query: str
    filters: Optional[dict]

class QueryResult(BaseModel):
    table: List[dict]
    summary: str
    law_references: Optional[List[str]]

🟨 rag_models.py
class EmbeddingChunk(BaseModel):
    id: str
    source: str          # "gst_act", "it_act", "companies_act", etc.
    chunk_text: str
    embedding: List[float]

class RetrievalResult(BaseModel):
    chunk_text: str
    similarity: float

🟥 report_models.py
class ProfitAndLoss(BaseModel):
    revenue: float
    expenses: float
    gross_profit: float
    net_profit: float

class BalanceSheet(BaseModel):
    assets: dict
    liabilities: dict
    equity: dict

class TrialBalance(BaseModel):
    accounts: List[dict]

🟪 return_filing_models.py
class GSTR1Summary(BaseModel):
    total_taxable: float
    b2b: float
    b2c: float
    exports: float
    nil_rated: float

class GSTR3BSummary(BaseModel):
    outward_tax: float
    eligible_itc: float
    rcm_tax: float
    net_payable: float

class TDSSummary(BaseModel):
    total_tds: float
    vendor_breakdown: List[dict]

🟧 share_models.py
class ShareTokenModel(BaseModel):
    token: str
    resource_type: Literal["sheet", "document"]
    resource_id: str
    expires_at: datetime
    max_uses: int
    current_uses: int

🟫 admin_models.py
class AdminLog(BaseModel):
    id: str
    action: str
    performed_by: str
    details: dict
    created_at: datetime

🟦 response_models.py
class SuccessResponse(BaseModel):
    success: bool = True
    data: Any

class ErrorResponse(BaseModel):
    success: bool = False
    error: str

class PaginatedResponse(BaseModel):
    success: bool = True
    data: List[Any]
    page: int
    per_page: int
    total: int