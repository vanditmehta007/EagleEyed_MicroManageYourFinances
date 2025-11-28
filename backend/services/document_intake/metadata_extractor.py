
from typing import Dict, Any


class MetadataExtractor:
    """
    Extracts key invoice‑level metadata from the parsed content of a document.
    The parser (e.g., PDF, CSV, JSON) should provide a dict‑like structure
    containing raw text fields; this class then pulls out the most common
    fields needed by Eagle Eyed.

    Expected output keys:
        - vendor_name
        - invoice_number
        - gstin
        - bill_date
        - due_date
        - amount
    """

    def __init__(self) -> None:
        # TODO: Load any regex patterns or configuration files if needed
        pass

    def extract(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pull out metadata from a parsed document.

        Args:
            parsed_content: The raw output from a document parser. It may contain
                free‑form text, tables, or key‑value pairs.

        Returns:
            A dictionary with the extracted fields (vendor_name, invoice_number,
            gstin, bill_date, due_date, amount). Missing fields are set to None.
        """
        # TODO: Implement robust extraction logic, possibly using regexes.
        # Below is a simple placeholder implementation that looks for common keys.

        vendor_name = parsed_content.get("vendor_name") or parsed_content.get("seller") or None
        invoice_number = parsed_content.get("invoice_number") or parsed_content.get("invoice_no") or None
        gstin = parsed_content.get("gstin") or parsed_content.get("gst_number") or None
        bill_date = parsed_content.get("bill_date") or parsed_content.get("date") or None
        due_date = parsed_content.get("due_date") or parsed_content.get("payment_due") or None
        amount = parsed_content.get("total_amount") or parsed_content.get("amount") or None

        return {
            "vendor_name": vendor_name,
            "invoice_number": invoice_number,
            "gstin": gstin,
            "bill_date": bill_date,
            "due_date": due_date,
            "amount": amount,
        }