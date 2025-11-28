# Eagle Eyed Backend API

Backend API for Eagle Eyed - AI-powered financial compliance platform for Chartered Accountants.

## Features

- **Authentication & Authorization**: JWT-based auth with Supabase
- **Document Processing**: OCR, classification, and metadata extraction
- **Ledger Classification**: AI-powered transaction categorization
- **Compliance Engine**: GST, TDS, Income Tax, and Companies Act checks
- **RAG System**: Law-grounded query answering with legal references
- **Report Generation**: P&L, Balance Sheet, Trial Balance, Cash Flow
- **Return Filing**: GSTR-1, GSTR-3B, TDS returns, Advance Tax
- **Red Flag Detection**: Anomaly detection and compliance alerts
- **Natural Language Queries**: Ask questions in plain English

## Tech Stack

- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL + RLS)
- **Vector Store**: pgvector (for RAG)
- **AI/ML**: OpenAI (embeddings + LLM)
- **Authentication**: Supabase Auth + JWT
- **Storage**: Supabase Storage

## Setup

### Prerequisites

- Python 3.10+
- Supabase account
- OpenAI API key (for AI features)

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your actual values
   ```

5. Run the server:
   ```bash
   uvicorn backend.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── config.py                 # Application configuration
├── main.py                   # FastAPI application entry point
├── models/                   # Pydantic models
├── routers/                  # API route handlers
├── services/                 # Business logic services
│   ├── admin/               # Admin and monitoring
│   ├── compliance_engine/   # Compliance checks
│   ├── document_intake/     # Document processing
│   ├── ledger_classifier/   # Transaction classification
│   ├── query_engine/        # NL query processing
│   ├── rag_service/         # RAG components
│   ├── red_flag/            # Anomaly detection
│   ├── report_engine/       # Report generation
│   ├── return_filing/       # Tax return filing
│   └── sharing/             # Share link management
├── rag/                      # RAG pipeline components
├── crawlers/                 # Law/scheme data crawlers
└── utils/                    # Utility functions
```

## Environment Variables

See `.env.example` for all required environment variables.

### Critical Variables

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/service key
- `JWT_SECRET_KEY`: Secret key for JWT signing
- `OPENAI_API_KEY`: OpenAI API key for embeddings and LLM

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
```

### Type Checking

```bash
mypy .
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in environment
- [ ] Configure `ALLOWED_ORIGINS` to specific domains
- [ ] Use strong `JWT_SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Configure proper CORS settings
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Set up database backups

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token

### Clients
- `GET /api/clients` - List clients
- `POST /api/clients` - Create client
- `GET /api/clients/{id}` - Get client details

### Transactions
- `GET /api/transactions` - List transactions
- `POST /api/transactions` - Create transaction
- `PUT /api/transactions/{id}` - Update transaction

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents
- `DELETE /api/documents/{id}` - Delete document

### Compliance
- `POST /api/compliance/gst` - Run GST compliance check
- `POST /api/compliance/tds` - Run TDS compliance check
- `POST /api/compliance/income-tax` - Run Income Tax check

### Reports
- `GET /api/reports/pnl` - Generate P&L statement
- `GET /api/reports/balance-sheet` - Generate Balance Sheet
- `GET /api/reports/trial-balance` - Generate Trial Balance

### Query
- `POST /api/query` - Execute natural language query

### RAG
- `POST /api/rag/reindex` - Trigger full re-indexing
- `POST /api/rag/refresh` - Refresh specific law source

## Support

For issues and questions, please refer to the main project documentation.

## License

Proprietary - All rights reserved
