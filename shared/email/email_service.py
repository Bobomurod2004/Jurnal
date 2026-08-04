"""
Core Email Service

Unified email sending service for mainweb and fmadmin applications.
Supports:
- Multi-language emails (UZ, RU, EN)
- Email validation
- Retry mechanism
- Rate limiting
- Error handling with categorization
- Email delivery logging
"""

import logging
import re
import smtplib
import time
from email.message import EmailMessage
from email.utils import formataddr
from urllib.parse import urljoin
from functools import lru_cache

from shared.observability import record_email_delivery_metric

logger = logging.getLogger(__name__)

# Email validation regex
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Language configuration
TEMPLATE_LANGUAGES = ('uz', 'ru', 'en')
LANGUAGE_MARKER_PATTERN = re.compile(r'\[(UZ|RU|EN)\]\s*', re.IGNORECASE)
LANGUAGE_SECTION_ORDER = (
    ('uz', 'Uzbek'),
    ('ru', 'Russian'),
    ('en', 'English'),
)

# Global state for email logging table
EMAIL_LOG_TABLE_READY = False


class EmailService:
    """
    Unified email service for sending notifications.

    Features:
    - Email validation
    - Retry mechanism with exponential backoff
    - Rate limiting to prevent SMTP abuse
    - Multi-language support
    - Template loading from database
    - Delivery logging
    """

    def __init__(self, db_connector, settings, app_name='app'):
        """
        Initialize email service.

        Args:
            db_connector: Database connector instance (dbc or db)
            settings: Application settings module
            app_name: Application name ('mainweb' or 'fmadmin')
        """
        self.db = db_connector
        self.settings = settings
        self.app_name = app_name

        # Rate limiting configuration
        self.rate_limit_batch_size = getattr(
            settings, 'MAIL_RATE_LIMIT_BATCH_SIZE', 10
        )
        self.rate_limit_pause_seconds = getattr(
            settings, 'MAIL_RATE_LIMIT_PAUSE_SECONDS', 2
        )

        # Retry configuration
        self.max_retry_attempts = getattr(
            settings, 'MAIL_MAX_RETRY_ATTEMPTS', 3
        )

    # ========== EMAIL VALIDATION ==========

    def _validate_email(self, email):
        """
        Validate email address format.

        Args:
            email: Email address string

        Returns:
            tuple: (is_valid: bool, result: str or error_message: str)
        """
        email = email.strip().lower()

        # Check basic format
        if not EMAIL_REGEX.match(email):
            return False, "Invalid email format"

        # Split local and domain parts
        try:
            local, domain = email.rsplit('@', 1)
        except ValueError:
            return False, "Invalid email format"

        # Validate local part length (max 64 chars)
        if len(local) > 64:
            return False, "Local part too long (max 64 characters)"

        # Validate domain length (max 253 chars)
        if len(domain) > 253:
            return False, "Domain too long (max 253 characters)"

        # Check for consecutive dots
        if '..' in email:
            return False, "Consecutive dots not allowed"

        return True, email

    def _normalize_recipients(self, recipients):
        """
        Normalize and validate recipient email addresses.

        Args:
            recipients: String (comma-separated) or list of email addresses

        Returns:
            list: Valid email addresses
        """
        if not recipients:
            return []

        # Convert to list if string
        if isinstance(recipients, str):
            raw_items = [r.strip() for r in recipients.split(',') if r.strip()]
        else:
            raw_items = recipients

        normalized = []
        invalid = []
        seen = set()

        for item in raw_items:
            is_valid, result = self._validate_email(item)

            if is_valid:
                # Avoid duplicates
                if result not in seen:
                    seen.add(result)
                    normalized.append(result)
            else:
                invalid.append((item, result))

        # Log invalid emails
        if invalid:
            logger.warning(
                f"Invalid emails skipped: {', '.join([f'{e}({r})' for e, r in invalid])}"
            )

        return normalized

    # ========== UTILITY FUNCTIONS ==========

    def _clean_text(self, value):
        """Clean and normalize text value."""
        if value is None:
            return ''
        return str(value).strip()

    def _normalize_details(self, details):
        """Normalize detail rows (label-value pairs)."""
        rows = []
        for label, value in details or []:
            label_text = self._clean_text(label)
            value_text = self._clean_text(value)
            if label_text and value_text:
                rows.append({'label': label_text, 'value': value_text})
        return rows

    def _normalize_body_lines(self, lines):
        """Normalize body text lines."""
        rows = []
        for line in lines or []:
            value = self._clean_text(line)
            if value:
                rows.append(value)
        return rows

    def _absolute_url(self, path):
        """Convert relative path to absolute URL."""
        base_url = (self.settings.APP_BASE_URL or '').rstrip('/') + '/'
        value = self._clean_text(path)

        if not value:
            return self.settings.APP_BASE_URL

        if value.startswith('http://') or value.startswith('https://'):
            return value

        return urljoin(base_url, value.lstrip('/'))

    # ========== ERROR HANDLING ==========

    def _categorize_smtp_error(self, exception):
        """
        Categorize SMTP exception for better error handling.

        Args:
            exception: Exception object

        Returns:
            tuple: (error_code: str, error_message: str, is_retryable: bool)
        """
        if isinstance(exception, smtplib.SMTPAuthenticationError):
            return 'auth_failed', 'SMTP authentication failed', False

        elif isinstance(exception, smtplib.SMTPServerDisconnected):
            return 'disconnected', 'SMTP server disconnected', True

        elif isinstance(exception, smtplib.SMTPRecipientsRefused):
            return 'recipient_refused', 'Recipient email rejected', False

        elif isinstance(exception, smtplib.SMTPSenderRefused):
            return 'sender_refused', 'Sender email rejected', False

        elif isinstance(exception, smtplib.SMTPDataError):
            return 'data_error', 'SMTP data transmission error', True

        elif isinstance(exception, (ConnectionError, TimeoutError)):
            return 'network_error', 'Network connection failed', True

        elif isinstance(exception, OSError):
            return 'os_error', f'OS error: {str(exception)}', True

        else:
            return 'unknown', str(exception), False

    # ========== SMTP CONNECTION ==========

    def _open_connection(self):
        """
        Open SMTP connection.

        Returns:
            SMTP client object

        Raises:
            RuntimeError: If MAIL_HOST is not configured
        """
        host = self._clean_text(self.settings.MAIL_HOST)
        if not host:
            raise RuntimeError('MAIL_HOST is not configured')

        # Create SMTP client
        if self.settings.MAIL_USE_SSL:
            client = smtplib.SMTP_SSL(
                host,
                self.settings.MAIL_PORT,
                timeout=self.settings.MAIL_TIMEOUT,
            )
        else:
            client = smtplib.SMTP(
                host,
                self.settings.MAIL_PORT,
                timeout=self.settings.MAIL_TIMEOUT,
            )
            client.ehlo()

            if self.settings.MAIL_USE_TLS:
                client.starttls()
                client.ehlo()

        # Authenticate if credentials provided
        if self.settings.MAIL_USERNAME:
            try:
                client.login(
                    self.settings.MAIL_USERNAME,
                    self.settings.MAIL_PASSWORD
                )
            except smtplib.SMTPAuthenticationError:
                # Retrying cannot fix rejected credentials, so name the
                # settings to check instead of leaving a bare 535 in the log.
                # The caller never receives the client here, which means only
                # this branch can close the socket it already opened.
                logger.error(
                    "SMTP authentication failed for user=%s at %s:%s -- check "
                    "MAIL_USERNAME/MAIL_PASSWORD and whether this port needs "
                    "MAIL_USE_TLS or MAIL_USE_SSL",
                    self.settings.MAIL_USERNAME,
                    host,
                    self.settings.MAIL_PORT,
                )
                try:
                    client.close()
                except Exception:
                    pass
                raise

        return client

    # ========== RETRY MECHANISM ==========

    def _send_with_retry(self, client, message, recipient):
        """
        Send email with retry mechanism.

        Args:
            client: SMTP client
            message: EmailMessage object
            recipient: Recipient email address

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                client.send_message(message)
                return True, None

            except Exception as e:
                error_code, error_msg, is_retryable = self._categorize_smtp_error(e)

                # If not retryable or last attempt, fail
                if not is_retryable or attempt >= self.max_retry_attempts:
                    logger.error(
                        f"Email send failed to {recipient}: {error_code} - {error_msg} "
                        f"(attempt {attempt}/{self.max_retry_attempts})"
                    )
                    return False, f"{error_code}: {error_msg}"

                # Calculate wait time with exponential backoff
                wait_time = 2 ** attempt  # 2, 4, 8 seconds

                logger.warning(
                    f"Retryable error for {recipient}: {error_code}, "
                    f"retrying in {wait_time}s (attempt {attempt}/{self.max_retry_attempts})"
                )

                time.sleep(wait_time)

        return False, "Max retry attempts reached"

    # ========== EMAIL LOGGING ==========

    def _ensure_email_delivery_logs_table(self):
        """
        Ensure email_delivery_logs table exists.

        Returns:
            bool: True if table exists or was created successfully
        """
        global EMAIL_LOG_TABLE_READY

        if EMAIL_LOG_TABLE_READY:
            return True

        conn = getattr(self.db, 'conn', None)
        if conn is None:
            return False

        cursor = None
        try:
            cursor = conn.cursor()

            # Create table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS email_delivery_logs (
                    id SERIAL PRIMARY KEY,
                    app TEXT NOT NULL,
                    recipient_email TEXT,
                    subject TEXT,
                    status TEXT NOT NULL,
                    template_alias TEXT,
                    error_text TEXT,
                    created_at BIGINT NOT NULL DEFAULT EXTRACT(epoch FROM now())
                );
                """
            )

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_delivery_logs_created_at "
                "ON email_delivery_logs(created_at DESC, id DESC);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_delivery_logs_status "
                "ON email_delivery_logs(status);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_delivery_logs_recipient "
                "ON email_delivery_logs(recipient_email);"
            )

            conn.commit()
            EMAIL_LOG_TABLE_READY = True
            return True

        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.exception(f"Failed to ensure email_delivery_logs table in {self.app_name}")
            return False

        finally:
            if cursor is not None:
                cursor.close()

    def _log_email_delivery(
        self,
        status,
        subject,
        recipients=None,
        template_alias=None,
        error_text=None
    ):
        """
        Log email delivery attempt.

        Args:
            status: Delivery status (sent, failed, skipped_*)
            subject: Email subject
            recipients: List of recipient email addresses
            template_alias: Template alias used (if any)
            error_text: Error message (if failed)

        Returns:
            bool: True if logged successfully
        """
        if not self._ensure_email_delivery_logs_table():
            return False

        conn = getattr(self.db, 'conn', None)
        if conn is None:
            return False

        # Normalize recipients
        rows = self._normalize_recipients(recipients) if recipients else [None]
        if not rows:
            rows = [None]

        normalized_status = self._clean_text(status).lower() or 'unknown'
        normalized_subject = self._clean_text(subject)
        normalized_template_alias = self._clean_text(template_alias) or None
        normalized_error_text = self._clean_text(error_text) or None
        now_ts = int(time.time())

        cursor = None
        try:
            cursor = conn.cursor()

            for recipient in rows:
                cursor.execute(
                    """
                    INSERT INTO email_delivery_logs (
                        app,
                        recipient_email,
                        subject,
                        status,
                        template_alias,
                        error_text,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.app_name,
                        recipient,
                        normalized_subject,
                        normalized_status,
                        normalized_template_alias,
                        normalized_error_text,
                        now_ts,
                    ),
                )

            conn.commit()
            record_email_delivery_metric(self.app_name, normalized_status)
            return True

        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.exception(
                f"Failed to log email delivery: status={normalized_status}, "
                f"subject={normalized_subject}"
            )
            return False

        finally:
            if cursor is not None:
                cursor.close()

    # ========== MULTI-LANGUAGE SUPPORT ==========

    def _extract_multilingual_map(self, raw_text, separators=(' | ',)):
        """
        Extract multi-language content from text.

        Supports two formats:
        1. Markers: "[UZ] text [RU] text [EN] text"
        2. Separators: "uz text | ru text | en text"

        Args:
            raw_text: Text to parse
            separators: List of separator strings

        Returns:
            tuple: (language_map: dict, common_text: str)
        """
        text = self._clean_text(raw_text)
        if not text:
            return {}, ''

        # Try marker format first
        matches = list(LANGUAGE_MARKER_PATTERN.finditer(text))
        if matches:
            language_map = {}
            for index, match in enumerate(matches):
                language_code = match.group(1).lower()
                start_index = match.end()
                end_index = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                segment = text[start_index:end_index].strip(" \t\r\n|/-")
                if segment:
                    language_map[language_code] = segment

            if language_map:
                return language_map, ''

        # Try separator format
        for separator in separators:
            if separator not in text:
                continue

            parts = [part.strip() for part in text.split(separator) if part.strip()]

            if len(parts) == len(LANGUAGE_SECTION_ORDER):
                return {
                    language_code: parts[index]
                    for index, (language_code, _label) in enumerate(LANGUAGE_SECTION_ORDER)
                }, ''

        # No multi-language format found
        return {}, text

    def _first_nonempty(self, values):
        """Get first non-empty value from list."""
        for value in values or []:
            text = self._clean_text(value)
            if text:
                return text
        return ''

    def _new_language_section(self, language_code, label):
        """Create new language section structure."""
        return {
            'code': language_code,
            'label': label,
            'subject': '',
            'intro': '',
            'details': [],
            'body_lines': [],
            'cta_label': '',
        }

    def _append_unique_detail(self, section, label, value):
        """Add unique detail to section."""
        label_text = self._clean_text(label)
        value_text = self._clean_text(value)
        if not label_text or not value_text:
            return

        detail_row = {'label': label_text, 'value': value_text}
        if detail_row not in section['details']:
            section['details'].append(detail_row)

    def _append_unique_body_line(self, section, line):
        """Add unique body line to section."""
        line_text = self._clean_text(line)
        if not line_text:
            return

        if line_text not in section['body_lines']:
            section['body_lines'].append(line_text)

    def _has_section_content(self, section):
        """Check if section has any content."""
        return bool(
            self._clean_text(section.get('subject'))
            or self._clean_text(section.get('intro'))
            or self._clean_text(section.get('cta_label'))
            or section.get('details')
            or section.get('body_lines')
        )

    def _build_language_sections(self, subject, intro, details, body_lines, cta_label):
        """
        Build multi-language sections for email.

        Args:
            subject: Subject text (can be multi-language)
            intro: Intro text (can be multi-language)
            details: List of (label, value) tuples
            body_lines: List of body text lines
            cta_label: CTA button label

        Returns:
            list: List of language section dicts
        """
        # Initialize sections for each language
        sections = {
            language_code: self._new_language_section(language_code, label)
            for language_code, label in LANGUAGE_SECTION_ORDER
        }

        common_content = {
            'subject': '',
            'intro': '',
            'cta_label': '',
            'details': [],
            'body_lines': [],
        }

        # Extract multi-language content
        subject_map, common_subject = self._extract_multilingual_map(subject)
        intro_map, common_intro = self._extract_multilingual_map(intro)
        cta_map, common_cta = self._extract_multilingual_map(
            cta_label,
            separators=(' / ', ' | ')
        )

        # Assign language-specific content
        for language_code, section in sections.items():
            section['subject'] = self._clean_text(subject_map.get(language_code))
            section['intro'] = self._clean_text(intro_map.get(language_code))
            section['cta_label'] = self._clean_text(cta_map.get(language_code))

        # Assign common content
        common_content['subject'] = self._clean_text(common_subject)
        common_content['intro'] = self._clean_text(common_intro)
        common_content['cta_label'] = self._clean_text(common_cta)

        # Process details
        for item in details or []:
            label_map, common_label = self._extract_multilingual_map(
                item.get('label'),
                separators=(' / ', ' | '),
            )
            value_map, common_value = self._extract_multilingual_map(
                item.get('value'),
                separators=(' / ', ' | '),
            )

            if label_map or value_map:
                # Multi-language detail
                for language_code, section in sections.items():
                    fallback_label = common_label or self._first_nonempty(label_map.values())
                    fallback_value = common_value or self._first_nonempty(value_map.values())
                    resolved_label = label_map.get(language_code) or fallback_label
                    resolved_value = value_map.get(language_code) or fallback_value
                    self._append_unique_detail(section, resolved_label, resolved_value)
            else:
                # Common detail
                self._append_unique_detail(common_content, common_label, common_value)

        # Process body lines
        active_language = None

        for line in body_lines or []:
            line_text = self._clean_text(line)
            if not line_text:
                continue

            # Check for language marker
            marker_match = re.fullmatch(r'\[(UZ|RU|EN)\]', line_text, re.IGNORECASE)
            if marker_match:
                active_language = marker_match.group(1).lower()
                continue

            # Extract multi-language from line
            line_map, common_line = self._extract_multilingual_map(line_text)

            if line_map:
                # Multi-language line
                for language_code, value in line_map.items():
                    self._append_unique_body_line(sections[language_code], value)
                active_language = None
                continue

            # Single language or common line
            if active_language in sections:
                self._append_unique_body_line(
                    sections[active_language],
                    common_line or line_text
                )
            else:
                self._append_unique_body_line(
                    common_content,
                    common_line or line_text
                )

        # Merge common content into sections
        for language_code, section in sections.items():
            if common_content['subject'] and not section['subject']:
                section['subject'] = common_content['subject']
            if common_content['intro'] and not section['intro']:
                section['intro'] = common_content['intro']
            if common_content['cta_label'] and not section['cta_label']:
                section['cta_label'] = common_content['cta_label']

            for detail_row in common_content['details']:
                self._append_unique_detail(
                    section,
                    detail_row.get('label'),
                    detail_row.get('value')
                )

            for line_text in common_content['body_lines']:
                self._append_unique_body_line(section, line_text)

        # Return only sections with content
        active_sections = [
            sections[language_code]
            for language_code, _label in LANGUAGE_SECTION_ORDER
            if self._has_section_content(sections[language_code])
        ]

        return active_sections

    def _build_context(
        self,
        subject,
        intro,
        details=None,
        body_lines=None,
        cta_url=None,
        cta_label=None,
    ):
        """Build email template context with multi-language support."""
        normalized_subject = self._clean_text(subject)
        normalized_intro = self._clean_text(intro)
        normalized_details = self._normalize_details(details)
        normalized_body_lines = self._normalize_body_lines(body_lines)
        normalized_cta_label = self._clean_text(cta_label) or 'Open'

        # Build language sections
        language_sections = self._build_language_sections(
            normalized_subject,
            normalized_intro,
            normalized_details,
            normalized_body_lines,
            normalized_cta_label,
        )

        is_multilingual = len(language_sections) > 1

        # Determine headline subject
        headline_subject = normalized_subject
        if is_multilingual:
            for section in language_sections:
                section_subject = self._clean_text(section.get('subject'))
                if section_subject:
                    headline_subject = section_subject
                    break

        return {
            'subject': normalized_subject,
            'headline_subject': headline_subject,
            'intro': normalized_intro,
            'details': normalized_details,
            'body_lines': normalized_body_lines,
            'is_multilingual': is_multilingual,
            'language_sections': language_sections,
            'cta_url': self._absolute_url(cta_url) if cta_url else '',
            'cta_label': normalized_cta_label,
            'signature_name': self.settings.MAIL_FROM_NAME,
            'app_base_url': self.settings.APP_BASE_URL,
        }

    def _render_email_template(self, template_name, context, jinja_env):
        """Render email template using Jinja2."""
        template = jinja_env.get_or_select_template(template_name)
        return template.render(**context)

    # ========== MAIN SEND FUNCTION ==========

    def send_notification_email(
        self,
        recipients,
        subject,
        intro,
        details=None,
        body_lines=None,
        cta_url=None,
        cta_label=None,
        reply_to=None,
        fail_silently=True,
        template_alias=None,
        jinja_env=None,
    ):
        """
        Send notification email.

        Args:
            recipients: Email address(es) - string or list
            subject: Email subject
            intro: Introduction text
            details: List of (label, value) tuples
            body_lines: List of body text lines
            cta_url: Call-to-action button URL
            cta_label: Call-to-action button text
            reply_to: Reply-to email address
            fail_silently: If True, don't raise exceptions
            template_alias: Template alias for DB templates
            jinja_env: Jinja2 environment (required for rendering)

        Returns:
            bool: True if sent successfully
        """
        # Validate and normalize recipients
        normalized_recipients = self._normalize_recipients(recipients)

        if not normalized_recipients:
            logger.warning(f"No valid recipients for email: {subject}")
            self._log_email_delivery(
                status='skipped_no_recipient',
                subject=subject,
                recipients=[],
                template_alias=template_alias,
            )
            return False

        # Check if email is enabled
        if not self.settings.MAIL_ENABLED:
            logger.info(f"Email delivery disabled, skipped: {subject}")
            self._log_email_delivery(
                status='skipped_mail_disabled',
                subject=subject,
                recipients=normalized_recipients,
                template_alias=template_alias,
            )
            return False

        # Build email context
        context = self._build_context(
            subject=subject,
            intro=intro,
            details=details,
            body_lines=body_lines,
            cta_url=cta_url,
            cta_label=cta_label,
        )

        # Render email templates
        try:
            if jinja_env is None:
                raise RuntimeError("jinja_env is required for email rendering")

            text_body = self._render_email_template(
                'emails/generic_notification.txt',
                context,
                jinja_env
            )
            html_body = self._render_email_template(
                'emails/generic_notification.html',
                context,
                jinja_env
            )

            # Check if sending is suppressed
            if self.settings.MAIL_SUPPRESS_SEND:
                logger.info(
                    f"MAIL_SUPPRESS_SEND enabled, skipped: {subject} "
                    f"to {', '.join(normalized_recipients)}"
                )
                self._log_email_delivery(
                    status='skipped_suppressed',
                    subject=subject,
                    recipients=normalized_recipients,
                    template_alias=template_alias,
                )
                return True

            # Send emails with rate limiting
            with self._open_connection() as client:
                sent_count = 0
                failed_recipients = []

                for index, recipient in enumerate(normalized_recipients):
                    # Build message
                    message = EmailMessage()
                    message['Subject'] = self._clean_text(subject)
                    message['From'] = formataddr((
                        self.settings.MAIL_FROM_NAME,
                        self.settings.MAIL_FROM_EMAIL
                    ))
                    message['To'] = recipient

                    if reply_to or self.settings.MAIL_REPLY_TO:
                        message['Reply-To'] = self._clean_text(
                            reply_to or self.settings.MAIL_REPLY_TO
                        )

                    message.set_content(text_body)
                    message.add_alternative(html_body, subtype='html')

                    # Send with retry
                    success, error_msg = self._send_with_retry(client, message, recipient)

                    if success:
                        sent_count += 1
                        logger.info(f"Email sent successfully to {recipient}")
                    else:
                        failed_recipients.append((recipient, error_msg))
                        logger.error(f"Failed to send email to {recipient}: {error_msg}")

                    # Rate limiting
                    if (index + 1) % self.rate_limit_batch_size == 0:
                        remaining = len(normalized_recipients) - (index + 1)
                        if remaining > 0:
                            logger.info(
                                f"Rate limit: sent {index + 1} emails, "
                                f"pausing {self.rate_limit_pause_seconds}s "
                                f"({remaining} remaining)"
                            )
                            time.sleep(self.rate_limit_pause_seconds)

            # Log results
            if sent_count > 0:
                self._log_email_delivery(
                    status='sent',
                    subject=subject,
                    recipients=[r for r in normalized_recipients
                               if r not in [f[0] for f in failed_recipients]],
                    template_alias=template_alias,
                )

            if failed_recipients:
                for recipient, error_msg in failed_recipients:
                    self._log_email_delivery(
                        status='failed',
                        subject=subject,
                        recipients=[recipient],
                        template_alias=template_alias,
                        error_text=error_msg,
                    )

            # Return True if at least one email was sent
            return sent_count > 0

        except Exception as exc:
            logger.exception(f"Failed to send email: {subject}")
            self._log_email_delivery(
                status='failed',
                subject=subject,
                recipients=normalized_recipients,
                template_alias=template_alias,
                error_text=str(exc),
            )

            if fail_silently:
                return False
            raise


# ========== HELPER FUNCTION ==========

def create_email_service(db_connector, settings, app_name='app'):
    """
    Factory function to create EmailService instance.

    Args:
        db_connector: Database connector
        settings: Application settings module
        app_name: Application name

    Returns:
        EmailService instance
    """
    return EmailService(db_connector, settings, app_name)
