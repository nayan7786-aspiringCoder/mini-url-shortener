"""
Core business logic for URL validation, code generation, and alias management.
Uses strictly the Python standard library.
"""

import re
import secrets
import string
from urllib.parse import urlparse
from typing import Optional, Tuple, Dict, Any, List
from storage import Storage

BASE62_ALPHABET = string.digits + string.ascii_letters
DEFAULT_CODE_LENGTH = 6
RESERVED_WORDS = {"shorten", "resolve", "list", "stats", "delete", "help", "api", "admin"}


def validate_and_normalize_url(url: str) -> Tuple[bool, str, str]:
    """
    Validates and normalizes a URL.
    Returns: (is_valid, normalized_url, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "", "URL cannot be empty."

    url = url.strip()

    # If scheme is missing, default to https://
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, "", f"Invalid URL structure: {e}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, "", f"Unsupported protocol '{parsed.scheme}'. Only http and https are supported."

    netloc = parsed.netloc
    if not netloc:
        return False, "", "URL must contain a valid domain (e.g., example.com)."

    # Domain check: netloc can contain port e.g. localhost:8000
    host = netloc.split(":")[0].strip()
    if not host:
        return False, "", "Invalid host in URL."

    # Allow localhost or valid domain names (at least one dot for domains)
    if host.lower() != "localhost":
        # Check basic domain pattern
        domain_pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        if not re.match(domain_pattern, host):
            # Check IPv4
            ipv4_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
            if not re.match(ipv4_pattern, host):
                return False, "", f"Invalid domain name: '{host}'."

    return True, url, ""


def validate_alias(alias: str) -> Tuple[bool, str]:
    """
    Validates custom alias format and reserved names.
    Returns: (is_valid, error_message)
    """
    if not alias:
        return False, "Alias cannot be empty."

    alias = alias.strip()
    if len(alias) < 2:
        return False, "Alias must be at least 2 characters long."
    if len(alias) > 30:
        return False, "Alias cannot exceed 30 characters."

    if not re.match(r"^[a-zA-Z0-9_-]+$", alias):
        return False, "Alias can only contain letters, numbers, hyphens (-), and underscores (_)."

    if alias.lower() in RESERVED_WORDS:
        return False, f"'{alias}' is a reserved keyword and cannot be used as an alias."

    return True, ""


class URLShortenerService:
    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage if storage is not None else Storage()

    def generate_short_code(self, length: int = DEFAULT_CODE_LENGTH) -> str:
        """Generates a random unique Base62 short code."""
        for _ in range(10):
            code = "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))
            if not self.storage.code_exists(code) and code.lower() not in RESERVED_WORDS:
                return code
        raise RuntimeError("Failed to generate a unique short code after 10 attempts.")

    def shorten(self, url: str, custom_alias: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
        """
        Shortens a URL.
        Returns: (success, code, message)
        """
        is_valid, norm_url, err = validate_and_normalize_url(url)
        if not is_valid:
            return False, None, err

        if custom_alias:
            alias = custom_alias.strip()
            alias_valid, alias_err = validate_alias(alias)
            if not alias_valid:
                return False, None, alias_err

            if self.storage.code_exists(alias):
                return False, None, f"Alias '{alias}' is already in use. Please choose another alias."

            code = alias
        else:
            # Check if this exact URL was already shortened
            existing = self.storage.find_by_url(norm_url)
            if existing:
                return True, existing["code"], f"URL already shortened previously. Short code: {existing['code']}"

            code = self.generate_short_code()

        success = self.storage.save_url(code, norm_url)
        if not success:
            return False, None, f"Failed to save short code '{code}'. It might already exist."

        return True, code, f"Successfully shortened to '{code}'."

    def resolve(self, code: str, increment_clicks: bool = True) -> Tuple[bool, Optional[str], str]:
        """
        Resolves a short code to its original URL.
        Returns: (success, original_url, message)
        """
        if not code:
            return False, None, "Code cannot be empty."

        code = code.strip()
        original_url = self.storage.get_url(code, increment_clicks=increment_clicks)
        if not original_url:
            return False, None, f"Short code '{code}' not found."

        return True, original_url, "Code resolved successfully."

    def get_stats(self, code: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Retrieves usage statistics for a short code.
        Returns: (success, stats_dict, message)
        """
        if not code:
            return False, None, "Code cannot be empty."

        code = code.strip()
        stats = self.storage.get_stats(code)
        if not stats:
            return False, None, f"Short code '{code}' not found."

        return True, stats, "Stats retrieved successfully."

    def list_urls(self, sort_by: str = "created_at", descending: bool = True) -> List[Dict[str, Any]]:
        """Returns all stored mappings."""
        return self.storage.list_urls(sort_by=sort_by, descending=descending)

    def delete(self, code: str) -> Tuple[bool, str]:
        """Deletes a short code."""
        if not code:
            return False, "Code cannot be empty."

        code = code.strip()
        deleted = self.storage.delete_url(code)
        if deleted:
            return True, f"Successfully deleted short code '{code}'."
        return False, f"Short code '{code}' not found."
