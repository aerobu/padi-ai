"""
AWS SES client for sending transactional emails.
"""

import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.core.config import get_settings


class SESClient:
    """AWS SES email service client."""

    def __init__(self):
        aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY

        # Check if AWS credentials are configured
        self._is_configured = bool(aws_access_key_id and aws_secret_access_key)

        if not self._is_configured:
            # Skip initialization in local dev mode
            self.client = None
            return

        self.client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    async def send_consent_verification_email(
        self,
        to_email: str,
        verification_token: str,
        parent_name: str,
    ) -> bool:
        """Send COPPA consent verification email."""
        if not self._is_configured:
            print(
                f"[SES] Local dev mode: Skipping email to {to_email} "
                f"(token: {verification_token[:8]}...)"
            )
            return True  # Don't fail consent without email in dev mode

        try:
            verification_link = (
                f"https://padi-ai.com/consent/confirm"
                f"?token={verification_token}"
            )

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5281;">Confirm Your Parental Consent</h2>
                    <p>Hello {parent_name},</p>
                    <p>Thank you for registering with PADI.AI. To complete your parental consent
                    and activate your account, please click the link below:</p>

                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}"
                           style="background-color: #2c5281; color: white;
                                  padding: 12px 30px; text-decoration: none;
                                  border-radius: 5px; display: inline-block;">
                            Confirm Consent
                        </a>
                    </p>

                    <p style="color: #718096; font-size: 14px;">
                        This link expires in 48 hours.
                    </p>

                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                    <p style="color: #718096; font-size: 12px;">
                        PADI.AI Team<br>
                        Adaptive Math Learning for Oregon Students
                    </p>
                </div>
            </body>
            </html>
            """

            response = self.client.send_email(
                Source=settings.AWS_SES_FROM_EMAIL or "noreply@padi-ai.com",
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": "Confirm Parental Consent - PADI.AI"},
                    "Body": {"Html": {"Data": html_body}},
                },
            )

            print(f"[SES] Email sent to {to_email}, MessageId: {response['MessageId']}")
            return True

        except NoCredentialsError:
            print(f"[SES] No AWS credentials configured, skipping email to {to_email}")
            return True  # Don't fail in dev mode
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            print(
                f"[SES] Error sending to {to_email}: "
                f"{error_code} - {error_message}"
            )
            return False
        except Exception as e:
            print(f"[SES] Unexpected error sending to {to_email}: {e}")
            return False

    async def send_assessment_complete_email(
        self,
        to_email: str,
        parent_name: str,
        child_name: str,
        results_url: str,
    ) -> bool:
        """Send 'assessment complete' notification email."""
        if not self._is_configured:
            print(
                f"[SES] Local dev mode: Skipping email to {to_email} "
                f"(for {child_name})"
            )
            return True

        try:
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5281;">Diagnostic Assessment Complete</h2>
                    <p>Hello {parent_name},</p>
                    <p>{child_name}'s diagnostic assessment is complete!
                    Click below to view detailed results and recommendations.</p>

                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{results_url}"
                           style="background-color: #2c5281; color: white;
                                  padding: 12px 30px; text-decoration: none;
                                  border-radius: 5px; display: inline-block;">
                            View Results
                        </a>
                    </p>

                    <p style="color: #718096; font-size: 14px;">
                        The results will be available for 30 days.
                    </p>

                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                    <p style="color: #718096; font-size: 12px;">
                        PADI.AI Team<br>
                        Adaptive Math Learning for Oregon Students
                    </p>
                </div>
            </body>
            </html>
            """

            response = self.client.send_email(
                Source=settings.AWS_SES_FROM_EMAIL or "noreply@padi-ai.com",
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": f"Assessment Results Ready - {child_name}"},
                    "Body": {"Html": {"Data": html_body}},
                },
            )

            print(f"[SES] Email sent to {to_email}, MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            print(f"[SES] Error sending to {to_email}: {e}")
            return False
        except Exception as e:
            print(f"[SES] Unexpected error sending to {to_email}: {e}")
            return False

    def is_configured(self) -> bool:
        """Check if SES client is configured with AWS credentials."""
        return self._is_configured


# Get settings
settings = get_settings()


def get_ses_client() -> SESClient:
    """FastAPI dependency for SES client."""
    return SESClient()
