import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
import time
from datetime import datetime

# Import core modules
from core.settings import settings
from core.file_parser import FileParser
from core.validators import EmailValidator
from core.templates import EmailTemplates
from core.personalize import Personalizer
from core.mailer import EmailMailer
from core.logger import CampaignLogger
from core.rate_limit import RateLimiter

# Page configuration
st.set_page_config(
    page_title="Bulk Email Automation",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Simple, professional color scheme */
    .main-header {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        color: #495057;
        text-align: center;
    }
    
    .metric-card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        color: #495057;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .success-card {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 8px;
        color: #155724;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .warning-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 8px;
        color: #856404;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .info-card {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        padding: 1rem;
        border-radius: 8px;
        color: #0c5460;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .error-card {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 8px;
        color: #721c24;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #f8f9fa;
    }
    
    .css-1d391kg .css-1v0mbdj {
        background: #f8f9fa;
    }
    
    /* Button styling */
    .stButton > button {
        background: #6c757d;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #5a6268;
        transform: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:active {
        transform: none;
    }
    
    /* Primary button */
    .stButton > button[data-baseweb="button"] {
        background: #007bff;
    }
    
    .stButton > button[data-baseweb="button"]:hover {
        background: #0056b3;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #6c757d;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        background: #f8f9fa;
        color: #6c757d;
    }
    
    /* Progress container */
    .progress-container {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Campaign card */
    .campaign-card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #6c757d;
    }
    
    /* Metric styling */
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
        color: #495057;
    }
    
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.7;
        color: #6c757d;
    }
    
    /* Status colors */
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    
    /* Form elements */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e9ecef;
    }
    
    .stSelectbox > div > div {
        border-radius: 6px;
    }
    
    .stTextInput > div > div > input {
        border-radius: 6px;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 6px;
    }
    
    .stSlider > div > div > div > div {
        border-radius: 6px;
    }
    
    .stCheckbox > div > div {
        border-radius: 4px;
    }
    
    .stNumberInput > div > div > input {
        border-radius: 6px;
    }
    
    .stFileUploader > div {
        border-radius: 8px;
    }
    
    /* Navigation styling */
    .nav-container {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .nav-title {
        color: #495057;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_campaign' not in st.session_state:
    st.session_state.current_campaign = None
if 'recipients_df' not in st.session_state:
    st.session_state.recipients_df = None
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}

def main():
    """Main application function."""
    
    # Sidebar with clean styling
    st.sidebar.markdown('<div class="nav-container"><div class="nav-title">📧 Email Automation</div><p style="margin: 0; color: #6c757d; font-size: 0.9rem;">Professional Bulk Email Tool</p></div>', unsafe_allow_html=True)
    
    # Check if credentials are configured
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        st.sidebar.markdown('<div class="warning-card"><div class="metric-value">⚠️</div><div class="metric-label">SMTP Not Configured</div><p>Please create a .env file with your credentials</p></div>', unsafe_allow_html=True)
        st.sidebar.info("Copy env_example.txt to .env and add your SMTP credentials")
        st.sidebar.code("cp env_example.txt .env")
        return
    
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard"
    
    # Top navbar (horizontal)
    st.markdown('<div class="nav-container"><div class="nav-title">🧭 Navigation</div></div>', unsafe_allow_html=True)
    nav_options = [
        "🏠 Dashboard",
        "📁 Upload & Validate",
        "✍️ Compose Email",
        "📤 Send Campaign",
        "📊 Campaign History",
    ]
    page = st.radio(
        "Navigation",
        nav_options,
        index=nav_options.index(st.session_state.current_page),
        horizontal=True,
        label_visibility="collapsed",
        key="top_nav",
    )
    
    # Update session state when page changes
    if page != st.session_state.current_page:
        st.session_state.current_page = page
    
    # Show the selected page
    if st.session_state.current_page == "🏠 Dashboard":
        show_dashboard()
    elif st.session_state.current_page == "📁 Upload & Validate":
        show_upload_validate()
    elif st.session_state.current_page == "✍️ Compose Email":
        show_compose_email()
    elif st.session_state.current_page == "📤 Send Campaign":
        show_send_campaign()
    elif st.session_state.current_page == "📊 Campaign History":
        show_campaign_history()

def show_dashboard():
    """Show dashboard with overview and quick actions."""
    # Main header with gradient
    st.markdown('<div class="main-header"><h1>🚀 Bulk Email Automation Dashboard</h1><p>Professional email campaigns made simple</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
            <h3>🎯 What You Can Do</h3>
            <ul style="font-size: 1.1rem; line-height: 2;">
                <li><strong>📁 Upload</strong> CSV, Excel, or text files with email addresses</li>
                <li><strong>🔍 Validate</strong> and clean your email list automatically</li>
                <li><strong>✍️ Personalize</strong> emails with smart templates and placeholders</li>
                <li><strong>📤 Send</strong> campaigns with intelligent rate limiting</li>
                <li><strong>📊 Monitor</strong> results and retry failed emails</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick stats with styled cards
        if st.session_state.recipients_df is not None:
            st.subheader("📊 Campaign Statistics")
            total = len(st.session_state.recipients_df)
            
            col1_1, col1_2, col1_3 = st.columns(3)
            with col1_1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{total}</div><div class="metric-label">Total Recipients</div></div>', unsafe_allow_html=True)
            
            if 'is_valid' in st.session_state.recipients_df.columns:
                valid = st.session_state.recipients_df['is_valid'].sum()
                invalid = total - valid
                
                with col1_2:
                    st.markdown(f'<div class="success-card"><div class="metric-value">{valid}</div><div class="metric-label">Valid Emails</div></div>', unsafe_allow_html=True)
                
                with col1_3:
                    st.markdown(f'<div class="warning-card"><div class="metric-value">{invalid}</div><div class="metric-label">Invalid Emails</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-card"><h3>🚀 Quick Actions</h3></div>', unsafe_allow_html=True)
        
        if st.button("📁 Upload New File", key="upload_btn"):
            st.session_state.current_page = "📁 Upload & Validate"
        
        if st.button("✍️ Compose Email", key="compose_btn"):
            st.session_state.current_page = "✍️ Compose Email"
        
        if st.button("📤 Send Campaign", key="send_btn"):
            st.session_state.current_page = "📤 Send Campaign"
        
        # SMTP Status with better styling
        st.markdown('<div class="metric-card"><h3>🔧 SMTP Status</h3></div>', unsafe_allow_html=True)
        try:
            mailer = EmailMailer()
            success, message = mailer.test_connection()
            if success:
                st.markdown('<div class="success-card"><div class="metric-value">✅</div><div class="metric-label">Connected</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warning-card"><div class="metric-value">❌</div><div class="metric-label">Connection Failed</div></div>', unsafe_allow_html=True)
                st.caption(f"Error: {message}")
        except Exception as e:
            st.markdown('<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Configuration Error</div></div>', unsafe_allow_html=True)
            st.caption(f"Error: {str(e)}")

def show_upload_validate():
    """Show file upload and validation page."""
    st.markdown('<div class="main-header"><h1>📁 Upload & Validate</h1><p>Upload your email list and validate it automatically</p></div>', unsafe_allow_html=True)
    
    # File upload with styled area
    st.markdown('<div class="upload-area"><h3>📁 Step 1: Upload Your File</h3></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'txt'],
        help="Supported formats: CSV, Excel (.xlsx), or text files"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            # Parse file
            df, columns = FileParser.parse_file(tmp_file_path)
            
            # Auto-detect email column
            email_column = FileParser.auto_detect_email_column(df)
            
            st.markdown(f'<div class="success-card"><div class="metric-value">✅</div><div class="metric-label">File uploaded successfully!</div><p>Found {len(df)} rows and {len(columns)} columns</p></div>', unsafe_allow_html=True)
            
            # Show preview
            st.markdown('<div class="info-card"><h3>📋 File Preview</h3></div>', unsafe_allow_html=True)
            preview_df = FileParser.get_preview(df, 10)
            st.dataframe(preview_df, use_container_width=True)
            
            # Column selection
            st.markdown('<div class="metric-card"><h3>⚙️ Step 2: Configure Columns</h3></div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Email Column")
                email_col = st.selectbox(
                    "Select the column containing email addresses:",
                    columns,
                    index=columns.index(email_column) if email_column else 0
                )
            
            with col2:
                st.subheader("Personalization Columns")
                st.write("Map columns to template placeholders:")
                
                # Get default mapping
                default_mapping = Personalizer.get_default_column_mapping(df)
                
                # Name column
                name_col = st.selectbox(
                    "Name column (for {{name}}):",
                    [''] + columns,
                    index=columns.index(default_mapping.get('{{name}}', '')) + 1 if default_mapping.get('{{name}}') in columns else 0
                )
                
                # Company column
                company_col = st.selectbox(
                    "Company column (for {{company}}):",
                    [''] + columns,
                    index=columns.index(default_mapping.get('{{company}}', '')) + 1 if default_mapping.get('{{company}}') in columns else 0
                )
            
            # Store column mapping
            column_mapping = {}
            if name_col:
                column_mapping['{{name}}'] = name_col
            if company_col:
                column_mapping['{{company}}'] = company_col
            
            st.session_state.column_mapping = column_mapping
            
            # Validation
            if st.button("🔍 Validate Emails"):
                with st.spinner("Validating emails..."):
                    # Clean and validate emails
                    df_clean = EmailValidator.clean_emails(df, email_col)
                    
                    # Remove duplicates
                    df_deduped = EmailValidator.remove_duplicates(df_clean, 'email_clean')
                    
                    # Filter valid emails
                    df_valid = EmailValidator.filter_valid_emails(df_deduped)
                    
                    # Store in session state
                    st.session_state.recipients_df = df_valid
                    
                    # Show validation results
                    st.markdown('<div class="success-card"><h3>🎯 Step 3: Validation Results</h3></div>', unsafe_allow_html=True)
                    
                    summary = EmailValidator.get_validation_summary(df_deduped)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["total_emails"]}</div><div class="metric-label">Total Emails</div></div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown(f'<div class="success-card"><div class="metric-value">{summary["valid_emails"]}</div><div class="metric-label">Valid Emails</div></div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown(f'<div class="warning-card"><div class="metric-value">{summary["invalid_emails"]}</div><div class="metric-label">Invalid Emails</div></div>', unsafe_allow_html=True)
                    with col4:
                        st.markdown(f'<div class="info-card"><div class="metric-value">{summary["valid_percentage"]}%</div><div class="metric-label">Success Rate</div></div>', unsafe_allow_html=True)
                    
                    # Show validation details
                    if summary['invalid_emails'] > 0:
                        st.markdown('<div class="warning-card"><h3>❌ Invalid Emails</h3></div>', unsafe_allow_html=True)
                        invalid_df = df_deduped[~df_deduped['is_valid']]
                        st.dataframe(invalid_df[['email_original', 'validation_error']], use_container_width=True)
                    
                    # Show valid emails
                    st.markdown('<div class="success-card"><h3>✅ Valid Emails</h3></div>', unsafe_allow_html=True)
                    st.dataframe(df_valid[['email_clean', 'name', 'company']].head(20), use_container_width=True)
                    
                    if len(df_valid) > 20:
                        st.caption(f"Showing first 20 of {len(df_valid)} valid emails")
                    
                    st.markdown(f'<div class="success-card"><div class="metric-value">🎉</div><div class="metric-label">Validation Complete!</div><p>{summary["valid_emails"]} emails ready for sending</p></div>', unsafe_allow_html=True)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.markdown(f'<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Error processing file</div><p>{str(e)}</p></div>', unsafe_allow_html=True)
            os.unlink(tmp_file_path)

def show_compose_email():
    """Show email composition page."""
    st.markdown('<div class="main-header"><h1>✍️ Compose Email</h1><p>Create your personalized email campaign</p></div>', unsafe_allow_html=True)
    
    if st.session_state.recipients_df is None:
        st.markdown('<div class="warning-card"><div class="metric-value">⚠️</div><div class="metric-label">No Recipients Found</div><p>Please upload and validate a file first!</p></div>', unsafe_allow_html=True)
        if st.button("📁 Go to Upload"):
            st.session_state.current_page = "📁 Upload & Validate"
        return
    
    # Email composition form
    st.markdown('<div class="metric-card"><h3>✍️ Compose Your Email</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Basic email details
        st.markdown('<div class="info-card"><h4>📧 Basic Details</h4></div>', unsafe_allow_html=True)
        sender_name = st.text_input("From Name:", value=settings.SENDER_NAME)
        subject = st.text_input("Subject:", placeholder="Enter email subject...")
        
        # Template type
        template_type = st.selectbox("Email Type:", ["plain", "html"])
        
        # Message content
        st.markdown('<div class="info-card"><h4>💬 Message Content</h4></div>', unsafe_allow_html=True)
        message = st.text_area(
            "Message:",
            height=200,
            placeholder="Enter your email message...\n\nUse placeholders like {{name}} and {{company}} for personalization."
        )
        
        # Template preview
        if message:
            st.subheader("📝 Template Preview")
            
            # Show available placeholders
            placeholders = EmailTemplates.get_available_placeholders()
            st.write("**Available placeholders:**")
            for placeholder in placeholders:
                st.caption(f"• {placeholder}")
            
            # Show preview for first few recipients
            if st.button("👀 Preview Personalization"):
                previews = Personalizer.preview_personalization(
                    st.session_state.recipients_df,
                    message,
                    st.session_state.column_mapping,
                    sender_name,
                    subject,
                    message
                )
                
                for preview in previews:
                    with st.expander(f"Preview for {preview['email']} ({preview['name']})"):
                        st.text(preview['personalized_content'])
    
    with col2:
        st.markdown('<div class="info-card"><h3>📊 Campaign Info</h3></div>', unsafe_allow_html=True)
        
        total_recipients = len(st.session_state.recipients_df)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total_recipients}</div><div class="metric-label">Recipients</div></div>', unsafe_allow_html=True)
        
        # Rate limiting
        st.markdown('<div class="warning-card"><h4>⏱️ Rate Limiting</h4></div>', unsafe_allow_html=True)
        rate_per_min = st.slider("Emails per minute:", 10, 200, 60)
        
        # Estimate completion time
        rate_limiter = RateLimiter(rate_per_min)
        eta_minutes = rate_limiter.estimate_completion_time(total_recipients)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{eta_minutes:.1f}</div><div class="metric-label">Estimated Time (min)</div></div>', unsafe_allow_html=True)
        
        # Attachments
        st.markdown('<div class="info-card"><h4>📎 Attachments</h4></div>', unsafe_allow_html=True)
        attachments = st.file_uploader(
            "Add attachments:",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx', 'txt', 'jpg', 'png']
        )
        
        if attachments:
            st.markdown(f'<div class="success-card"><div class="metric-value">📎</div><div class="metric-label">{len(attachments)} file(s) selected</div></div>', unsafe_allow_html=True)
    
    # Save campaign
    if st.button("💾 Save Campaign"):
        if not subject or not message:
            st.error("Please fill in subject and message!")
            return
        
        # Create campaign in database
        try:
            logger = CampaignLogger()
            campaign_id = logger.create_campaign(subject, template_type, sender_name)
            
            # Prepare recipients data
            recipients_data = []
            for _, row in st.session_state.recipients_df.iterrows():
                recipients_data.append({
                    'email': row['email_clean'],
                    'name': row.get('name', ''),
                    'company': row.get('company', '')
                })
            
            # Add recipients to campaign
            logger.add_recipients(campaign_id, recipients_data)
            
            # Store campaign info in session state
            st.session_state.current_campaign = {
                'id': campaign_id,
                'subject': subject,
                'message': message,
                'template_type': template_type,
                'sender_name': sender_name,
                'rate_per_min': rate_per_min,
                'attachments': [att.name for att in attachments] if attachments else []
            }
            
            st.success(f"✅ Campaign saved! ID: {campaign_id}")
            st.info("Go to 'Send Campaign' page to start sending emails.")
            
        except Exception as e:
            st.markdown(f'<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Error saving campaign</div><p>{str(e)}</p></div>', unsafe_allow_html=True)

def show_send_campaign():
    """Show campaign sending page."""
    st.markdown('<div class="main-header"><h1>📤 Send Campaign</h1><p>Send your email campaign to all recipients</p></div>', unsafe_allow_html=True)
    
    if st.session_state.current_campaign is None:
        st.markdown('<div class="warning-card"><div class="metric-value">⚠️</div><div class="metric-label">No Campaign Ready</div><p>Please compose an email first!</p></div>', unsafe_allow_html=True)
        if st.button("✍️ Compose Email"):
            st.session_state.current_page = "✍️ Compose Email"
        return
    
    campaign = st.session_state.current_campaign
    
    # Campaign summary
    st.markdown('<div class="metric-card"><h3>📊 Campaign Summary</h3></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="info-card"><div class="metric-value">📧</div><div class="metric-label">{campaign["subject"]}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-card"><div class="metric-value">{campaign["template_type"].upper()}</div><div class="metric-label">Template Type</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="info-card"><div class="metric-value">👤</div><div class="metric-label">{campaign["sender_name"]}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-card"><div class="metric-value">{campaign["rate_per_min"]}/min</div><div class="metric-label">Rate Limit</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="success-card"><div class="metric-value">{len(st.session_state.recipients_df)}</div><div class="metric-label">Recipients</div></div>', unsafe_allow_html=True)
        if campaign['attachments']:
            st.markdown(f'<div class="info-card"><div class="metric-value">📎</div><div class="metric-label">{len(campaign["attachments"])} Attachments</div></div>', unsafe_allow_html=True)
    
    # Test send
    st.markdown('<div class="warning-card"><h3>🧪 Test Send</h3></div>', unsafe_allow_html=True)
    
    test_email = st.text_input("Test Email Address:", placeholder="Enter email for test send")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📧 Send Test Email"):
            if not test_email:
                st.markdown('<div class="warning-card"><div class="metric-value">⚠️</div><div class="metric-label">Please enter a test email address!</div></div>', unsafe_allow_html=True)
                return
            
            try:
                # Initialize mailer
                mailer = EmailMailer()
                mailer.set_rate_limit(campaign['rate_per_min'])
                
                # Send test email
                success, message = mailer.send_email(
                    test_email,
                    f"[TEST] {campaign['subject']}",
                    campaign['message'],
                    campaign['template_type'],
                    campaign['sender_name']
                )
                
                if success:
                    st.markdown('<div class="success-card"><div class="metric-value">✅</div><div class="metric-label">Test email sent successfully!</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="warning-card"><div class="metric-value">❌</div><div class="metric-label">Test email failed</div><p>{message}</p></div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.markdown(f'<div class="warning-card"><div class="metric-value">❌</div><div class="metric-label">Error sending test email</div><p>{str(e)}</p></div>', unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 Test SMTP Connection"):
            try:
                mailer = EmailMailer()
                success, message = mailer.test_connection()
                
                if success:
                    st.markdown('<div class="success-card"><div class="metric-value">✅</div><div class="metric-label">SMTP connection successful!</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="warning-card"><div class="metric-value">❌</div><div class="metric-label">SMTP connection failed</div><p>{message}</p></div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.markdown(f'<div class="warning-card"><div class="metric-value">❌</div><div class="metric-label">Error testing connection</div><p>{str(e)}</p></div>', unsafe_allow_html=True)
    
    # Send campaign
    st.markdown('<div class="metric-card"><h3>📤 Send Campaign</h3></div>', unsafe_allow_html=True)
    
    # Options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="info-card"><h4>⚙️ Send Options</h4></div>', unsafe_allow_html=True)
        continue_on_error = st.checkbox("Continue on error", value=True)
        max_retries = st.slider("Max retries", 1, 5, 3)
    
    with col2:
        st.markdown('<div class="info-card"><h4>📊 Batch Settings</h4></div>', unsafe_allow_html=True)
        batch_size = st.slider("Batch size", 10, 100, 50)
        delay_between_batches = st.number_input("Delay between batches (seconds)", 1, 60, 5)
    
    # Progress tracking
    if 'sending_progress' not in st.session_state:
        st.session_state.sending_progress = 0
    
    # Send button
    if st.button("🚀 Start Sending Campaign", type="primary"):
        if st.session_state.recipients_df is None:
            st.markdown('<div class="warning-card"><div class="metric-value">⚠️</div><div class="metric-label">No recipients to send to!</div></div>', unsafe_allow_html=True)
            return
        
        try:
            # Initialize components
            mailer = EmailMailer()
            mailer.set_rate_limit(campaign['rate_per_min'])
            
            # Prepare recipients
            recipients = []
            for _, row in st.session_state.recipients_df.iterrows():
                recipients.append({
                    'email': row['email_clean'],
                    'name': row.get('name', ''),
                    'company': row.get('company', '')
                })
            
            # Progress tracking with styled container
            st.markdown('<div class="progress-container"><h4>📊 Sending Progress</h4></div>', unsafe_allow_html=True)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Send in batches
            total_recipients = len(recipients)
            successful = 0
            failed = 0
            
            for i in range(0, total_recipients, batch_size):
                batch = recipients[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_recipients + batch_size - 1) // batch_size
                
                status_text.text(f"📤 Sending batch {batch_num}/{total_batches}...")
                
                # Send batch
                for j, recipient in enumerate(batch):
                    try:
                        success, message = mailer.send_email(
                            recipient['email'],
                            campaign['subject'],
                            campaign['message'],
                            campaign['template_type'],
                            campaign['sender_name']
                        )
                        
                        if success:
                            successful += 1
                        else:
                            failed += 1
                        
                        # Update progress
                        current_progress = (i + j + 1) / total_recipients
                        progress_bar.progress(current_progress)
                        
                        # Update status
                        status_text.text(f"📧 Sent: {successful}, ❌ Failed: {failed}, 📊 Progress: {current_progress:.1%}")
                        
                    except Exception as e:
                        failed += 1
                        st.markdown(f'<div class="warning-card"><div class="metric-value">❌</div><div class="metric-label">Error sending to {recipient["email"]}</div><p>{str(e)}</p></div>', unsafe_allow_html=True)
                
                # Delay between batches
                if i + batch_size < total_recipients:
                    time.sleep(delay_between_batches)
            
            # Final status
            progress_bar.progress(1.0)
            status_text.text(f"🎉 Campaign completed! Sent: {successful}, Failed: {failed}")
            
            st.markdown(f'<div class="success-card"><div class="metric-value">🎉</div><div class="metric-label">Campaign completed successfully!</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-card"><div class="metric-value">{(successful / total_recipients) * 100:.1f}%</div><div class="metric-label">Success Rate</div></div>', unsafe_allow_html=True)
            
            # Update campaign status in database
            logger = CampaignLogger()
            for recipient in recipients:
                if recipient['email'] in [r['email'] for r in recipients[:successful]]:
                    logger.update_recipient_status(campaign['id'], recipient['email'], 'sent')
                else:
                    logger.update_recipient_status(campaign['id'], recipient['email'], 'failed', 'Send error')
            
        except Exception as e:
            st.markdown(f'<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Error sending campaign</div><p>{str(e)}</p></div>', unsafe_allow_html=True)

def show_campaign_history():
    """Show campaign history and results."""
    st.markdown('<div class="main-header"><h1>📊 Campaign History</h1><p>View and manage your email campaigns</p></div>', unsafe_allow_html=True)
    
    try:
        logger = CampaignLogger()
        campaigns = logger.get_all_campaigns()
        
        if not campaigns:
            st.info("📭 No campaigns found. Start by creating your first campaign!")
            return
        
        # Campaign list
        st.header("All Campaigns")
        
        for campaign in campaigns:
            with st.expander(f"📧 {campaign['subject']} - {campaign['created_at']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Sender:** {campaign['sender_name']}")
                    st.write(f"**Type:** {campaign['template_type'].upper()}")
                    st.write(f"**Status:** {campaign['status']}")
                
                with col2:
                    st.write(f"**Total:** {campaign['total_recipients']}")
                    st.write(f"**Sent:** {campaign['sent_count']}")
                    st.write(f"**Failed:** {campaign['failed_count']}")
                
                with col3:
                    st.write(f"**Success Rate:** {campaign['success_rate']}%")
                    st.write(f"**Created:** {campaign['created_at']}")
                
                # Actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"📊 View Details", key=f"details_{campaign['id']}"):
                        show_campaign_details(campaign['id'])
                
                with col2:
                    if st.button(f"📥 Export Results", key=f"export_{campaign['id']}"):
                        export_campaign_results(campaign['id'])
                
                with col3:
                    if campaign['failed_count'] > 0:
                        if st.button(f"🔄 Retry Failed", key=f"retry_{campaign['id']}"):
                            retry_failed_emails(campaign['id'])
        
    except Exception as e:
        st.markdown(f'<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Error loading campaign history</div><p>{str(e)}</p></div>', unsafe_allow_html=True)

def show_campaign_details(campaign_id: int):
    """Show detailed campaign information."""
    try:
        logger = CampaignLogger()
        summary = logger.get_campaign_summary(campaign_id)
        
        if not summary:
            st.markdown('<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Campaign not found!</div></div>', unsafe_allow_html=True)
            return
        
        st.markdown(f'<div class="main-header"><h2>📊 Campaign Details - {summary["subject"]}</h2></div>', unsafe_allow_html=True)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Recipients", summary['total_recipients'])
        with col2:
            st.metric("Sent", summary['sent_count'])
        with col3:
            st.metric("Failed", summary['failed_count'])
        with col4:
            st.metric("Success Rate", f"{summary['success_rate']}%")
        
        # Failed recipients
        if summary['failed_count'] > 0:
            st.subheader("❌ Failed Recipients")
            failed_recipients = logger.get_failed_recipients(campaign_id)
            
            failed_df = pd.DataFrame(failed_recipients)
            st.dataframe(failed_df, use_container_width=True)
            
            # Download failed list
            csv = failed_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Failed List",
                data=csv,
                file_name=f"failed_recipients_campaign_{campaign_id}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"❌ Error loading campaign details: {e}")

def export_campaign_results(campaign_id: int):
    """Export campaign results to CSV."""
    try:
        logger = CampaignLogger()
        summary = logger.get_campaign_summary(campaign_id)
        
        if not summary:
            st.markdown('<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Campaign not found!</div></div>', unsafe_allow_html=True)
            return
        
        # Get all recipients for this campaign
        # This would require adding a method to get all recipients
        st.markdown('<div class="info-card"><div class="metric-value">📥</div><div class="metric-label">Export functionality would be implemented here</div></div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.markdown(f'<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Error exporting results</div><p>{str(e)}</p></div>', unsafe_allow_html=True)

def retry_failed_emails(campaign_id: int):
    """Retry sending to failed recipients."""
    try:
        logger = CampaignLogger()
        failed_recipients = logger.get_failed_recipients(campaign_id)
        
        if not failed_recipients:
            st.markdown('<div class="info-card"><div class="metric-value">📭</div><div class="metric-label">No failed recipients to retry!</div></div>', unsafe_allow_html=True)
            return
        
        st.markdown(f'<div class="info-card"><div class="metric-value">🔄</div><div class="metric-label">Retry functionality would be implemented here</div><p>For {len(failed_recipients)} failed recipients</p></div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.markdown(f'<div class="error-card"><div class="metric-value">❌</div><div class="metric-label">Error retrying failed emails</div><p>{str(e)}</p></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 