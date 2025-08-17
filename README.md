# 📧 Bulk Email Automation Tool

A powerful, user-friendly bulk email automation tool built with Python and Streamlit. Send personalized emails to large lists with advanced features like validation, rate limiting, and comprehensive tracking.

## ✨ Features

- **📁 Multi-format Support**: Upload CSV, Excel (.xlsx), or text files
- **🔍 Smart Validation**: Automatic email validation and deduplication
- **🎨 Personalization**: Use placeholders like `{{name}}` and `{{company}}`
- **📧 Template System**: Plain text and HTML email templates
- **⏱️ Rate Limiting**: Configurable sending rates to avoid provider limits
- **📊 Campaign Tracking**: Monitor progress and track results
- **🔄 Retry Logic**: Automatic retry for failed emails
- **📈 Analytics**: Detailed campaign statistics and reporting
- **🔒 Secure**: Uses SMTP with proper authentication

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- Gmail account (or other SMTP provider)
- Gmail App Password (recommended over regular password)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd email-automation

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

1. Copy the example environment file:
   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` with your SMTP credentials:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your.email@gmail.com
   SMTP_PASS=your_app_password
   SENDER_NAME=Your Name
   REPLY_TO=support@yourdomain.com
   RATE_PER_MIN=60
   ```

**Important**: For Gmail, use an **App Password**, not your regular password. [Learn how to create one](https://support.google.com/accounts/answer/185833).

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

## 📖 Usage Guide

### Step 1: Upload & Validate

1. Go to **"📁 Upload & Validate"** page
2. Upload your CSV/Excel file with email addresses
3. The tool will auto-detect email columns
4. Map personalization columns (name, company, etc.)
5. Click **"Validate Emails"** to clean your list

### Step 2: Compose Email

1. Go to **"✍️ Compose Email"** page
2. Fill in sender name, subject, and message
3. Use placeholders like `{{name}}` and `{{company}}`
4. Choose email type (plain text or HTML)
5. Set rate limiting (emails per minute)
6. Click **"Save Campaign"**

### Step 3: Send Campaign

1. Go to **"📤 Send Campaign"** page
2. Review campaign summary
3. Send a test email to verify everything works
4. Click **"Start Sending Campaign"**
5. Monitor progress with real-time updates

### Step 4: Monitor Results

1. Go to **"📊 Campaign History"** page
2. View campaign statistics and success rates
3. Download failed recipient lists
4. Retry failed emails if needed

## 🎯 Supported File Formats

### CSV Files
```csv
email,name,company
john@example.com,John Doe,Acme Corp
jane@example.com,Jane Smith,Tech Solutions
```

### Excel Files (.xlsx)
- Same structure as CSV
- Multiple sheets supported
- Auto-detects email columns

### Text Files
- One email per line
- Automatic email extraction using regex
- Simple format for basic lists

## 🔧 Configuration Options

### SMTP Settings
- **Gmail**: `smtp.gmail.com:587` (STARTTLS)
- **Outlook**: `smtp-mail.outlook.com:587` (STARTTLS)
- **Custom**: Any SMTP server with authentication

### Rate Limiting
- **Default**: 60 emails per minute
- **Range**: 10-200 emails per minute
- **Purpose**: Avoid provider throttling and improve deliverability

### Personalization Placeholders
- `{{name}}` - Recipient's name
- `{{company}}` - Company name
- `{{email}}` - Email address
- `{{sender_name}}` - Your name
- `{{subject}}` - Email subject
- `{{message}}` - Email content

## 📊 Sample Data

Use the included sample file to test the tool:
```
data/samples/sample_recipients.csv
```

This file contains 5 sample recipients with names and companies for testing personalization.

## 🛠️ Advanced Features

### Batch Processing
- Configurable batch sizes (10-100 emails)
- Delay between batches to avoid overwhelming servers
- Progress tracking with real-time updates

### Error Handling
- Automatic retry with exponential backoff
- Detailed error logging and reporting
- Continue-on-error option for large campaigns

### Database Logging
- SQLite database for campaign tracking
- Comprehensive recipient status tracking
- Export capabilities for analysis

### Template System
- Jinja2-based templating engine
- HTML and plain text support
- Automatic fallback for missing data

## 🔒 Security & Best Practices

### Email Security
- Use App Passwords, not regular passwords
- Enable 2FA on your email account
- Monitor for unusual activity

### Deliverability
- Start with small lists to test
- Use consistent sender information
- Include unsubscribe instructions
- Respect recipient preferences

### Rate Limiting
- Start conservative (30-60 emails/minute)
- Monitor bounce rates and adjust
- Follow provider guidelines

## 🐛 Troubleshooting

### Common Issues

**SMTP Connection Failed**
- Check credentials in `.env` file
- Verify App Password is correct
- Check firewall/network settings

**Emails Not Sending**
- Verify rate limiting settings
- Check SMTP provider limits
- Review error logs in console

**Personalization Not Working**
- Verify column mapping is correct
- Check placeholder syntax (`{{name}}`)
- Ensure data exists in mapped columns

### Debug Mode

Enable detailed logging by setting log level in `core/logger.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📁 Project Structure

```
email-automation/
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── env_example.txt           # Environment variables template
├── README.md                 # This file
├── core/                     # Core functionality modules
│   ├── __init__.py
│   ├── settings.py           # Configuration management
│   ├── file_parser.py        # File parsing and column detection
│   ├── validators.py         # Email validation and cleaning
│   ├── templates.py          # Email template system
│   ├── personalize.py        # Personalization engine
│   ├── mailer.py            # SMTP email sending
│   ├── rate_limit.py        # Rate limiting and throttling
│   └── logger.py            # Database logging and tracking
├── data/                     # Sample data and attachments
│   └── samples/
│       └── sample_recipients.csv
└── storage/                  # Runtime storage (auto-created)
    ├── campaigns.db         # SQLite database
    ├── attachments/         # File attachments
    └── logs/               # Application logs
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for legitimate business communication only. Please:
- Respect anti-spam laws (CAN-SPAM, GDPR, etc.)
- Only email people who have opted in
- Include proper unsubscribe mechanisms
- Monitor bounce rates and complaints

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the error logs in the console
3. Verify your SMTP configuration
4. Test with the sample data first

---

**Happy emailing! 📧✨** 