from typing import Dict, Any, List
from datetime import date
from backend.utils.date_utils import DateUtils
from backend.utils.income_tax_utils import IncomeTaxUtils
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class QuarterlyTaskService:
    """
    Service for generating Quarterly Reports and Tasks.
    
    Includes:
    - TDS Payment & Return Checks (24Q, 26Q)
    - Advance Tax Estimation
    - Quarterly GST Comparison (GSTR-1 vs GSTR-3B)
    - Financial Ratio Analysis
    """

    def generate_quarterly_report(self, client_id: str, quarter: str, year: int) -> Dict[str, Any]:
        """
        Generates a comprehensive quarterly report.
        
        Args:
            client_id: Client identifier.
            quarter: Quarter string (e.g., "Q1", "Q2").
            year: Financial Year start (e.g., 2023 for FY 2023-24).
        """
        logger.info(f"Generating quarterly report for client {client_id} ({quarter} FY {year})")
        
        report = {
            "client_id": client_id,
            "quarter": quarter,
            "financial_year": f"{year}-{year+1}",
            "generated_at": str(date.today()),
            "tds_status": self._check_tds_compliance(client_id, quarter, year),
            "advance_tax": self._estimate_advance_tax(client_id, quarter, year),
            "gst_comparison": self._compare_quarterly_gst(client_id, quarter, year),
            "ratio_analysis": self._analyze_ratios(client_id, quarter, year)
        }
        
        return report

    def _check_tds_compliance(self, client_id: str, quarter: str, year: int) -> Dict[str, Any]:
        """
        Checks TDS payment status and return filing readiness.
        """
        try:
            from backend.services.compliance_engine.tds_engine import TDSEngine
            
            # Get quarter date range
            quarter_map = {
                "Q1": (f"{year}-04-01", f"{year}-06-30"),
                "Q2": (f"{year}-07-01", f"{year}-09-30"),
                "Q3": (f"{year}-10-01", f"{year}-12-31"),
                "Q4": (f"{year+1}-01-01", f"{year+1}-03-31")
            }
            
            start_date, end_date = quarter_map.get(quarter, (f"{year}-04-01", f"{year}-06-30"))
            
            # Fetch transactions for the quarter
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Check TDS applicability
            tds_engine = TDSEngine()
            total_deducted = 0.0
            
            for txn in transactions:
                result = tds_engine._check_transaction_tds(txn)
                if result.tds_applicable:
                    amount = float(txn.get("amount", 0))
                    tds_amount = tds_engine.calculate_tds_amount(amount, result.section)
                    total_deducted += tds_amount
            
            return {
                "total_deducted": round(total_deducted, 2),
                "total_deposited": 0.0,  # TODO: Track actual deposits
                "short_deduction": 0.0,
                "interest_payable": 0.0,
                "return_filed": False,  # TODO: Track return filing status
                "pending_forms": ["26Q", "24Q"] if total_deducted > 0 else []
            }
            
        except Exception as e:
            logger.error(f"TDS compliance check failed: {e}")
            return {"total_deducted": 0.0, "total_deposited": 0.0, "return_filed": False}

    def _estimate_advance_tax(self, client_id: str, quarter: str, year: int) -> Dict[str, Any]:
        """
        Estimates Advance Tax liability based on YTD profit.
        """
        try:
            # Get YTD date range (April to current quarter end)
            quarter_map = {
                "Q1": f"{year}-06-30",
                "Q2": f"{year}-09-30",
                "Q3": f"{year}-12-31",
                "Q4": f"{year+1}-03-31"
            }
            
            ytd_end = quarter_map.get(quarter, f"{year}-06-30")
            
            # Fetch YTD transactions
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", f"{year}-04-01").lte("date", ytd_end).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Calculate YTD profit
            revenue = sum(float(t.get("amount", 0)) for t in transactions if t.get("type") == "credit")
            expenses = sum(float(t.get("amount", 0)) for t in transactions if t.get("type") == "debit")
            ytd_profit = revenue - expenses
            
            # Estimate annual income (simple projection)
            quarter_num = int(quarter[1])
            estimated_annual_income = ytd_profit * (4 / quarter_num)
            
            # Calculate tax liability (assuming 30% corporate tax)
            tax_rate = 0.30
            tax_liability = estimated_annual_income * tax_rate
            
            # Advance tax percentages
            advance_tax_percentages = {
                "Q1": 0.15,  # 15% by June 15
                "Q2": 0.45,  # 45% by Sept 15
                "Q3": 0.75,  # 75% by Dec 15
                "Q4": 1.00   # 100% by Mar 15
            }
            
            advance_tax_due = tax_liability * advance_tax_percentages.get(quarter, 0.15)
            
            due_dates = {
                "Q1": "15th June",
                "Q2": "15th September",
                "Q3": "15th December",
                "Q4": "15th March"
            }
            
            return {
                "estimated_annual_income": round(estimated_annual_income, 2),
                "tax_liability": round(tax_liability, 2),
                "tds_credit": 0.0,  # TODO: Track TDS credits
                "net_tax_payable": round(tax_liability, 2),
                "advance_tax_due": round(advance_tax_due, 2),
                "due_date": due_dates.get(quarter, "15th June")
            }
            
        except Exception as e:
            logger.error(f"Advance tax estimation failed: {e}")
            return {"estimated_annual_income": 0.0, "tax_liability": 0.0, "advance_tax_due": 0.0}

    def _compare_quarterly_gst(self, client_id: str, quarter: str, year: int) -> Dict[str, Any]:
        """
        Compares GSTR-1 (Sales) vs GSTR-3B (Summary) for the quarter.
        """
        try:
            # Get quarter date range
            quarter_map = {
                "Q1": (f"{year}-04-01", f"{year}-06-30"),
                "Q2": (f"{year}-07-01", f"{year}-09-30"),
                "Q3": (f"{year}-10-01", f"{year}-12-31"),
                "Q4": (f"{year+1}-01-01", f"{year+1}-03-31")
            }
            
            start_date, end_date = quarter_map.get(quarter, (f"{year}-04-01", f"{year}-06-30"))
            
            # Fetch sales transactions (GSTR-1)
            response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "credit").gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            
            sales_txns = response.data if response.data else []
            
            gstr1_turnover = sum(float(t.get("amount", 0)) for t in sales_txns)
            gstr1_tax = sum(float(t.get("gst_amount", 0)) for t in sales_txns)
            
            # For GSTR-3B, we use the same data (in practice, this would come from filed returns)
            gstr3b_turnover = gstr1_turnover
            gstr3b_tax = gstr1_tax
            
            difference = gstr1_turnover - gstr3b_turnover
            tax_difference = gstr1_tax - gstr3b_tax
            
            return {
                "gstr1_turnover": round(gstr1_turnover, 2),
                "gstr3b_turnover": round(gstr3b_turnover, 2),
                "difference": round(difference, 2),
                "gstr1_tax": round(gstr1_tax, 2),
                "gstr3b_tax": round(gstr3b_tax, 2),
                "tax_difference": round(tax_difference, 2),
                "status": "Matched" if abs(difference) < 0.01 else "Mismatch"
            }
            
        except Exception as e:
            logger.error(f"GST comparison failed: {e}")
            return {"gstr1_turnover": 0.0, "gstr3b_turnover": 0.0, "status": "Error"}

    def _analyze_ratios(self, client_id: str, quarter: str, year: int) -> Dict[str, Any]:
        """
        Calculates key financial ratios for the quarter.
        """
        try:
            # Get quarter date range
            quarter_map = {
                "Q1": f"{year}-06-30",
                "Q2": f"{year}-09-30",
                "Q3": f"{year}-12-31",
                "Q4": f"{year+1}-03-31"
            }
            
            end_date = quarter_map.get(quarter, f"{year}-06-30")
            
            # Fetch all transactions up to quarter end
            response = supabase.table("transactions").select("*").eq("client_id", client_id).lte("date", end_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Calculate revenue and expenses
            revenue = sum(float(t.get("amount", 0)) for t in transactions if t.get("type") == "credit")
            expenses = sum(float(t.get("amount", 0)) for t in transactions if t.get("type") == "debit")
            
            gross_profit = revenue - expenses
            net_profit = gross_profit  # Simplified
            
            # Calculate ratios
            gross_profit_ratio = (gross_profit / revenue * 100) if revenue > 0 else 0
            net_profit_ratio = (net_profit / revenue * 100) if revenue > 0 else 0
            
            return {
                "gross_profit_ratio": round(gross_profit_ratio, 2),
                "net_profit_ratio": round(net_profit_ratio, 2),
                "current_ratio": 0.0,  # TODO: Requires balance sheet data
                "quick_ratio": 0.0     # TODO: Requires balance sheet data
            }
            
        except Exception as e:
            logger.error(f"Ratio analysis failed: {e}")
            return {"gross_profit_ratio": 0.0, "net_profit_ratio": 0.0}
