import pandas as pd
import re
from email_validator import validate_email, EmailNotValidError
from typing import List, Dict, Tuple

class EmailValidator:
    """Validate and clean email addresses."""
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
        'tempmail.org', 'throwaway.email', 'yopmail.com'
    }
    
    @staticmethod
    def validate_email_syntax(email: str) -> Tuple[bool, str]:
        """
        Validate email syntax using email-validator library.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate and normalize email
            valid_email = validate_email(email)
            return True, valid_email.email
        except EmailNotValidError as e:
            return False, str(e)
    
    @staticmethod
    def is_disposable_domain(email: str) -> bool:
        """
        Check if email domain is disposable.
        
        Args:
            email: Email address to check
            
        Returns:
            True if disposable domain
        """
        domain = email.split('@')[-1].lower()
        return domain in EmailValidator.DISPOSABLE_DOMAINS
    
    @staticmethod
    def clean_emails(df: pd.DataFrame, email_column: str) -> pd.DataFrame:
        """
        Clean and validate emails in DataFrame.
        
        Args:
            df: DataFrame containing email data
            email_column: Name of the email column
            
        Returns:
            Cleaned DataFrame with validation results
        """
        if email_column not in df.columns:
            raise ValueError(f"Email column '{email_column}' not found in DataFrame")
        
        # Create a copy to avoid modifying original
        df_clean = df.copy()
        
        # Add validation columns
        df_clean['email_original'] = df_clean[email_column]
        df_clean['email_clean'] = ''
        df_clean['is_valid'] = False
        df_clean['validation_error'] = ''
        df_clean['is_disposable'] = False
        
        valid_emails = []
        invalid_emails = []
        
        for idx, row in df_clean.iterrows():
            email = str(row[email_column]).strip().lower()
            
            # Skip empty emails
            if pd.isna(email) or email == '' or email == 'nan':
                df_clean.at[idx, 'validation_error'] = 'Empty email'
                invalid_emails.append(idx)
                continue
            
            # Validate syntax
            is_valid, result = EmailValidator.validate_email_syntax(email)
            
            if is_valid:
                clean_email = result
                df_clean.at[idx, 'email_clean'] = clean_email
                df_clean.at[idx, 'is_valid'] = True
                
                # Check if disposable
                is_disposable = EmailValidator.is_disposable_domain(clean_email)
                df_clean.at[idx, 'is_disposable'] = is_disposable
                
                valid_emails.append(idx)
            else:
                df_clean.at[idx, 'validation_error'] = result
                invalid_emails.append(idx)
        
        return df_clean
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, email_column: str = 'email_clean') -> pd.DataFrame:
        """
        Remove duplicate emails from DataFrame.
        
        Args:
            df: DataFrame to deduplicate
            email_column: Column to use for deduplication
            
        Returns:
            DataFrame with duplicates removed
        """
        if email_column not in df.columns:
            raise ValueError(f"Email column '{email_column}' not found in DataFrame")
        
        # Remove duplicates based on clean email
        df_deduped = df.drop_duplicates(subset=[email_column], keep='first')
        
        # Reset index
        df_deduped = df_deduped.reset_index(drop=True)
        
        return df_deduped
    
    @staticmethod
    def filter_valid_emails(df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter DataFrame to only include valid emails.
        
        Args:
            df: DataFrame with validation results
            
        Returns:
            DataFrame with only valid emails
        """
        if 'is_valid' not in df.columns:
            raise ValueError("DataFrame must contain 'is_valid' column from validation")
        
        return df[df['is_valid'] == True].copy()
    
    @staticmethod
    def get_validation_summary(df: pd.DataFrame) -> Dict:
        """
        Get summary of validation results.
        
        Args:
            df: DataFrame with validation results
            
        Returns:
            Dictionary with validation summary
        """
        if 'is_valid' not in df.columns:
            return {"error": "DataFrame not validated"}
        
        total = len(df)
        valid = df['is_valid'].sum()
        invalid = total - valid
        disposable = df.get('is_disposable', pd.Series([False] * len(df))).sum()
        
        return {
            'total_emails': total,
            'valid_emails': valid,
            'invalid_emails': invalid,
            'disposable_emails': disposable,
            'valid_percentage': round((valid / total) * 100, 2) if total > 0 else 0
        } 