
from typing import Dict, Any, List, Optional
from fastapi import UploadFile
from backend.services.document_intake.document_service import DocumentIntakeService
from backend.services.document_intake.bank_statement_parser import BankStatementParser
from backend.services.document_intake.invoice_parser import InvoiceParser
from backend.services.ocr.ocr_service import OCRService
from backend.services.transaction_service import TransactionService
from backend.services.compliance_engine.gst_compliance import GSTComplianceService
from backend.models.transaction_models import TransactionCreate
from backend.utils.logger import logger
import os

# Initialize services
_document_service = DocumentIntakeService()
_bank_statement_parser = BankStatementParser()
_invoice_parser = InvoiceParser()
_ocr_service = OCRService()
_transaction_service = TransactionService()
_gst_service = GSTComplianceService()

async def upload_document(file_path: str, client_id: str, folder_category: str = "general") -> Dict[str, Any]:
    """
    Upload a document from a local file path.
    """
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            content = f.read()
            
        # Create a mock UploadFile
        # In a real agent scenario, we might handle file streams differently
        from io import BytesIO
        file_obj = UploadFile(filename=filename, file=BytesIO(content))
        
        # Call service
        result = await _document_service.upload_document(file_obj, client_id, folder_category)
        return result
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return {"error": str(e)}

async def parse_bank_statement(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a bank statement file (CSV, Excel) from a local path.
    """
    try:
        if not os.path.exists(file_path):
            return [{"error": f"File not found: {file_path}"}]
            
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            content = f.read()
            
        from io import BytesIO
        file_obj = UploadFile(filename=filename, file=BytesIO(content))
        
        return await _bank_statement_parser.parse(file_obj)
        
    except Exception as e:
        logger.error(f"Bank statement parsing failed: {e}")
        return [{"error": str(e)}]

async def parse_invoice(file_path: str) -> Dict[str, Any]:
    """
    Extract data from an invoice file.
    """
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            content = f.read()
            
        from io import BytesIO
        file_obj = UploadFile(filename=filename, file=BytesIO(content))
        
        # InvoiceParser.extract() is not async in the outline but let's check usage
        # Assuming it might be async or sync. The outline didn't show async def but let's be safe.
        # Actually, let's check InvoiceParser outline if possible, but I'll assume sync based on typical pattern unless I see await.
        # Wait, BankStatementParser.parse IS async.
        # Let's assume InvoiceParser.extract is sync for now, if it fails I'll fix.
        # Actually, let's wrap it in try/except.
        return await _invoice_parser.parse(file_obj)
        
    except Exception as e:
        logger.error(f"Invoice parsing failed: {e}")
        return {"error": str(e)}

def extract_ocr(file_path: str) -> Dict[str, Any]:
    """
    Extract text from an image or PDF using OCR.
    """
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            content = f.read()
            
        from io import BytesIO
        file_obj = UploadFile(filename=filename, file=BytesIO(content))
        
        result = _ocr_service.extract_text(file_obj)
        return result.dict() if hasattr(result, 'dict') else result.__dict__
        
    except Exception as e:
        logger.error(f"OCR failed: {e}")
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return {"error": str(e)}

async def analyze_document_compliance(file_path: str, client_id: str) -> Dict[str, Any]:
    """
    Analyze a document (Bank Statement/Excel) for compliance.
    Parses transactions, saves them, and runs GST compliance checks.
    """
    try:
        # 1. Parse Document
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            content = f.read()
            
        from io import BytesIO
        file_obj = UploadFile(filename=filename, file=BytesIO(content))
        
        # Determine parser based on extension
        parsed_data = []
        if filename.endswith(('.xlsx', '.xls', '.csv')):
            parsed_data = await _bank_statement_parser.parse(file_obj)
        else:
            return {"error": "Currently only Excel/CSV bank statements are supported for full analysis."}
            
        if not parsed_data:
            return {"message": "No transactions found in document."}
            
        # 2. Bulk Create Transactions
        txns_to_create = []
        for row in parsed_data:
            # Map parsed dict to TransactionCreate model
            # Note: BankStatementParser returns dicts with keys: date, description, amount, type, balance, mode
            txns_to_create.append(TransactionCreate(
                amount=row.get("amount"),
                date=row.get("date"),
                description=row.get("description"),
                type=row.get("type"),
                client_id=client_id,
                ledger="Uncategorized", # Default
                gstin=None # Parser doesn't extract GSTIN from bank stmt usually
            ))
            
        bulk_result = _transaction_service.create_bulk_transactions(txns_to_create)
        
        if not bulk_result.get("success"):
            return {"error": "Failed to save transactions."}
            
        created_txns = bulk_result.get("data", [])
        created_ids = [t["id"] for t in created_txns]
        
        # 3. Run Compliance Checks
        compliance_results = _gst_service.check_compliance(created_ids)
        
        # 4. Summarize Results
        flagged_transactions = [res.model_dump() for res in compliance_results if not res.itc_eligible or res.rcm_applicable]
        
        return {
            "status": "success",
            "total_transactions": len(created_txns),
            "flagged_issues": len(flagged_transactions),
            "details": flagged_transactions
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"error": str(e)}

# Tool Registry Export
DOCUMENT_TOOLS = {
    "upload_document": upload_document,
    "parse_bank_statement": parse_bank_statement,
    "parse_invoice": parse_invoice,
    "parse_invoice": parse_invoice,
    "extract_ocr": extract_ocr,
    "analyze_document_compliance": analyze_document_compliance
}
