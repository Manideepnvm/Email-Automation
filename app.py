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

# Initialize session state
if 'current_campaign' not in st.session_state:
    st.session_state.current_campaign = None
if 'recipients_df' not in st.session_state:
    st.session_state.recipients_df = None
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}

def main():
    """Main application function."""
    
    # Sidebar
    st.sidebar.title("📧 Email Automation")
    
    # Check if credentials are configured
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        st.sidebar.error("⚠️ SMTP credentials not configured!")
        st.sidebar.info("Please copy env_example.txt to .env and add your SMTP credentials.")
        st.sidebar.code("cp env_example.txt .env")
        return
    
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard"
    
    # Navigation
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🏠 Dashboard", "📁 Upload & Validate", "✍️ Compose Email", "📤 Send Campaign", "📊 Campaign History"],
        index=["🏠 Dashboard", "📁 Upload & Validate", "✍️ Compose Email", "📤 Send Campaign", "📊 Campaign History"].index(st.session_state.current_page)
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
    st.title("🏠 Dashboard")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Welcome to Bulk Email Automation")
        st.write("""
        This tool helps you send personalized bulk emails with ease. Here's what you can do:
        
        - **Upload** CSV, Excel, or text files with email addresses
        - **Validate** and clean your email list
        - **Personalize** emails with templates and placeholders
        - **Send** campaigns with rate limiting and tracking
        - **Monitor** results and retry failed emails
        """)
        
        # Quick stats
        if st.session_state.recipients_df is not None:
            st.subheader("📊 Current Recipients")
            total = len(st.session_state.recipients_df)
            st.metric("Total Recipients", total)
            
            if 'is_valid' in st.session_state.recipients_df.columns:
                valid = st.session_state.recipients_df['is_valid'].sum()
                st.metric("Valid Emails", valid)
                st.metric("Invalid Emails", total - valid)
    
    with col2:
        st.subheader("🚀 Quick Actions")
        
        if st.button("📁 Upload New File"):
            st.session_state.current_page = "📁 Upload & Validate"
        
        if st.button("✍️ Compose Email"):
            st.session_state.current_page = "✍️ Compose Email"
        
        if st.button("📤 Send Campaign"):
            st.session_state.current_page = "📤 Send Campaign"
        
        # SMTP Status
        st.subheader("🔧 SMTP Status")
        try:
            mailer = EmailMailer()
            success, message = mailer.test_connection()
            if success:
                st.success("✅ Connected")
            else:
                st.error("❌ Connection Failed")
                st.caption(message)
        except Exception as e:
            st.error(f"❌ Configuration Error: {e}")

def show_upload_validate():
    """Show file upload and validation page."""
    st.title("📁 Upload & Validate")
    
    # File upload
    st.header("1. Upload File")
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
            
            st.success(f"✅ File uploaded successfully! Found {len(df)} rows and {len(columns)} columns.")
            
            # Show preview
            st.subheader("📋 File Preview")
            preview_df = FileParser.get_preview(df, 10)
            st.dataframe(preview_df, use_container_width=True)
            
            # Column selection
            st.header("2. Configure Columns")
            
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
                    st.header("3. Validation Results")
                    
                    summary = EmailValidator.get_validation_summary(df_deduped)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Emails", summary['total_emails'])
                    with col2:
                        st.metric("Valid Emails", summary['valid_emails'])
                    with col3:
                        st.metric("Invalid Emails", summary['invalid_emails'])
                    with col4:
                        st.metric("Success Rate", f"{summary['valid_percentage']}%")
                    
                    # Show validation details
                    if summary['invalid_emails'] > 0:
                        st.subheader("❌ Invalid Emails")
                        invalid_df = df_deduped[~df_deduped['is_valid']]
                        st.dataframe(invalid_df[['email_original', 'validation_error']], use_container_width=True)
                    
                    # Show valid emails
                    st.subheader("✅ Valid Emails")
                    st.dataframe(df_valid[['email_clean', 'name', 'company']].head(20), use_container_width=True)
                    
                    if len(df_valid) > 20:
                        st.caption(f"Showing first 20 of {len(df_valid)} valid emails")
                    
                    st.success(f"✅ Validation complete! {summary['valid_emails']} emails ready for sending.")
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
            os.unlink(tmp_file_path)

def show_compose_email():
    """Show email composition page."""
    st.title("✍️ Compose Email")
    
    if st.session_state.recipients_df is None:
        st.warning("⚠️ Please upload and validate a file first!")
        if st.button("📁 Go to Upload"):
            st.session_state.current_page = "📁 Upload & Validate"
        return
    
    # Email composition form
    st.header("Compose Your Email")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Basic email details
        sender_name = st.text_input("From Name:", value=settings.SENDER_NAME)
        subject = st.text_input("Subject:", placeholder="Enter email subject...")
        
        # Template type
        template_type = st.selectbox("Email Type:", ["plain", "html"])
        
        # Message content
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
        st.subheader("📊 Campaign Info")
        
        total_recipients = len(st.session_state.recipients_df)
        st.metric("Recipients", total_recipients)
        
        # Rate limiting
        st.subheader("⏱️ Rate Limiting")
        rate_per_min = st.slider("Emails per minute:", 10, 200, 60)
        
        # Estimate completion time
        rate_limiter = RateLimiter(rate_per_min)
        eta_minutes = rate_limiter.estimate_completion_time(total_recipients)
        st.metric("Estimated Time", f"{eta_minutes:.1f} min")
        
        # Attachments
        st.subheader("📎 Attachments")
        attachments = st.file_uploader(
            "Add attachments:",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx', 'txt', 'jpg', 'png']
        )
        
        if attachments:
            st.write(f"📎 {len(attachments)} file(s) selected")
    
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
            st.error(f"❌ Error saving campaign: {e}")

