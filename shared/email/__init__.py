"""
Shared Email Service Module

Provides unified email sending functionality for both mainweb and fmadmin.
"""

from .email_service import EmailService, create_email_service

__all__ = ['EmailService', 'create_email_service']
