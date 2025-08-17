#!/usr/bin/env python3
"""
Simple test script to verify core functionality.
Run this to test the core modules before using the Streamlit app.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all core modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from core.settings import settings
        print("✅ Settings imported successfully")
        
        from core.file_parser import FileParser
        print("✅ FileParser imported successfully")
        
        from core.validators import EmailValidator
        print("✅ EmailValidator imported successfully")
        
        from core.templates import EmailTemplates
        print("✅ EmailTemplates imported successfully")
        
        from core.personalize import Personalizer
        print("✅ Personalizer imported successfully")
        
        from core.rate_limit import RateLimiter
        print("✅ RateLimiter imported successfully")
        
        from core.logger import CampaignLogger
        print("✅ CampaignLogger imported successfully")
        
        from core.mailer import EmailMailer
        print("✅ EmailMailer imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_file_parser():
    """Test file parsing functionality."""
    print("\n📁 Testing file parser...")
    
    try:
        from core.file_parser import FileParser
        
        # Test with sample CSV
        sample_file = "data/samples/sample_recipients.csv"
        
        if not os.path.exists(sample_file):
            print(f"⚠️ Sample file not found: {sample_file}")
            return False
        
        df, columns = FileParser.parse_file(sample_file)
        print(f"✅ Parsed {len(df)} rows and {len(columns)} columns")
        
        # Test auto-detection
        email_col = FileParser.auto_detect_email_column(df)
        print(f"✅ Auto-detected email column: {email_col}")
        
        # Test preview
        preview = FileParser.get_preview(df, 3)
        print(f"✅ Preview generated with {len(preview)} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ File parser test failed: {e}")
        return False

def test_validators():
    """Test email validation functionality."""
    print("\n🔍 Testing validators...")
    
    try:
        from core.validators import EmailValidator
        
        # Test email validation
        test_emails = [
            "test@example.com",
            "invalid-email",
            "another@test.org",
            "spaces @example.com"
        ]
        
        for email in test_emails:
            is_valid, result = EmailValidator.validate_email_syntax(email)
            status = "✅" if is_valid else "❌"
            print(f"{status} {email}: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validator test failed: {e}")
        return False

def test_templates():
    """Test template functionality."""
    print("\n📝 Testing templates...")
    
    try:
        from core.templates import EmailTemplates
        
        # Test default templates
        plain_template = EmailTemplates.get_default_template('plain')
        html_template = EmailTemplates.get_default_template('html')
        
        print(f"✅ Plain template length: {len(plain_template)}")
        print(f"✅ HTML template length: {len(html_template)}")
        
        # Test template rendering
        test_data = {
            'name': 'John Doe',
            'company': 'Test Corp',
            'sender_name': 'Test Sender',
            'subject': 'Test Subject',
            'message': 'Hello {{name}}!'
        }
        
        rendered = EmailTemplates.render_template(plain_template, test_data)
        print(f"✅ Template rendered successfully ({len(rendered)} chars)")
        
        return True
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

def test_rate_limiter():
    """Test rate limiting functionality."""
    print("\n⏱️ Testing rate limiter...")
    
    try:
        from core.rate_limit import RateLimiter
        
        limiter = RateLimiter(60)
        
        # Test rate info
        info = limiter.get_rate_limit_info()
        print(f"✅ Rate limit: {info['emails_per_minute']} emails/min")
        
        # Test completion time estimation
        eta = limiter.estimate_completion_time(100)
        print(f"✅ ETA for 100 emails: {eta:.1f} minutes")
        
        # Test progress info
        progress = limiter.get_progress_info(25, 100)
        print(f"✅ Progress: {progress['percentage']}% ({progress['sent']}/{progress['total']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiter test failed: {e}")
        return False

def test_settings():
    """Test settings configuration."""
    print("\n⚙️ Testing settings...")
    
    try:
        from core.settings import settings
        
        print(f"✅ SMTP Host: {settings.SMTP_HOST}")
        print(f"✅ SMTP Port: {settings.SMTP_PORT}")
        print(f"✅ Rate Limit: {settings.RATE_PER_MIN} emails/min")
        print(f"✅ Storage Dir: {settings.STORAGE_DIR}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting core functionality tests...\n")
    
    tests = [
        test_imports,
        test_settings,
        test_file_parser,
        test_validators,
        test_templates,
        test_rate_limiter
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Core functionality is working correctly.")
        print("\nNext steps:")
        print("1. Copy env_example.txt to .env")
        print("2. Add your SMTP credentials to .env")
        print("3. Run: streamlit run app.py")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 