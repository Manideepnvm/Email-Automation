import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class FileParser:
    """Parse various file formats to extract email addresses and data."""
    
    @staticmethod
    def parse_file(file_path: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        Parse file and return DataFrame with available columns.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Tuple of (DataFrame, list of column names)
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.csv':
            return FileParser._parse_csv(file_path)
        elif file_extension == '.xlsx':
            return FileParser._parse_xlsx(file_path)
        elif file_extension == '.txt':
            return FileParser._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    @staticmethod
    def _parse_csv(file_path: Path) -> Tuple[pd.DataFrame, List[str]]:
        """Parse CSV file."""
        try:
            df = pd.read_csv(file_path)
            return df, df.columns.tolist()
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {e}")
    
    @staticmethod
    def _parse_xlsx(file_path: Path) -> Tuple[pd.DataFrame, List[str]]:
        """Parse Excel file."""
        try:
            df = pd.read_excel(file_path)
            return df, df.columns.tolist()
        except Exception as e:
            raise ValueError(f"Error parsing Excel file: {e}")
    
    @staticmethod
    def _parse_txt(file_path: Path) -> Tuple[pd.DataFrame, List[str]]:
        """Parse text file - extract emails from each line."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extract emails using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Find all emails in the line
                    found_emails = re.findall(email_pattern, line)
                    if found_emails:
                        emails.extend(found_emails)
            
            # Create DataFrame with email column
            df = pd.DataFrame({'email': emails})
            return df, ['email']
            
        except Exception as e:
            raise ValueError(f"Error parsing text file: {e}")
    
    @staticmethod
    def auto_detect_email_column(df: pd.DataFrame) -> Optional[str]:
        """
        Auto-detect the email column in the DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Name of the email column or None if not found
        """
        email_patterns = [
            'email', 'e-mail', 'mail', 'email_address', 'emailaddress',
            'e_mail', 'e_mail_address', 'emailaddress'
        ]
        
        # Check for exact matches first
        for col in df.columns:
            if col.lower() in email_patterns:
                return col
        
        # Check for partial matches
        for col in df.columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in email_patterns):
                return col
        
        # Check if any column contains email-like data
        for col in df.columns:
            if df[col].dtype == 'object':
                # Sample some values to check if they look like emails
                sample_values = df[col].dropna().head(10)
                if len(sample_values) > 0:
                    email_count = 0
                    for value in sample_values:
                        if '@' in str(value) and '.' in str(value):
                            email_count += 1
                    
                    if email_count >= len(sample_values) * 0.7:  # 70% look like emails
                        return col
        
        return None
    
    @staticmethod
    def get_preview(df: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
        """
        Get a preview of the DataFrame.
        
        Args:
            df: DataFrame to preview
            max_rows: Maximum number of rows to show
            
        Returns:
            Preview DataFrame
        """
        return df.head(max_rows) 