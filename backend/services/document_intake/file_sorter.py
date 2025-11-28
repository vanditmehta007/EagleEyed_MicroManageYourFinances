# backend/services/document_intake/file_sorter.py

from typing import Dict, List, Optional
from backend.utils.logger import logger


class FileSorter:
    """
    Utility for determining the target folder for a document based on its
    classified type (e.g., "bank_statement", "invoice", "gst_json", etc.).

    The mapping mirrors the folder structure used by the Eagle Eyed app:
        - Bank Statements
        - Expenses
        - GST
        - Sales
        - Purchases
        - Payroll
        - Tax Returns
        - Balance Sheets
        - Profit & Loss
        - TDS Certificates
        - Uncategorized (fallback)

    The actual moving of files is performed elsewhere; this class only
    provides the folder name.
    """

    # Mapping from document class to folder name
    _FOLDER_MAP: Dict[str, str] = {
        "bank_statement": "Bank Statements",
        "invoice": "Expenses",
        "gst_json": "GST",
        "expense": "Expenses",
        "expense_bill": "Expenses",
        "sales": "Sales",
        "purchase": "Purchases",
        "payroll": "Payroll",
        "tax_return": "Tax Returns",
        "balance_sheet": "Balance Sheets",
        "profit_loss": "Profit & Loss",
        "tds_certificate": "TDS Certificates",
        "transaction_sheet": "Transaction Sheets",
        "json_data": "Data Files",
    }

    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize FileSorter with optional custom folder mapping.
        
        Args:
            custom_mapping: Optional custom mapping to override default folder assignments.
        """
        # TODO: Extend mapping or make it configurable via environment/DB if needed
        # Merge custom mapping with default mapping
        if custom_mapping:
            self.folder_map = {**self._FOLDER_MAP, **custom_mapping}
            logger.info(f"FileSorter initialized with custom mapping: {custom_mapping}")
        else:
            self.folder_map = self._FOLDER_MAP.copy()
            logger.info("FileSorter initialized with default mapping")

    def get_target_folder(self, doc_type: str) -> str:
        """
        Return the folder name that a document of the given type should be placed
        into.

        Args:
            doc_type: The document classification string (e.g., "invoice").

        Returns:
            The folder name as a string. If the type is unknown, returns
            "Uncategorized".
        """
        # Normalize doc_type to lowercase for case-insensitive matching
        normalized_type = doc_type.lower().strip()
        
        # Get folder from mapping
        folder = self.folder_map.get(normalized_type, "Uncategorized")
        
        logger.debug(f"Document type '{doc_type}' mapped to folder '{folder}'")
        
        return folder

    def sort_documents(self, doc_type_to_ids: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Organise a batch of document IDs into their target folders.

        Args:
            doc_type_to_ids: Mapping from document type to a list of document IDs.

        Returns:
            Mapping from folder name to a list of document IDs that belong there.
        """
        # TODO: Implement any additional grouping logic if required.
        folder_to_ids: Dict[str, List[str]] = {}
        
        for doc_type, ids in doc_type_to_ids.items():
            if not ids:
                continue
                
            folder = self.get_target_folder(doc_type)
            
            # Initialize folder list if not exists
            if folder not in folder_to_ids:
                folder_to_ids[folder] = []
            
            # Add document IDs to the folder
            folder_to_ids[folder].extend(ids)
        
        # Log summary
        total_docs = sum(len(ids) for ids in folder_to_ids.values())
        logger.info(f"Sorted {total_docs} documents into {len(folder_to_ids)} folders")
        
        return folder_to_ids

    def get_all_folders(self) -> List[str]:
        """
        Get list of all available folder names.
        
        Returns:
            List of folder names including "Uncategorized".
        """
        folders = list(set(self.folder_map.values()))
        if "Uncategorized" not in folders:
            folders.append("Uncategorized")
        return sorted(folders)

    def get_document_types_for_folder(self, folder_name: str) -> List[str]:
        """
        Get all document types that map to a specific folder.
        
        Args:
            folder_name: The folder name to query.
            
        Returns:
            List of document types that belong to this folder.
        """
        doc_types = [
            doc_type for doc_type, folder in self.folder_map.items()
            if folder == folder_name
        ]
        
        logger.debug(f"Folder '{folder_name}' contains document types: {doc_types}")
        
        return doc_types

    def add_custom_mapping(self, doc_type: str, folder_name: str) -> None:
        """
        Add or update a custom document type to folder mapping.
        
        Args:
            doc_type: Document type identifier.
            folder_name: Target folder name.
        """
        self.folder_map[doc_type.lower().strip()] = folder_name
        logger.info(f"Added custom mapping: '{doc_type}' -> '{folder_name}'")

    def remove_custom_mapping(self, doc_type: str) -> bool:
        """
        Remove a custom document type mapping.
        
        Args:
            doc_type: Document type identifier to remove.
            
        Returns:
            True if mapping was removed, False if it didn't exist.
        """
        normalized_type = doc_type.lower().strip()
        
        if normalized_type in self.folder_map:
            del self.folder_map[normalized_type]
            logger.info(f"Removed custom mapping for '{doc_type}'")
            return True
        else:
            logger.warning(f"No mapping found for '{doc_type}'")
            return False

    def get_folder_statistics(self, doc_type_to_ids: Dict[str, List[str]]) -> Dict[str, Dict[str, int]]:
        """
        Get statistics about document distribution across folders.
        
        Args:
            doc_type_to_ids: Mapping from document type to list of document IDs.
            
        Returns:
            Dictionary with folder names as keys and statistics as values.
        """
        folder_to_ids = self.sort_documents(doc_type_to_ids)
        
        statistics = {}
        for folder, ids in folder_to_ids.items():
            statistics[folder] = {
                "count": len(ids),
                "percentage": 0.0
            }
        
        # Calculate percentages
        total_docs = sum(stats["count"] for stats in statistics.values())
        if total_docs > 0:
            for folder in statistics:
                statistics[folder]["percentage"] = round(
                    (statistics[folder]["count"] / total_docs) * 100, 2
                )
        
        logger.info(f"Generated statistics for {len(statistics)} folders")
        
        return statistics