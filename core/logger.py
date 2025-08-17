import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from .settings import settings

class CampaignLogger:
    """Log campaign and recipient data to SQLite database."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize logger with database path.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or settings.DB_PATH
        self._ensure_storage_dir()
        self._init_database()
        
        # Setup file logging
        self._setup_file_logging()
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        storage_dir = Path(self.db_path).parent
        storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                template_type TEXT NOT NULL,
                sender_name TEXT NOT NULL,
                total_recipients INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'created'
            )
        ''')
        
        # Create recipients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                name TEXT,
                company TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                sent_at TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_id ON recipients (campaign_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON recipients (email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON recipients (status)')
        
        conn.commit()
        conn.close()
    
    def _setup_file_logging(self):
        """Setup file logging for the application."""
        log_dir = Path(settings.STORAGE_DIR) / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / 'email_automation.log'
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def create_campaign(self, subject: str, template_type: str, sender_name: str) -> int:
        """
        Create a new campaign record.
        
        Args:
            subject: Campaign subject
            template_type: Type of template (plain/html)
            sender_name: Name of sender
            
        Returns:
            Campaign ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO campaigns (subject, template_type, sender_name)
            VALUES (?, ?, ?)
        ''', (subject, template_type, sender_name))
        
        campaign_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.logger.info(f"Created campaign {campaign_id}: {subject}")
        return campaign_id
    
    def add_recipients(self, campaign_id: int, recipients_data: List[Dict]) -> None:
        """
        Add recipients to a campaign.
        
        Args:
            campaign_id: ID of the campaign
            recipients_data: List of recipient dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for recipient in recipients_data:
            cursor.execute('''
                INSERT INTO recipients (campaign_id, email, name, company)
                VALUES (?, ?, ?, ?)
            ''', (
                campaign_id,
                recipient.get('email', ''),
                recipient.get('name', ''),
                recipient.get('company', '')
            ))
        
        # Update total recipients count
        cursor.execute('''
            UPDATE campaigns 
            SET total_recipients = (SELECT COUNT(*) FROM recipients WHERE campaign_id = ?)
            WHERE id = ?
        ''', (campaign_id, campaign_id))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Added {len(recipients_data)} recipients to campaign {campaign_id}")
    
    def update_recipient_status(self, campaign_id: int, email: str, status: str, 
                               error_message: str = None, retry_count: int = None) -> None:
        """
        Update recipient status.
        
        Args:
            campaign_id: ID of the campaign
            email: Recipient email
            status: New status (sent, failed, pending)
            error_message: Error message if failed
            retry_count: Number of retry attempts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == 'sent':
            cursor.execute('''
                UPDATE recipients 
                SET status = ?, sent_at = CURRENT_TIMESTAMP
                WHERE campaign_id = ? AND email = ?
            ''', (status, campaign_id, email))
        else:
            update_fields = ['status = ?']
            params = [status]
            
            if error_message:
                update_fields.append('error_message = ?')
                params.append(error_message)
            
            if retry_count is not None:
                update_fields.append('retry_count = ?')
                params.append(retry_count)
            
            params.extend([campaign_id, email])
            
            cursor.execute(f'''
                UPDATE recipients 
                SET {', '.join(update_fields)}
                WHERE campaign_id = ? AND email = ?
            ''', params)
        
        conn.commit()
        conn.close()
        
        if status == 'sent':
            self.logger.info(f"Email sent to {email} in campaign {campaign_id}")
        elif status == 'failed':
            self.logger.error(f"Failed to send email to {email} in campaign {campaign_id}: {error_message}")
    
    def get_campaign_summary(self, campaign_id: int) -> Dict:
        """
        Get summary statistics for a campaign.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Dictionary with campaign summary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get campaign info
        cursor.execute('''
            SELECT subject, template_type, sender_name, total_recipients, created_at, status
            FROM campaigns WHERE id = ?
        ''', (campaign_id,))
        
        campaign_row = cursor.fetchone()
        if not campaign_row:
            conn.close()
            return {}
        
        # Get recipient statistics
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM recipients 
            WHERE campaign_id = ?
            GROUP BY status
        ''', (campaign_id,))
        
        status_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'campaign_id': campaign_id,
            'subject': campaign_row[0],
            'template_type': campaign_row[1],
            'sender_name': campaign_row[2],
            'total_recipients': campaign_row[3],
            'created_at': campaign_row[4],
            'status': campaign_row[5],
            'sent_count': status_counts.get('sent', 0),
            'failed_count': status_counts.get('failed', 0),
            'pending_count': status_counts.get('pending', 0),
            'success_rate': round((status_counts.get('sent', 0) / campaign_row[3]) * 100, 1) if campaign_row[3] > 0 else 0
        }
    
    def get_failed_recipients(self, campaign_id: int) -> List[Dict]:
        """
        Get list of failed recipients for a campaign.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            List of failed recipient dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, name, company, error_message, retry_count
            FROM recipients 
            WHERE campaign_id = ? AND status = 'failed'
        ''', (campaign_id,))
        
        failed_recipients = []
        for row in cursor.fetchall():
            failed_recipients.append({
                'email': row[0],
                'name': row[1],
                'company': row[2],
                'error_message': row[3],
                'retry_count': row[4]
            })
        
        conn.close()
        return failed_recipients
    
    def get_all_campaigns(self) -> List[Dict]:
        """
        Get all campaigns with summary statistics.
        
        Returns:
            List of campaign dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.subject, c.template_type, c.sender_name, 
                   c.total_recipients, c.created_at, c.status,
                   COUNT(CASE WHEN r.status = 'sent' THEN 1 END) as sent_count,
                   COUNT(CASE WHEN r.status = 'failed' THEN 1 END) as failed_count
            FROM campaigns c
            LEFT JOIN recipients r ON c.id = r.campaign_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        ''')
        
        campaigns = []
        for row in cursor.fetchall():
            campaigns.append({
                'id': row[0],
                'subject': row[1],
                'template_type': row[2],
                'sender_name': row[3],
                'total_recipients': row[4],
                'created_at': row[5],
                'status': row[6],
                'sent_count': row[7] or 0,
                'failed_count': row[8] or 0,
                'success_rate': round(((row[7] or 0) / row[4]) * 100, 1) if row[4] > 0 else 0
            })
        
        conn.close()
        return campaigns 