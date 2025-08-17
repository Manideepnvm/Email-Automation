from jinja2 import Template
from typing import Dict, List

class EmailTemplates:
    """Default email templates with Jinja2 placeholders."""
    
    # Default plain text template
    DEFAULT_PLAIN_TEMPLATE = """Hello {{name|default('there')}},

{{message}}

{% if company %}
Company: {{company}}
{% endif %}

Best regards,
{{sender_name}}

---
To unsubscribe, reply with "UNSUBSCRIBE" in the subject line."""

    # Default HTML template
    DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{subject|default('Email')}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
        .content { padding: 20px 0; }
        .footer { background-color: #f8f9fa; padding: 20px; border-radius: 5px; font-size: 12px; color: #666; }
        .unsubscribe { color: #dc3545; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Hello {{name|default('there')}}!</h2>
        </div>
        
        <div class="content">
            {{message|safe}}
            
            {% if company %}
            <p><strong>Company:</strong> {{company}}</p>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>Best regards,<br>
            <strong>{{sender_name}}</strong></p>
            
            <hr>
            <p style="font-size: 11px; color: #999;">
                To unsubscribe, reply with "UNSUBSCRIBE" in the subject line.
            </p>
        </div>
    </div>
</body>
</html>"""

    @staticmethod
    def get_default_template(template_type: str = 'plain') -> str:
        """
        Get default template by type.
        
        Args:
            template_type: 'plain' or 'html'
            
        Returns:
            Template string
        """
        if template_type.lower() == 'html':
            return EmailTemplates.DEFAULT_HTML_TEMPLATE
        else:
            return EmailTemplates.DEFAULT_PLAIN_TEMPLATE
    
    @staticmethod
    def render_template(template_text: str, data: Dict) -> str:
        """
        Render template with data using Jinja2.
        
        Args:
            template_text: Template string
            data: Dictionary of data to insert
            
        Returns:
            Rendered template
        """
        try:
            template = Template(template_text)
            return template.render(**data)
        except Exception as e:
            raise ValueError(f"Error rendering template: {e}")
    
    @staticmethod
    def get_available_placeholders() -> List[str]:
        """
        Get list of available placeholders.
        
        Returns:
            List of placeholder names
        """
        return [
            '{{name}}',
            '{{company}}',
            '{{email}}',
            '{{sender_name}}',
            '{{subject}}',
            '{{message}}'
        ]
    
    @staticmethod
    def get_placeholder_help() -> Dict[str, str]:
        """
        Get help text for each placeholder.
        
        Returns:
            Dictionary mapping placeholders to descriptions
        """
        return {
            '{{name}}': 'Recipient\'s name (falls back to "there" if not provided)',
            '{{company}}': 'Recipient\'s company name (optional)',
            '{{email}}': 'Recipient\'s email address',
            '{{sender_name}}': 'Your name as the sender',
            '{{subject}}': 'Email subject line',
            '{{message}}': 'Main email content'
        }
    
    @staticmethod
    def validate_template(template_text: str) -> bool:
        """
        Validate template syntax.
        
        Args:
            template_text: Template string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            Template(template_text)
            return True
        except Exception:
            return False 