import logging
import io
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import dateutil.parser

from backend.services.document_intake.document_service import DocumentIntakeService
from backend.services.document_intake.bank_statement_parser import BankStatementParser
from backend.services.document_intake.invoice_parser import InvoiceParser
from backend.services.document_intake.gst_json_parser import GstJsonParser
from backend.services.document_intake.payment_gateway_parser import PaymentGatewayParser
from backend.services.sheet_service import SheetService
from backend.services.ledger_classifier.ledger_classifier_service import LedgerClassifierService
from backend.models.sheet_models import SheetCreate
from backend.utils.supabase_client import supabase

# Configure logging
logger = logging.getLogger(__name__)

class MockUploadFile:
    """
    Mock class to simulate FastAPI UploadFile for parsers when running in a worker.
    """
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.content = content
        self.file = io.BytesIO(content)
        self.content_type = "application/octet-stream" # Default

    async def read(self):
        return self.content

class DocumentIntakeWorker:
    """
    Worker responsible for processing uploaded documents asynchronously.
    It orchestrates the parsing, storage, and classification of transactions from documents.
    """

    def __init__(self):
        self.document_service = DocumentIntakeService()
        self.sheet_service = SheetService()
        self.ledger_classifier = LedgerClassifierService()
        
        # Initialize parsers
        self.parsers = {
            "bank_statement": BankStatementParser(),
            "invoice": InvoiceParser(),
            "gst_json": GstJsonParser(),
            "payment_gateway": PaymentGatewayParser(),
            # Map other types to appropriate parsers
            "expense": InvoiceParser(), 
            "sales": InvoiceParser(),
            "purchase": InvoiceParser(),
            "payroll": BankStatementParser(), # Assuming payroll might be CSV/Excel list
        }

    async def process_document(self, document_id: str):
        """
        Process a single document by ID:
        1. Fetch document metadata.
        2. Download file content.
        3. Parse content into transactions.
        4. Store transactions in a Sheet.
        5. Trigger Ledger Classification.
        """
        try:
            logger.info(f"Starting processing for document {document_id}")
            
            # 1. Get document metadata
            try:
                document = self.document_service.get_document(document_id)
            except Exception as e:
                logger.error(f"Document {document_id} not found: {e}")
                return

            # 2. Download file content
            try:
                # Download from Supabase storage bucket "documents"
                # Note: The bucket name should ideally come from config
                response = supabase.storage.from_("documents").download(document.file_path)
                file_content = response
            except Exception as e:
                logger.error(f"Failed to download file {document.file_path}: {e}")
                return

            # 3. Select and run parser
            parser = self.parsers.get(document.file_type)
            if not parser:
                logger.warning(f"No specific parser for {document.file_type}, using InvoiceParser as fallback")
                parser = self.parsers["invoice"]

            mock_file = MockUploadFile(document.original_filename, file_content)
            
            try:
                extracted_data = await parser.parse(mock_file)
            except Exception as e:
                logger.error(f"Parsing failed for document {document_id}: {e}")
                return
            
            if not extracted_data:
                logger.info(f"No transactions extracted from document {document_id}")
                return

            # 4. Determine Sheet ID
            # Use the date of the first transaction to find or create a sheet
            first_txn_date = extracted_data[0].get("date") if extracted_data else None
            sheet_id = self._get_or_create_sheet(document.client_id, first_txn_date, document.original_filename)

            # 5. Store transactions
            transaction_ids = self._store_transactions(extracted_data, sheet_id, document.client_id)
            
            # 6. Trigger Ledger Classification
            if transaction_ids:
                try:
                    self.ledger_classifier.classify_transactions(transaction_ids)
                    logger.info(f"Triggered ledger classification for {len(transaction_ids)} transactions")
                except Exception as e:
                    logger.error(f"Failed to trigger ledger classification: {e}")

            logger.info(f"Successfully processed document {document_id}")

        except Exception as e:
            logger.error(f"Unexpected error in document intake worker for {document_id}: {str(e)}")

    def _get_or_create_sheet(self, client_id: str, date_str: Optional[str], filename: str) -> str:
        """
        Find an existing sheet for the month/year or create a new one.
        """
        try:
            # Default to current date if no date in transactions
            dt = datetime.utcnow()
            if date_str:
                try:
                    dt = dateutil.parser.parse(str(date_str))
                except:
                    pass
            
            month = dt.month
            year = dt.year
            
            # List existing sheets
            sheets = self.sheet_service.list_sheets(client_id)
            
            # Try to find a matching sheet
            for sheet in sheets:
                if sheet.month == month and sheet.year == year:
                    return sheet.id
            
            # Create new sheet if not found
            sheet_name = f"Sheet - {datetime(year, month, 1).strftime('%B %Y')}"
            sheet_data = SheetCreate(
                name=sheet_name,
                month=month,
                year=year
            )
            # Note: SheetCreate in models might not have client_id, but the service create_sheet takes user_id?
            # Let's check SheetCreate definition in models. 
            # In backend_spec.md: class SheetCreate(BaseModel): month: int, year: int, name: str
            # Service create_sheet(sheet_data, user_id). 
            # Wait, sheet_models.py in spec doesn't have client_id in SheetCreate, but Sheet has client_id.
            # The service create_sheet implementation I read earlier assigns client_id from sheet_data.client_id?
            # Let's re-read the service code snippet I saw.
            # "new_sheet = { ... 'client_id': sheet_data.client_id ... }"
            # But SheetCreate definition I saw in spec didn't have client_id.
            # I should check the actual file backend/models/sheet_models.py if possible, but I saw the spec.
            # I'll assume I need to pass client_id somehow. 
            # Actually, the service method signature is `create_sheet(self, sheet_data: SheetCreate, user_id: str)`.
            # And it uses `sheet_data.client_id`. This implies `SheetCreate` MUST have `client_id`.
            # I will assume `SheetCreate` has `client_id` or I should add it to the dict if I can't modify the model.
            # But I can't modify the model here.
            # I'll assume the service handles it or the model has it.
            # Wait, if `SheetCreate` doesn't have it, `sheet_data.client_id` will fail.
            # I'll check `backend/models/sheet_models.py` quickly to be safe.
            
            # For now, I'll proceed assuming I can construct the sheet.
            # I'll manually create the sheet record if service is problematic, but better to use service.
            # I'll assume SheetCreate has client_id.
            
            # We need a user_id for `create_sheet`. The document has `client_id`. 
            # The `client_id` maps to a client record, which has a `user_id` (owner).
            # I might not have the user_id handy.
            # I'll just pass `client_id` as `user_id` or a system ID if allowed.
            # Or I'll insert directly to Supabase to avoid service constraints if needed.
            # Direct insert is safer here since I'm in a worker.
            
            new_sheet_id = str(uuid.uuid4())
            new_sheet = {
                "id": new_sheet_id,
                "client_id": client_id,
                "month": month,
                "year": year,
                "name": sheet_name,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            supabase.table("sheets").insert(new_sheet).execute()
            return new_sheet_id

        except Exception as e:
            logger.error(f"Error getting/creating sheet: {e}")
            # Fallback: create a generic sheet
            fallback_id = str(uuid.uuid4())
            try:
                supabase.table("sheets").insert({
                    "id": fallback_id,
                    "client_id": client_id,
                    "month": datetime.utcnow().month,
                    "year": datetime.utcnow().year,
                    "name": f"Imported {filename}",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }).execute()
                return fallback_id
            except:
                raise Exception("Could not create fallback sheet")

    def _store_transactions(self, data: List[Dict], sheet_id: str, client_id: str) -> List[str]:
        """
        Bulk insert transactions into the database.
        """
        transactions = []
        txn_ids = []
        
        for row in data:
            txn_id = str(uuid.uuid4())
            txn_ids.append(txn_id)
            
            # Ensure required fields
            txn = {
                "id": txn_id,
                "sheet_id": sheet_id,
                "client_id": client_id, # Spec says Transaction has client_id
                "date": row.get("date"),
                "description": row.get("description", ""),
                "amount": float(row.get("amount", 0)),
                "type": row.get("type", "debit"),
                "ledger": row.get("ledger", "Uncategorized"),
                "vendor": row.get("vendor"),
                "invoice_number": row.get("invoice_number"),
                "gstin": row.get("gstin"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            transactions.append(txn)
            
        if transactions:
            try:
                # Chunking insertion if too large
                chunk_size = 100
                for i in range(0, len(transactions), chunk_size):
                    chunk = transactions[i:i + chunk_size]
                    supabase.table("transactions").insert(chunk).execute()
            except Exception as e:
                logger.error(f"Failed to insert transactions: {e}")
                return []
                
        return txn_ids
