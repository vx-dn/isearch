"""AWS Cognito service implementation."""

import base64
import hashlib
import hmac
import logging
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CognitoService:
    """Service for AWS Cognito User Pool operations."""

    def __init__(
        self,
        user_pool_id: str,
        client_id: str,
        client_secret: Optional[str] = None,
        region: str = "ap-southeast-1",
    ):
        """Initialize Cognito service."""
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.client = boto3.client("cognito-idp", region_name=region)

    def _calculate_secret_hash(self, username: str) -> Optional[str]:
        """Calculate secret hash for Cognito client."""
        if not self.client_secret:
            return None

        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()

    async def sign_up(
        self,
        username: str,
        password: str,
        email: str,
        attributes: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Sign up a new user."""
        try:
            user_attributes = [{"Name": "email", "Value": email}]

            if attributes:
                for key, value in attributes.items():
                    user_attributes.append({"Name": key, "Value": value})

            params = {
                "ClientId": self.client_id,
                "Username": username,
                "Password": password,
                "UserAttributes": user_attributes,
            }

            secret_hash = self._calculate_secret_hash(username)
            if secret_hash:
                params["SecretHash"] = secret_hash

            response = self.client.sign_up(**params)
            logger.info(f"User {username} signed up successfully")
            return {
                "success": True,
                "user_sub": response.get("UserSub"),
                "confirmation_required": not response.get("UserConfirmed", False),
                "code_delivery_details": response.get("CodeDeliveryDetails"),
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Failed to sign up user {username}: {error_code} - {error_message}"
            )
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error during sign up: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def confirm_sign_up(
        self, username: str, confirmation_code: str
    ) -> dict[str, Any]:
        """Confirm user sign up with verification code."""
        try:
            params = {
                "ClientId": self.client_id,
                "Username": username,
                "ConfirmationCode": confirmation_code,
            }

            secret_hash = self._calculate_secret_hash(username)
            if secret_hash:
                params["SecretHash"] = secret_hash

            self.client.confirm_sign_up(**params)
            logger.info(f"User {username} confirmed successfully")
            return {"success": True}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Failed to confirm user {username}: {error_code} - {error_message}"
            )
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error during confirmation: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def initiate_auth(self, username: str, password: str) -> dict[str, Any]:
        """Initiate authentication for a user."""
        try:
            params = {
                "ClientId": self.client_id,
                "AuthFlow": "USER_PASSWORD_AUTH",
                "AuthParameters": {"USERNAME": username, "PASSWORD": password},
            }

            secret_hash = self._calculate_secret_hash(username)
            if secret_hash:
                params["AuthParameters"]["SECRET_HASH"] = secret_hash

            response = self.client.initiate_auth(**params)

            # Check if authentication is successful
            if "AuthenticationResult" in response:
                auth_result = response["AuthenticationResult"]
                logger.info(f"User {username} authenticated successfully")
                return {
                    "success": True,
                    "access_token": auth_result.get("AccessToken"),
                    "id_token": auth_result.get("IdToken"),
                    "refresh_token": auth_result.get("RefreshToken"),
                    "expires_in": auth_result.get("ExpiresIn"),
                    "token_type": auth_result.get("TokenType"),
                }

            # Handle challenges (MFA, password reset, etc.)
            elif "ChallengeName" in response:
                challenge_name = response["ChallengeName"]
                logger.info(
                    f"Authentication challenge for user {username}: {challenge_name}"
                )
                return {
                    "success": False,
                    "challenge_name": challenge_name,
                    "challenge_parameters": response.get("ChallengeParameters", {}),
                    "session": response.get("Session"),
                }

            else:
                logger.warning(
                    f"Unexpected authentication response for user {username}"
                )
                return {
                    "success": False,
                    "error_code": "UnexpectedResponse",
                    "error_message": "Unexpected authentication response",
                }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Failed to authenticate user {username}: {error_code} - {error_message}"
            )
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def refresh_token(self, refresh_token: str, username: str) -> dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            params = {
                "ClientId": self.client_id,
                "AuthFlow": "REFRESH_TOKEN_AUTH",
                "AuthParameters": {"REFRESH_TOKEN": refresh_token},
            }

            secret_hash = self._calculate_secret_hash(username)
            if secret_hash:
                params["AuthParameters"]["SECRET_HASH"] = secret_hash

            response = self.client.initiate_auth(**params)

            if "AuthenticationResult" in response:
                auth_result = response["AuthenticationResult"]
                logger.info(f"Token refreshed successfully for user {username}")
                return {
                    "success": True,
                    "access_token": auth_result.get("AccessToken"),
                    "id_token": auth_result.get("IdToken"),
                    "expires_in": auth_result.get("ExpiresIn"),
                    "token_type": auth_result.get("TokenType"),
                }

            return {
                "success": False,
                "error_code": "TokenRefreshFailed",
                "error_message": "Failed to refresh token",
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Failed to refresh token: {error_code} - {error_message}")
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def get_user(self, access_token: str) -> dict[str, Any]:
        """Get user information using access token."""
        try:
            response = self.client.get_user(AccessToken=access_token)

            # Parse user attributes
            user_attributes = {}
            for attr in response.get("UserAttributes", []):
                user_attributes[attr["Name"]] = attr["Value"]

            logger.debug(f"Retrieved user information for {response.get('Username')}")
            return {
                "success": True,
                "username": response.get("Username"),
                "user_status": response.get("UserStatus"),
                "attributes": user_attributes,
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Failed to get user: {error_code} - {error_message}")
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error getting user: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def update_user_attributes(
        self, access_token: str, attributes: dict[str, str]
    ) -> dict[str, Any]:
        """Update user attributes."""
        try:
            user_attributes = [
                {"Name": name, "Value": value} for name, value in attributes.items()
            ]

            response = self.client.update_user_attributes(
                UserAttributes=user_attributes, AccessToken=access_token
            )

            logger.info(f"Updated user attributes: {list(attributes.keys())}")
            return {
                "success": True,
                "code_delivery_details": response.get("CodeDeliveryDetailsList", []),
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Failed to update user attributes: {error_code} - {error_message}"
            )
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error updating user attributes: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def change_password(
        self, access_token: str, previous_password: str, proposed_password: str
    ) -> dict[str, Any]:
        """Change user password."""
        try:
            self.client.change_password(
                AccessToken=access_token,
                PreviousPassword=previous_password,
                ProposedPassword=proposed_password,
            )

            logger.info("Password changed successfully")
            return {"success": True}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Failed to change password: {error_code} - {error_message}")
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error changing password: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def forgot_password(self, username: str) -> dict[str, Any]:
        """Initiate forgot password flow."""
        try:
            params = {"ClientId": self.client_id, "Username": username}

            secret_hash = self._calculate_secret_hash(username)
            if secret_hash:
                params["SecretHash"] = secret_hash

            response = self.client.forgot_password(**params)

            logger.info(f"Forgot password initiated for user {username}")
            return {
                "success": True,
                "code_delivery_details": response.get("CodeDeliveryDetails"),
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Failed to initiate forgot password for {username}: {error_code} - {error_message}"
            )
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error during forgot password: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def confirm_forgot_password(
        self, username: str, confirmation_code: str, new_password: str
    ) -> dict[str, Any]:
        """Confirm forgot password with new password."""
        try:
            params = {
                "ClientId": self.client_id,
                "Username": username,
                "ConfirmationCode": confirmation_code,
                "Password": new_password,
            }

            secret_hash = self._calculate_secret_hash(username)
            if secret_hash:
                params["SecretHash"] = secret_hash

            self.client.confirm_forgot_password(**params)

            logger.info(f"Password reset confirmed for user {username}")
            return {"success": True}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Failed to confirm forgot password for {username}: {error_code} - {error_message}"
            )
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error confirming forgot password: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }

    async def global_sign_out(self, access_token: str) -> dict[str, Any]:
        """Sign out user from all devices."""
        try:
            self.client.global_sign_out(AccessToken=access_token)

            logger.info("User signed out globally")
            return {"success": True}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Failed to sign out globally: {error_code} - {error_message}")
            return {
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
            }
        except Exception as e:
            logger.error(f"Unexpected error during global sign out: {e}")
            return {
                "success": False,
                "error_code": "UnknownError",
                "error_message": str(e),
            }
