# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import (
    auth_router,
    user_router,
    client_router,
    sheet_router,
    transaction_router,
    document_router,
    import_router,
    query_router,
    compliance_router,
    report_router,
    return_filing_router,
    ledger_classifier_router,
    redflag_router,
    rag_router,
    share_router,
    admin_router,
    health_router,
    ocr_router,
    settings_router,
    agent_router
)

app = FastAPI(
    title="Eagle Eyed API",
    description="Backend API for Eagle Eyed - AI-powered financial compliance platform for CAs",
    version="1.0.0"
)

from backend.services.admin.system_monitor import SystemMonitor

@app.on_event("startup")
async def startup_event():
    print("Eagle Eyed API starting up...")
    print("Checking Database Connection...")
    try:
        status = SystemMonitor._check_database()
        if status["status"] == "up":
            print(f"✅ Database Connected Successfully! (Response Time: {status['response_time_ms']}ms)")
        else:
            print(f"⚠️ Database Connection Status: {status['status']}")
            if "error" in status:
                print(f"❌ Error: {status['error']}")
    except Exception as e:
        print(f"❌ Failed to check database connection: {e}")

# CORS configuration
from backend.middleware.jwt_verification import JWTVerificationMiddleware
from backend.middleware.multi_tenant_rls import MultiTenantRLSMiddleware
from backend.middleware.role_enforcement import RoleEnforcementMiddleware

# Middleware Configuration
# Note: Middleware is added in reverse order of execution (LIFO).
# Execution Order: CORS -> JWT -> RLS -> RBAC

app.add_middleware(RoleEnforcementMiddleware)
app.add_middleware(MultiTenantRLSMiddleware)
app.add_middleware(JWTVerificationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api", tags=["Authentication"])
app.include_router(user_router.router, prefix="/api", tags=["Users"])
app.include_router(client_router.router, prefix="/api", tags=["Client"])
app.include_router(sheet_router.router, prefix="/api", tags=["Sheets"])
app.include_router(transaction_router.router, prefix="/api", tags=["Transactions"])
app.include_router(document_router.router, prefix="/api", tags=["Documents"])
app.include_router(import_router.router, prefix="/api", tags=["Import"])
app.include_router(query_router.router, prefix="/api", tags=["Query"])
app.include_router(compliance_router.router, prefix="/api", tags=["Compliance"])
app.include_router(report_router.router, prefix="/api", tags=["Reports"])
app.include_router(return_filing_router.router, prefix="/api", tags=["Return Filing"])
app.include_router(ledger_classifier_router.router, prefix="/api", tags=["Ledger Classifier"])
app.include_router(redflag_router.router, prefix="/api", tags=["Red Flags"])
app.include_router(rag_router.router, prefix="/api", tags=["RAG"])
app.include_router(share_router.router, prefix="/api", tags=["Sharing"])
app.include_router(admin_router.router, prefix="/api", tags=["Admin"])
app.include_router(health_router.router, tags=["Health"])
app.include_router(ocr_router.router, prefix="/api", tags=["OCR"])
app.include_router(settings_router.router, prefix="/api", tags=["Settings"])
app.include_router(agent_router.router, prefix="/api")

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Eagle Eyed API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    # TODO: Configure host and port via environment variables
    uvicorn.run(app, host="0.0.0.0", port=8000)
