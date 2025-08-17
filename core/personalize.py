import pandas as pd
from typing import Dict, List, Optional
from .templates import EmailTemplates

class Personalizer:
    """Handle personalization of email templates with DataFrame data."""
    
    @staticmethod
    def map_columns_to_placeholders(df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Map DataFrame columns to template placeholders.
        
        Args:
            df: DataFrame with recipient data
            column_mapping: Dictionary mapping placeholder names to column names
            
        Returns:
            DataFrame with mapped columns
        """
        df_mapped = df.copy()
        
        # Add mapped columns
        for placeholder, column in column_mapping.items():
            if column in df.columns:
                # Clean the placeholder name (remove {{ }})
                clean_placeholder = placeholder.replace('{{', '').replace('}}', '')
                df_mapped[f'placeholder_{clean_placeholder}'] = df[column]
            else:
                # Column not found, add empty column
                clean_placeholder = placeholder.replace('{{', '').replace('}}', '')
                df_mapped[f'placeholder_{clean_placeholder}'] = ''
        
        return df_mapped
    
    @staticmethod
    def get_default_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
        """
        Get default column mapping based on DataFrame columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary mapping placeholders to column names
        """
        mapping = {}
        columns_lower = [col.lower() for col in df.columns]
        
        # Common mappings
        if 'name' in columns_lower or 'first_name' in columns_lower or 'full_name' in columns_lower:
            name_col = next(col for col in df.columns if col.lower() in ['name', 'first_name', 'full_name'])
            mapping['{{name}}'] = name_col
        
        if 'company' in columns_lower or 'organization' in columns_lower:
            company_col = next(col for col in df.columns if col.lower() in ['company', 'organization'])
            mapping['{{company}}'] = company_col
        
        if 'email' in columns_lower:
            email_col = next(col for col in df.columns if col.lower() == 'email')
            mapping['{{email}}'] = email_col
        
        return mapping
    
    @staticmethod
    def render_personalized_email(row: pd.Series, template_text: str, 
                                column_mapping: Dict[str, str], 
                                sender_name: str, subject: str, message: str) -> str:
        """
        Render personalized email for a specific recipient.
        
        Args:
            row: DataFrame row with recipient data
            template_text: Email template text
            column_mapping: Mapping of placeholders to columns
            sender_name: Sender's name
            subject: Email subject
            message: Email message content
            
        Returns:
            Personalized email content
        """
        # Prepare data for template
        template_data = {
            'sender_name': sender_name,
            'subject': subject,
            'message': message
        }
        
        # Add mapped column data
        for placeholder, column in column_mapping.items():
            if column in row.index:
                clean_placeholder = placeholder.replace('{{', '').replace('}}', '')
                template_data[clean_placeholder] = str(row[column]) if pd.notna(row[column]) else ''
            else:
                # Column not found, use empty string
                clean_placeholder = placeholder.replace('{{', '').replace('}}', '')
                template_data[clean_placeholder] = ''
        
        # Add email if available
        if 'email' in row.index:
            template_data['email'] = str(row['email']) if pd.notna(row['email']) else ''
        
        # Render template
        try:
            return EmailTemplates.render_template(template_text, template_data)
        except Exception as e:
            # Fallback to basic template if rendering fails
            fallback = f"Hello {template_data.get('name', 'there')},\n\n{message}\n\nBest regards,\n{sender_name}"
            return fallback
    
    @staticmethod
    def preview_personalization(df: pd.DataFrame, template_text: str, 
                              column_mapping: Dict[str, str], 
                              sender_name: str, subject: str, message: str,
                              num_previews: int = 3) -> List[Dict]:
        """
        Preview personalization for first few recipients.
        
        Args:
            df: DataFrame with recipient data
            template_text: Email template text
            column_mapping: Mapping of placeholders to columns
            sender_name: Sender's name
            subject: Email subject
            message: Email message content
            num_previews: Number of previews to generate
            
        Returns:
            List of preview dictionaries
        """
        previews = []
        
        for i, (idx, row) in enumerate(df.head(num_previews).iterrows()):
            if i >= num_previews:
                break
                
            personalized_content = Personalizer.render_personalized_email(
                row, template_text, column_mapping, sender_name, subject, message
            )
            
            preview = {
                'recipient_index': idx,
                'email': str(row.get('email', 'N/A')),
                'name': str(row.get('name', 'N/A')) if 'name' in row.index else 'N/A',
                'personalized_content': personalized_content[:500] + '...' if len(personalized_content) > 500 else personalized_content
            }
            
            previews.append(preview)
        
        return previews
    
    @staticmethod
    def validate_column_mapping(df: pd.DataFrame, column_mapping: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Validate column mapping against DataFrame.
        
        Args:
            df: DataFrame to validate against
            column_mapping: Column mapping to validate
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'valid_columns': [],
            'missing_columns': [],
            'empty_columns': []
        }
        
        for placeholder, column in column_mapping.items():
            if column in df.columns:
                validation['valid_columns'].append(f"{placeholder} -> {column}")
                
                # Check if column has data
                if df[column].isna().all() or (df[column] == '').all():
                    validation['empty_columns'].append(f"{placeholder} -> {column} (no data)")
            else:
                validation['missing_columns'].append(f"{placeholder} -> {column}")
        
        return validation 