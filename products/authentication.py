# products/authentication.py

import jwt
import json
import requests
import logging
from jwt.algorithms import RSAAlgorithm
from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from django.conf import settings

logger = logging.getLogger(__name__)


class WSO2Authentication(authentication.BaseAuthentication):
    """
    Custom DRF Authentication class for WSO2 Identity Server JWT tokens.
    Uses manual JWKS fetching to support self-signed SSL certificates
    in local development.
    """

    def authenticate(self, request):
        # ── Step 1: Read Authorization header ──────────────────────────────────
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None  # No token — DRF will enforce permissions

        if not auth_header.startswith('Bearer '):
            return None  # Not a Bearer token — ignore

        token = auth_header.split(' ')[1].strip()

        if not token:
            raise exceptions.AuthenticationFailed(
                'Bearer token is empty.'
            )

        # ── Step 2: Validate the JWT ────────────────────────────────────────────
        decoded_token = self._validate_token(token)

        # ── Step 3: Get or create Django user ───────────────────────────────────
        username = decoded_token.get('sub', 'wso2user')
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': decoded_token.get('email', '')}
        )

        if created:
            logger.info(f"New Django user created for WSO2 subject: {username}")

        return (user, decoded_token)


    def _get_public_key(self, token):
        """
        Manually fetches WSO2 JWKS and finds the correct public key
        for this token. This approach lets us control SSL verification.
        """
        wso2_config  = settings.WSO2_CONFIG
        jwks_url     = wso2_config['JWKS_URL']
        verify_ssl   = wso2_config.get('VERIFY_SSL', False)

        try:
            # Fetch JWKS from WSO2 manually using requests
            # verify=False skips SSL check for self-signed cert (dev only)
            response = requests.get(
                jwks_url,
                verify=verify_ssl,      # False in dev, True/cert-path in production
                timeout=10              # don't wait more than 10 seconds
            )
            response.raise_for_status()
            jwks = response.json()

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to WSO2 JWKS at: {jwks_url}")
            raise exceptions.AuthenticationFailed(
                f'Cannot connect to WSO2 Identity Server at {jwks_url}. '
                f'Please make sure WSO2 IS is running.'
            )
        except requests.exceptions.Timeout:
            logger.error("WSO2 JWKS request timed out.")
            raise exceptions.AuthenticationFailed(
                'WSO2 Identity Server did not respond in time.'
            )
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL error connecting to WSO2: {str(e)}")
            raise exceptions.AuthenticationFailed(
                'SSL error connecting to WSO2. '
                'Set VERIFY_SSL to False in settings for local development.'
            )
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {str(e)}")
            raise exceptions.AuthenticationFailed(
                f'Failed to fetch WSO2 public keys: {str(e)}'
            )

        # ── Find the right key from JWKS using the token's 'kid' header ─────────
        #
        # A JWKS can contain multiple keys. Each JWT token has a 'kid'
        # (key ID) in its header that tells us which key was used to sign it.
        # We match the token's kid to the right key in the JWKS.
        #
        try:
            # Decode token header without verifying (just to get the 'kid')
            token_header = jwt.get_unverified_header(token)
            token_kid    = token_header.get('kid')

        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed(
                'Token is malformed — cannot read token header.'
            )

        # Search for the matching key in the JWKS
        for key_data in jwks.get('keys', []):
            if key_data.get('kid') == token_kid:
                # Convert JWK format → RSA public key object
                public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))
                return public_key

        # If no matching kid found, try the first key as fallback
        if jwks.get('keys'):
            logger.warning("No matching 'kid' found, using first key as fallback.")
            public_key = RSAAlgorithm.from_jwk(json.dumps(jwks['keys'][0]))
            return public_key

        raise exceptions.AuthenticationFailed(
            'No matching public key found in WSO2 JWKS.'
        )


    def _validate_token(self, token):
        """
        Validates the JWT token using the WSO2 public key.
        """
        wso2_config = settings.WSO2_CONFIG

        # Get the correct public key from WSO2 JWKS
        public_key = self._get_public_key(token)

        try:
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                issuer=wso2_config['ISSUER'],
                options={
                    "verify_aud": False,   # skip audience check
                    "verify_exp": True,    # always check expiry
                }
            )
            logger.info(f"Token valid for subject: {decoded.get('sub')}")
            return decoded

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed(
                'Access token has expired. Request a new token from WSO2.'
            )
        except jwt.InvalidIssuerError:
            raise exceptions.AuthenticationFailed(
                f'Token issuer is invalid. '
                f'Expected: {wso2_config["ISSUER"]}. '
                f'Tip: decode your token at https://jwt.io and check the "iss" field.'
            )
        except jwt.InvalidSignatureError:
            raise exceptions.AuthenticationFailed(
                'Token signature is invalid.'
            )
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed(
                'Token is malformed and cannot be decoded.'
            )
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(
                f'Token validation failed: {str(e)}'
            )