def show_send_campaign():
    """Show campaign sending page."""
    st.title("📤 Send Campaign")
    
    if st.session_state.current_campaign is None:
        st.warning("⚠️ No campaign ready to send!")
        if st.button("✍️ Compose Email"):
            st.session_state.current_page = "✍️ Compose Email"
        return
    
    campaign = st.session_state.current_campaign
    
    # Campaign summary
    st.header("Campaign Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Subject", campaign['subject'])
        st.metric("Template Type", campaign['template_type'].upper())
    with col2:
        st.metric("Sender", campaign['sender_name'])
        st.metric("Rate Limit", f"{campaign['rate_per_min']}/min")
    with col3:
        st.metric("Recipients", len(st.session_state.recipients_df))
        if campaign['attachments']:
            st.metric("Attachments", len(campaign['attachments']))
    
    # Test send
    st.header("🧪 Test Send")
    
    test_email = st.text_input("Test Email Address:", placeholder="Enter email for test send")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📧 Send Test Email"):
            if not test_email:
                st.error("Please enter a test email address!")
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
                    st.success("✅ Test email sent successfully!")
                else:
                    st.error(f"❌ Test email failed: {message}")
                    
            except Exception as e:
                st.error(f"❌ Error sending test email: {e}")
    
    with col2:
        if st.button("🔄 Test SMTP Connection"):
            try:
                mailer = EmailMailer()
                success, message = mailer.test_connection()
                
                if success:
                    st.success("✅ SMTP connection successful!")
                else:
                    st.error(f"❌ SMTP connection failed: {message}")
                    
            except Exception as e:
                st.error(f"❌ Error testing connection: {e}")
    
    # Send campaign
    st.header("📤 Send Campaign")
    
    # Options
    col1, col2 = st.columns(2)
    
    with col1:
        continue_on_error = st.checkbox("Continue on error", value=True)
        max_retries = st.slider("Max retries", 1, 5, 3)
    
    with col2:
        batch_size = st.slider("Batch size", 10, 100, 50)
        delay_between_batches = st.number_input("Delay between batches (seconds)", 1, 60, 5)
    
    # Progress tracking
    if 'sending_progress' not in st.session_state:
        st.session_state.sending_progress = 0
    
    # Send button
    if st.button("🚀 Start Sending Campaign", type="primary"):
        if not st.session_state.recipients_df is not None:
            st.error("No recipients to send to!")
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
            
            # Progress bar
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
                
                status_text.text(f"Sending batch {batch_num}/{total_batches}...")
                
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
                        status_text.text(f"Sent: {successful}, Failed: {failed}, Progress: {current_progress:.1%}")
                        
                    except Exception as e:
                        failed += 1
                        st.error(f"Error sending to {recipient['email']}: {e}")
                
                # Delay between batches
                if i + batch_size < total_recipients:
                    time.sleep(delay_between_batches)
            
            # Final status
            progress_bar.progress(1.0)
            status_text.text(f"Campaign completed! Sent: {successful}, Failed: {failed}")
            
            st.success(f"✅ Campaign completed successfully!")
            st.metric("Success Rate", f"{(successful / total_recipients) * 100:.1f}%")
            
            # Update campaign status in database
            logger = CampaignLogger()
            for recipient in recipients:
                if recipient['email'] in [r['email'] for r in recipients[:successful]]:
                    logger.update_recipient_status(campaign['id'], recipient['email'], 'sent')
                else:
                    logger.update_recipient_status(campaign['id'], recipient['email'], 'failed', 'Send error')
            
        except Exception as e:
            st.error(f"❌ Error sending campaign: {e}")

def show_campaign_history():
    """Show campaign history and results."""
    st.title("📊 Campaign History")
    
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
        st.error(f"❌ Error loading campaign history: {e}")

def show_campaign_details(campaign_id: int):
    """Show detailed campaign information."""
    try:
        logger = CampaignLogger()
        summary = logger.get_campaign_summary(campaign_id)
        
        if not summary:
            st.error("Campaign not found!")
            return
        
        st.subheader(f"Campaign Details - {summary['subject']}")
        
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
            st.error("Campaign not found!")
            return
        
        # Get all recipients for this campaign
        # This would require adding a method to get all recipients
        st.info("Export functionality would be implemented here")
        
    except Exception as e:
        st.error(f"❌ Error exporting results: {e}")

def retry_failed_emails(campaign_id: int):
    """Retry sending to failed recipients."""
    try:
        logger = CampaignLogger()
        failed_recipients = logger.get_failed_recipients(campaign_id)
        
        if not failed_recipients:
            st.info("No failed recipients to retry!")
            return
        
        st.info(f"Retry functionality would be implemented here for {len(failed_recipients)} failed recipients")
        
    except Exception as e:
        st.error(f"❌ Error retrying failed emails: {e}")

if __name__ == "__main__":
    main() 