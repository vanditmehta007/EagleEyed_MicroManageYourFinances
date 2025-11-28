# backend/services/red_flag/anomaly_detector.py

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import re
from backend.models.redflag_models import RedFlag
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from fastapi import HTTPException


class AnomalyDetectorService:
    """
    Service for detecting anomalies and red flags in financial transactions.
    
    Detects:
    - Duplicate transactions
    - Round-number anomalies
    - Unusual vendor patterns
    - Missing invoice sequences
    - Suspicious timing patterns
    - Amount threshold violations
    """

    def __init__(self) -> None:
        # TODO: Initialize detection rules and thresholds
        self.round_number_threshold = 1000  # Flag round numbers above this
        self.duplicate_time_window = 24  # Hours
        logger.info("AnomalyDetectorService initialized")

    def scan_for_red_flags(self, client_id: str, sheet_id: str) -> List[RedFlag]:
        """
        Scan all transactions in a sheet for red flags.
        """
        try:
            # TODO: Fetch all transactions for the sheet
            response = supabase.table("transactions").select("*").eq("sheet_id", sheet_id).is_("deleted_at", "null").execute()
            transactions = response.data or []
            
            if not transactions:
                return []
            
            red_flags = []
            
            # TODO: Run all detection methods
            red_flags.extend(self.detect_duplicates(transactions))
            red_flags.extend(self.detect_round_numbers(transactions))
            red_flags.extend(self.detect_missing_sequences(transactions))
            red_flags.extend(self.detect_unusual_vendors(transactions))
            
            # TODO: Aggregate and return red flags
            # Save red flags to database
            if red_flags:
                data_to_insert = [flag.dict(exclude={"id", "created_at"}) for flag in red_flags]
                supabase.table("red_flags").insert(data_to_insert).execute()
                logger.info(f"Detected and saved {len(red_flags)} red flags for sheet {sheet_id}")
            
            return red_flags
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

    def list_red_flags(self, client_id: str, resolved: bool = False) -> List[RedFlag]:
        """
        List all red flags for a client.
        """
        try:
            # TODO: Query red_flags table with filters
            query = supabase.table("red_flags").select("*").eq("client_id", client_id)
            
            if resolved:
                query = query.eq("status", "resolved")
            else:
                query = query.neq("status", "resolved")
                
            response = query.execute()
            
            # TODO: Return list of RedFlag objects
            return [RedFlag(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"Failed to list red flags: {e}")
            return []

    def resolve_red_flag(self, flag_id: str, resolution_note: str) -> RedFlag:
        """
        Mark a red flag as resolved.
        """
        try:
            # TODO: Update red_flag record with resolved status and note
            update_data = {
                "status": "resolved",
                "resolution_note": resolution_note,
                "resolved_at": datetime.utcnow().isoformat()
            }
            
            response = supabase.table("red_flags").update(update_data).eq("id", flag_id).execute()
            
            if not response.data:
                raise HTTPException(status_code=404, detail="Red flag not found")
            
            # TODO: Return updated RedFlag
            return RedFlag(**response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to resolve red flag: {e}")
            raise HTTPException(status_code=500, detail=f"Resolution failed: {str(e)}")

    def detect_duplicates(self, transactions: List[Dict[str, Any]]) -> List[RedFlag]:
        """
        Detect duplicate transactions (same vendor, amount, date).
        """
        flags = []
        # TODO: Group transactions by (vendor, amount, date)
        groups = defaultdict(list)
        
        for txn in transactions:
            key = (
                txn.get("vendor", "").lower().strip(),
                float(txn.get("amount", 0)),
                txn.get("date", "").split("T")[0]  # Compare date only, ignore time
            )
            groups[key].append(txn)
        
        # TODO: Flag groups with count > 1
        for key, group in groups.items():
            if len(group) > 1:
                vendor, amount, date = key
                txn_ids = [t["id"] for t in group]
                
                flag = RedFlag(
                    client_id=group[0]["client_id"],
                    transaction_id=group[0]["id"],  # Link to first transaction
                    type="duplicate_transaction",
                    severity="high",
                    description=f"Potential duplicate: {len(group)} transactions with same vendor, amount ({amount}), and date ({date})",
                    metadata={"duplicate_ids": txn_ids, "count": len(group)}
                )
                flags.append(flag)
        
        # TODO: Return RedFlag objects
        return flags

    def detect_round_numbers(self, transactions: List[Dict[str, Any]]) -> List[RedFlag]:
        """
        Detect suspicious round-number transactions.
        """
        flags = []
        
        for txn in transactions:
            amount = float(txn.get("amount", 0))
            
            # TODO: Check for amounts ending in 000, 0000, etc.
            if amount > self.round_number_threshold and amount % 1000 == 0:
                # TODO: Flag if pattern is unusual for the vendor
                # (Simplified check: flag all large round numbers for review)
                flag = RedFlag(
                    client_id=txn["client_id"],
                    transaction_id=txn["id"],
                    type="round_number",
                    severity="medium",
                    description=f"Suspicious round number amount: {amount}",
                    metadata={"amount": amount}
                )
                flags.append(flag)
        
        # TODO: Return RedFlag objects
        return flags

    def detect_missing_sequences(self, transactions: List[Dict[str, Any]]) -> List[RedFlag]:
        """
        Detect missing invoice number sequences.
        """
        flags = []
        # TODO: Group by vendor
        vendor_invoices = defaultdict(list)
        
        for txn in transactions:
            vendor = txn.get("vendor")
            inv_num = txn.get("invoice_number")
            if vendor and inv_num:
                # Extract numeric part of invoice number
                match = re.search(r'(\d+)$', str(inv_num))
                if match:
                    num = int(match.group(1))
                    vendor_invoices[vendor].append((num, txn))
        
        # TODO: Extract invoice numbers and check for gaps
        for vendor, items in vendor_invoices.items():
            if len(items) < 3:
                continue
                
            items.sort(key=lambda x: x[0])
            numbers = [x[0] for x in items]
            
            # Check for gaps
            for i in range(len(numbers) - 1):
                if numbers[i+1] - numbers[i] > 1:
                    missing_range = f"{numbers[i]+1} to {numbers[i+1]-1}"
                    if numbers[i+1] - numbers[i] == 2:
                        missing_range = str(numbers[i]+1)
                        
                    flag = RedFlag(
                        client_id=items[i][1]["client_id"],
                        transaction_id=items[i][1]["id"],
                        type="missing_invoice_sequence",
                        severity="medium",
                        description=f"Missing invoice sequence for {vendor}: {missing_range}",
                        metadata={"vendor": vendor, "gap_start": numbers[i], "gap_end": numbers[i+1]}
                    )
                    flags.append(flag)
        
        # TODO: Return RedFlag objects
        return flags

    def detect_unusual_vendors(self, transactions: List[Dict[str, Any]]) -> List[RedFlag]:
        """
        Detect transactions with unusual or suspicious vendor patterns.
        """
        flags = []
        vendor_counts = defaultdict(int)
        
        for txn in transactions:
            vendor_counts[txn.get("vendor", "")] += 1
            
        for txn in transactions:
            vendor = txn.get("vendor", "")
            amount = float(txn.get("amount", 0))
            
            # TODO: Check for vendors with single transactions (if amount is high)
            if vendor_counts[vendor] == 1 and amount > 50000:
                flag = RedFlag(
                    client_id=txn["client_id"],
                    transaction_id=txn["id"],
                    type="one_time_vendor",
                    severity="low",
                    description=f"High value transaction ({amount}) with one-time vendor: {vendor}",
                    metadata={"vendor": vendor, "amount": amount}
                )
                flags.append(flag)
            
            # TODO: Check for vendors with unusual naming patterns
            # (e.g., very short names, names with special chars)
            if len(vendor) < 3 or re.search(r'[^a-zA-Z0-9\s\.\-\&]', vendor):
                flag = RedFlag(
                    client_id=txn["client_id"],
                    transaction_id=txn["id"],
                    type="suspicious_vendor_name",
                    severity="medium",
                    description=f"Unusual vendor name format: {vendor}",
                    metadata={"vendor": vendor}
                )
                flags.append(flag)
                
            # TODO: Check for missing GSTIN where required
            # (Assuming GSTIN should be present for high value B2B transactions)
            if amount > 250000 and not txn.get("gstin"):
                flag = RedFlag(
                    client_id=txn["client_id"],
                    transaction_id=txn["id"],
                    type="missing_gstin",
                    severity="high",
                    description=f"High value transaction ({amount}) missing GSTIN",
                    metadata={"amount": amount}
                )
                flags.append(flag)
        
        # TODO: Return RedFlag objects
        return flags
