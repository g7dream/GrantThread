"""Offline validation for the small, public GrantThread frontend configuration.

Validation establishes a consistent build, not working cloud authentication or
model access. No AWS clients, credential files, or network requests are used.
"""
from __future__ import annotations

import ipaddress
import json
import re
from urllib.parse import urlsplit

PUBLIC_KEYS = ("apiUrl", "cognitoDomain", "cognitoClientId", "cognitoRedirectUri")
ENV_KEYS = {
    "apiUrl": "VITE_API_URL",
    "cognitoDomain": "VITE_COGNITO_DOMAIN",
    "cognitoClientId": "VITE_COGNITO_CLIENT_ID",
    "cognitoRedirectUri": "VITE_COGNITO_REDIRECT_URI",
}


class ReleaseError(ValueError):
    """A release cannot safely be prepared from the supplied local inputs."""


def read_json(text: str):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseError("JSON contains a duplicate key")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=unique_pairs)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ReleaseError("Input must be valid JSON") from exc


def validate_base(base: str) -> str:
    if not isinstance(base, str) or not re.fullmatch(r"/(?:[a-z0-9-]+/)*", base):
        raise ReleaseError("Base must be a lowercase absolute path with a trailing slash")
    return base


def https_url(value: str, label: str):
    if not isinstance(value, str) or not value or any(ord(c) <= 32 for c in value):
        raise ReleaseError(f"{label} must be a public HTTPS URL")
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise ReleaseError(f"{label} is not a valid URL") from exc
    if (parts.scheme != "https" or not parts.hostname or parts.username is not None
            or parts.password is not None or parts.query or parts.fragment
            or port not in (None, 443) or any(c in value for c in "\\%$\"'`<>")):
        raise ReleaseError(f"{label} must use HTTPS without credentials, query, fragment or a custom port")
    host = parts.hostname.lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host) or ".." in host:
        raise ReleaseError(f"{label} must have a valid public hostname")
    if "." not in host or host.endswith((".localhost", ".local", ".test", ".example", ".invalid")):
        raise ReleaseError(f"{label} must not point to a local or example hostname")
    if host in ("example.com", "example.org", "example.net") or host.endswith((".example.com", ".example.org", ".example.net")):
        raise ReleaseError(f"{label} still uses an example hostname")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        raise ReleaseError(f"{label} must use the deployed service hostname, not an IP address")
    if not re.fullmatch(r"(?:/[a-zA-Z0-9_-]*)*", parts.path) or "//" in parts.path:
        raise ReleaseError(f"{label} contains an unsupported URL path")
    return parts


def validate_site(site_url: str, base: str):
    parts = https_url(site_url, "Site URL")
    if parts.path != validate_base(base):
        raise ReleaseError("Site URL path must exactly match --base, including the trailing slash")
    return parts


def validate_cloud_config(config: dict, base: str, site_url: str) -> dict:
    validate_site(site_url, base)
    if not isinstance(config, dict) or set(config) != set(PUBLIC_KEYS):
        raise ReleaseError("Build publicConfig must contain only the four supported public settings")
    for key in PUBLIC_KEYS:
        if not isinstance(config[key], str) or not config[key] or config[key] != config[key].strip():
            raise ReleaseError(f"Cloud build requires a nonempty {ENV_KEYS[key]}")
    api = https_url(config["apiUrl"], "API URL")
    if not api.path.endswith("/api") or "//" in api.path:
        raise ReleaseError("API URL must end in /api without a trailing slash")
    domain = https_url(config["cognitoDomain"], "Cognito domain")
    if domain.path not in ("", "/"):
        raise ReleaseError("Cognito domain must be an HTTPS origin without a path")
    if not re.fullmatch(r"[a-z0-9]{1,128}", config["cognitoClientId"]):
        raise ReleaseError("Cognito client ID must be the public app client ID from the stack outputs")
    if config["cognitoClientId"] in {"placeholder", "changeme", "clientid", "example"}:
        raise ReleaseError("Cognito client ID is still a placeholder")
    if config["cognitoRedirectUri"] != site_url:
        raise ReleaseError("VITE_COGNITO_REDIRECT_URI must exactly match --site-url")
    https_url(config["cognitoRedirectUri"], "Cognito redirect URI")
    return dict(config)


def stack_outputs(document) -> dict[str, str]:
    """Accept aws describe-stacks JSON, its Outputs list, or a simple output map."""
    if isinstance(document, dict) and "Stacks" in document:
        stacks = document["Stacks"]
        if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
            raise ReleaseError("Select exactly one stack when exporting outputs")
        document = stacks[0]
    if isinstance(document, dict) and "Outputs" in document:
        document = document["Outputs"]
    if isinstance(document, list):
        result = {}
        for entry in document:
            if not isinstance(entry, dict) or not isinstance(entry.get("OutputKey"), str) or not isinstance(entry.get("OutputValue"), str):
                raise ReleaseError("Stack output entries require OutputKey and OutputValue strings")
            if entry["OutputKey"] in result:
                raise ReleaseError("Stack outputs contain a duplicate OutputKey")
            result[entry["OutputKey"]] = entry["OutputValue"]
        return result
    if isinstance(document, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in document.items()):
        return document
    raise ReleaseError("Expected one CloudFormation stack's public Outputs JSON")


def config_from_outputs(document, site_url: str, base: str) -> dict:
    outputs = stack_outputs(document)
    mapping = {"ApiUrl": "apiUrl", "CognitoDomain": "cognitoDomain", "CognitoClientId": "cognitoClientId"}
    missing = [key for key in mapping if not outputs.get(key)]
    if missing:
        raise ReleaseError("Missing stack outputs: " + ", ".join(missing))
    config = {target: outputs[source] for source, target in mapping.items()}
    config["cognitoRedirectUri"] = site_url
    if outputs.get("CallbackUrl", site_url) != site_url:
        raise ReleaseError("Stack CallbackUrl does not match --site-url; rebuild cannot repair Cognito callback registration")
    site = validate_site(site_url, base)
    if outputs.get("FrontendOrigin", f"{site.scheme}://{site.netloc}") != f"{site.scheme}://{site.netloc}":
        raise ReleaseError("Stack FrontendOrigin does not match --site-url; correct the stack CORS configuration")
    if set(outputs.get("CognitoScope", "openid email profile grantthread/access").split()) != {"openid", "email", "profile", "grantthread/access"}:
        raise ReleaseError("Stack CognitoScope does not match the frontend access-token scopes")
    return validate_cloud_config(config, base, site_url)
