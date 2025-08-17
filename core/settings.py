import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Configuration settings for the email automation tool."""
    
    # SMTP Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    SENDER_NAME = os.getenv('SENDER_NAME', 'Email Automation')
    REPLY_TO = os.getenv('REPLY_TO', '')
    
    # Rate Limiting
    RATE_PER_MIN = int(os.getenv('RATE_PER_MIN', '60'))
    
    # File Paths
    STORAGE_DIR = 'storage'
    ATTACHMENTS_DIR = os.path.join(STORAGE_DIR, 'attachments')
    DB_PATH = os.path.join(STORAGE_DIR, 'campaigns.db')
    
    # Validation
    MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_RECIPIENTS = 10000
    
    @classmethod
    def validate(cls):
        """Validate required settings."""
        required = ['SMTP_USER', 'SMTP_PASS']
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True

# Global settings instance
settings = Settings() 