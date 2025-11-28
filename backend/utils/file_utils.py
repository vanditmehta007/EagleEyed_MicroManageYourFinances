import os
import mimetypes
from typing import Optional, Tuple, List, Union

class FileUtils:
    """
    Helper utilities for file handling, validation, and identification.
    
    Provides functionality for:
    - Identifying file types (MIME detection)
    - Validating file extensions
    - Reading/Writing file content safely
    - Checking file size limits
    """

    # Allowed file extensions for the application
    ALLOWED_EXTENSIONS = {
        'pdf', 'csv', 'xlsx', 'xls', 'json', 'jpg', 'jpeg', 'png', 'txt'
    }

    # MIME type mapping for stricter validation
    MIME_TYPES = {
        'pdf': 'application/pdf',
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
        'json': 'application/json',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'txt': 'text/plain'
    }

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Extracts the file extension from a filename.
        
        Args:
            filename: The name of the file.
            
        Returns:
            Lowercase extension without the dot (e.g., 'pdf').
        """
        if '.' not in filename:
            return ""
        return filename.rsplit('.', 1)[1].lower()

    @staticmethod
    def validate_file_type(filename: str, allowed_extensions: Optional[set] = None) -> bool:
        """
        Checks if the file extension is allowed.
        
        Args:
            filename: The name of the file.
            allowed_extensions: Set of allowed extensions. Defaults to global ALLOWED_EXTENSIONS.
            
        Returns:
            True if valid, False otherwise.
        """
        ext = FileUtils.get_file_extension(filename)
        allowed = allowed_extensions or FileUtils.ALLOWED_EXTENSIONS
        return ext in allowed

    @staticmethod
    def detect_mime_type(file_path: str) -> Optional[str]:
        """
        Detects the MIME type of a file based on its path/extension.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            MIME type string (e.g., 'application/pdf') or None.
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type

    @staticmethod
    def read_file(file_path: str, mode: str = 'r') -> Union[str, bytes, None]:
        """
        Reads content from a file safely.
        
        Args:
            file_path: Path to the file.
            mode: Read mode ('r' for text, 'rb' for binary).
            
        Returns:
            File content or None if error.
        """
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, mode, encoding='utf-8' if 'b' not in mode else None) as f:
                return f.read()
        except Exception as e:
            # In a real app, log this error
            print(f"Error reading file {file_path}: {e}")
            return None

    @staticmethod
    def write_file(file_path: str, content: Union[str, bytes], mode: str = 'w') -> bool:
        """
        Writes content to a file safely.
        
        Args:
            file_path: Path to the file.
            content: Content to write.
            mode: Write mode ('w' for text, 'wb' for binary).
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, mode, encoding='utf-8' if 'b' not in mode else None) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Gets the size of a file in bytes.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Size in bytes, or -1 if file doesn't exist.
        """
        if not os.path.exists(file_path):
            return -1
        return os.path.getsize(file_path)

    @staticmethod
    def is_file_too_large(file_path: str, max_size_mb: int = 10) -> bool:
        """
        Checks if a file exceeds a size limit.
        
        Args:
            file_path: Path to the file.
            max_size_mb: Maximum allowed size in Megabytes.
            
        Returns:
            True if file is too large, False otherwise.
        """
        size_bytes = FileUtils.get_file_size(file_path)
        if size_bytes == -1:
            return False
            
        limit_bytes = max_size_mb * 1024 * 1024
        return size_bytes > limit_bytes
