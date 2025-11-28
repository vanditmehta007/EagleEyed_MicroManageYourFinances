from typing import List, Dict, Any
from datetime import datetime, timedelta
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger


class CompaniesActChecker:
    """
    Service for performing Companies Act compliance checks.
    Includes bookkeeping compliance, related‑party transaction checks,
    and statutory record‑keeping validations.
    """

    # Threshold for related-party transaction materiality (in INR)
    RELATED_PARTY_THRESHOLD = 100000  # 1 Lakh

    # Minimum bookkeeping retention period (in years)
    BOOKKEEPING_RETENTION_YEARS = 8

    def check_bookkeeping_compliance(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Verify that the client's bookkeeping adheres to Companies Act requirements.
        
        Args:
            client_id: Identifier of the client whose books are being checked.
        
        Returns:
            A list of dictionaries describing any compliance issues found.
        """
        issues = []
        
        try:
            # TODO: Retrieve bookkeeping data and apply Companies Act rules
            # Fetch all sheets for the client
            sheets_response = supabase.table("sheets").select("*").eq("client_id", client_id).is_("deleted_at", "null").execute()
            
            if not sheets_response.data:
                # No financial sheets found - this is a compliance issue
                issues.append({
                    "issue_type": "missing_books",
                    "severity": "critical",
                    "description": "No financial records found for the client",
                    "section_reference": "Section 128 - Books of Account",
                    "recommendation": "Maintain proper books of account as required under Companies Act, 2013"
                })
                return issues
            
            sheets = sheets_response.data
            current_year = datetime.now().year
            
            # Check 1: Verify books are maintained for required retention period (8 years)
            oldest_year = min([sheet["financial_year"] for sheet in sheets])
            retention_gap = current_year - oldest_year
            
            if retention_gap < self.BOOKKEEPING_RETENTION_YEARS:
                issues.append({
                    "issue_type": "insufficient_retention",
                    "severity": "high",
                    "description": f"Books maintained for only {retention_gap} years. Companies Act requires {self.BOOKKEEPING_RETENTION_YEARS} years retention",
                    "section_reference": "Section 128(5) - Preservation of Books",
                    "recommendation": f"Maintain books for at least {self.BOOKKEEPING_RETENTION_YEARS} financial years"
                })
            
            # Check 2: Verify current financial year books exist
            if current_year not in [sheet["financial_year"] for sheet in sheets]:
                issues.append({
                    "issue_type": "missing_current_year",
                    "severity": "critical",
                    "description": f"No financial records found for current year {current_year}",
                    "section_reference": "Section 128 - Books of Account",
                    "recommendation": "Maintain up-to-date books of account for the current financial year"
                })
            
            # Check 3: Verify transactions are properly documented
            for sheet in sheets:
                transactions_response = supabase.table("transactions").select("*").eq("sheet_id", sheet["id"]).is_("deleted_at", "null").execute()
                
                if transactions_response.data:
                    transactions = transactions_response.data
                    
                    # Check for transactions without proper documentation
                    undocumented_count = 0
                    for txn in transactions:
                        # A transaction should have either invoice_number or proper description
                        if not txn.get("invoice_number") and (not txn.get("description") or len(txn.get("description", "")) < 10):
                            undocumented_count += 1
                    
                    if undocumented_count > 0:
                        issues.append({
                            "issue_type": "inadequate_documentation",
                            "severity": "medium",
                            "description": f"{undocumented_count} transactions in FY {sheet['financial_year']} lack proper documentation",
                            "section_reference": "Section 128 - Books of Account",
                            "recommendation": "Ensure all transactions have proper invoice numbers and descriptions"
                        })
            
            # TODO: Populate result entries with issue description, section reference, severity, etc.
            logger.info(f"Bookkeeping compliance check completed for client {client_id}: {len(issues)} issues found")
            
        except Exception as e:
            logger.error(f"Error checking bookkeeping compliance for client {client_id}: {e}")
            issues.append({
                "issue_type": "check_failed",
                "severity": "high",
                "description": f"Failed to complete bookkeeping compliance check: {str(e)}",
                "section_reference": "N/A",
                "recommendation": "Contact system administrator"
            })
        
        return issues

    def check_related_party_transactions(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Identify related‑party transactions that may violate Companies Act provisions.
        
        Args:
            client_id: Identifier of the client to inspect.
        
        Returns:
            A list of dictionaries detailing any related‑party compliance concerns.
        """
        issues = []
        
        try:
            # TODO: Fetch transactions and vendor/client relationships
            # Get client details
            client_response = supabase.table("clients").select("*").eq("id", client_id).single().execute()
            
            if not client_response.data:
                return issues
            
            client = client_response.data
            client_pan = client.get("pan", "")
            client_gstin = client.get("gstin", "")
            
            # Fetch all transactions for this client
            sheets_response = supabase.table("sheets").select("id").eq("client_id", client_id).is_("deleted_at", "null").execute()
            
            if not sheets_response.data:
                return issues
            
            sheet_ids = [sheet["id"] for sheet in sheets_response.data]
            
            # Get all transactions across all sheets
            for sheet_id in sheet_ids:
                transactions_response = supabase.table("transactions").select("*").eq("sheet_id", sheet_id).is_("deleted_at", "null").execute()
                
                if not transactions_response.data:
                    continue
                
                transactions = transactions_response.data
                
                # TODO: Apply related‑party detection logic per Companies Act
                # Check for potential related-party transactions
                for txn in transactions:
                    # Related party indicators:
                    # 1. Same PAN as client
                    # 2. Same GSTIN prefix (first 2 digits indicate state, next 10 is PAN)
                    # 3. High-value transactions with specific vendors (recurring)
                    
                    txn_pan = txn.get("pan", "")
                    txn_gstin = txn.get("gstin", "")
                    txn_amount = txn.get("amount", 0)
                    
                    is_related_party = False
                    relationship_type = ""
                    
                    # Check 1: Same PAN indicates related party
                    if txn_pan and client_pan and txn_pan == client_pan:
                        is_related_party = True
                        relationship_type = "same_pan"
                    
                    # Check 2: GSTIN with same PAN component (characters 3-12)
                    elif txn_gstin and client_gstin:
                        if len(txn_gstin) >= 12 and len(client_gstin) >= 12:
                            if txn_gstin[2:12] == client_gstin[2:12]:
                                is_related_party = True
                                relationship_type = "same_pan_in_gstin"
                    
                    # If related party detected and amount exceeds threshold
                    if is_related_party and txn_amount >= self.RELATED_PARTY_THRESHOLD:
                        issues.append({
                            "issue_type": "related_party_transaction",
                            "severity": "high",
                            "transaction_id": txn["id"],
                            "description": f"Related-party transaction of ₹{txn_amount:,.2f} detected with {txn.get('vendor', 'Unknown')}",
                            "relationship_type": relationship_type,
                            "section_reference": "Section 188 - Related Party Transactions",
                            "recommendation": "Ensure proper board approval and disclosure for related-party transactions exceeding threshold limits"
                        })
            
            logger.info(f"Related-party transaction check completed for client {client_id}: {len(issues)} issues found")
            
        except Exception as e:
            logger.error(f"Error checking related-party transactions for client {client_id}: {e}")
            issues.append({
                "issue_type": "check_failed",
                "severity": "high",
                "description": f"Failed to complete related-party transaction check: {str(e)}",
                "section_reference": "N/A",
                "recommendation": "Contact system administrator"
            })
        
        return issues

    def validate_statutory_records(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Validate that required statutory records (e.g., registers, minutes, filings) are present and up‑to‑date.
        
        Args:
            client_id: Identifier of the client whose statutory records are being validated.
        
        Returns:
            A list of dictionaries indicating missing or outdated statutory documents.
        """
        issues = []
        
        try:
            # TODO: Check existence and freshness of statutory registers, board minutes, annual returns, etc.
            # Fetch documents for this client
            documents_response = supabase.table("documents").select("*").eq("client_id", client_id).is_("deleted_at", "null").execute()
            
            if not documents_response.data:
                # No documents found - major compliance issue
                issues.append({
                    "issue_type": "no_statutory_documents",
                    "severity": "critical",
                    "description": "No statutory documents found on record",
                    "section_reference": "Section 88, 117, 92 - Statutory Registers and Records",
                    "recommendation": "Upload and maintain all required statutory registers, board minutes, and annual returns"
                })
                return issues
            
            documents = documents_response.data
            current_date = datetime.now()
            
            # Required statutory document types
            required_doc_types = {
                "register_of_members": {"section": "Section 88", "name": "Register of Members"},
                "board_minutes": {"section": "Section 118", "name": "Minutes of Board Meetings"},
                "annual_return": {"section": "Section 92", "name": "Annual Return (MGT-7)"},
                "financial_statements": {"section": "Section 129", "name": "Financial Statements"},
                "audit_report": {"section": "Section 143", "name": "Audit Report"}
            }
            
            # Check for presence of each required document type
            found_doc_types = set()
            for doc in documents:
                file_type = doc.get("file_type", "").lower()
                folder_category = doc.get("folder_category", "").lower()
                
                # Map document types (this is simplified - in production, use better categorization)
                if "register" in folder_category or "member" in folder_category:
                    found_doc_types.add("register_of_members")
                elif "minutes" in folder_category or "board" in folder_category:
                    found_doc_types.add("board_minutes")
                elif "annual" in folder_category or "return" in folder_category:
                    found_doc_types.add("annual_return")
                elif "financial" in folder_category or "statement" in folder_category:
                    found_doc_types.add("financial_statements")
                elif "audit" in folder_category:
                    found_doc_types.add("audit_report")
            
            # TODO: Return findings with references to the relevant Companies Act sections.
            # Check for missing document types
            for doc_type, details in required_doc_types.items():
                if doc_type not in found_doc_types:
                    issues.append({
                        "issue_type": "missing_statutory_document",
                        "severity": "high",
                        "description": f"Missing required document: {details['name']}",
                        "section_reference": details["section"],
                        "recommendation": f"Upload and maintain {details['name']} as required under {details['section']}"
                    })
            
            # Check for outdated annual returns (should be filed within 60 days of AGM)
            # Simplified check: look for annual returns in last 12 months
            recent_annual_returns = [
                doc for doc in documents
                if "annual" in doc.get("folder_category", "").lower()
                and (current_date - datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))).days <= 365
            ]
            
            if not recent_annual_returns:
                issues.append({
                    "issue_type": "outdated_annual_return",
                    "severity": "critical",
                    "description": "No annual return filed in the last 12 months",
                    "section_reference": "Section 92 - Annual Return",
                    "recommendation": "File annual return (Form MGT-7) within prescribed timeline"
                })
            
            logger.info(f"Statutory records validation completed for client {client_id}: {len(issues)} issues found")
            
        except Exception as e:
            logger.error(f"Error validating statutory records for client {client_id}: {e}")
            issues.append({
                "issue_type": "check_failed",
                "severity": "high",
                "description": f"Failed to complete statutory records validation: {str(e)}",
                "section_reference": "N/A",
                "recommendation": "Contact system administrator"
            })
        
        return issues
