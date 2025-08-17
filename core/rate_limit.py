import time
from typing import Optional

class RateLimiter:
    """Simple rate limiter for email sending."""
    
    def __init__(self, emails_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            emails_per_minute: Maximum emails to send per minute
        """
        self.emails_per_minute = emails_per_minute
        self.last_send_time = 0
        self.min_interval = 60.0 / emails_per_minute if emails_per_minute > 0 else 0
    
    def wait_if_needed(self) -> None:
        """
        Wait if necessary to respect rate limits.
        """
        if self.min_interval <= 0:
            return
        
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_send_time = time.time()
    
    def set_rate(self, emails_per_minute: int) -> None:
        """
        Update rate limit.
        
        Args:
            emails_per_minute: New rate limit
        """
        self.emails_per_minute = emails_per_minute
        self.min_interval = 60.0 / emails_per_minute if emails_per_minute > 0 else 0
    
    def get_current_rate(self) -> int:
        """
        Get current rate limit.
        
        Returns:
            Current emails per minute limit
        """
        return self.emails_per_minute
    
    def estimate_completion_time(self, total_emails: int) -> float:
        """
        Estimate time to complete sending all emails.
        
        Args:
            total_emails: Total number of emails to send
            
        Returns:
            Estimated time in minutes
        """
        if self.emails_per_minute <= 0:
            return 0
        
        return total_emails / self.emails_per_minute
    
    def get_progress_info(self, sent_count: int, total_count: int) -> dict:
        """
        Get progress information for the current campaign.
        
        Args:
            sent_count: Number of emails sent so far
            total_count: Total number of emails to send
            
        Returns:
            Dictionary with progress information
        """
        if total_count == 0:
            return {
                'sent': 0,
                'total': 0,
                'percentage': 0,
                'remaining': 0,
                'eta_minutes': 0
            }
        
        percentage = (sent_count / total_count) * 100
        remaining = total_count - sent_count
        
        if self.emails_per_minute > 0:
            eta_minutes = remaining / self.emails_per_minute
        else:
            eta_minutes = 0
        
        return {
            'sent': sent_count,
            'total': total_count,
            'percentage': round(percentage, 1),
            'remaining': remaining,
            'eta_minutes': round(eta_minutes, 1)
        }
    
    def get_rate_limit_info(self) -> dict:
        """
        Get current rate limiting information.
        
        Returns:
            Dictionary with rate limit info
        """
        return {
            'emails_per_minute': self.emails_per_minute
        } 