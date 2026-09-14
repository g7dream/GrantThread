"""API Gateway HTTP API v2 Lambda integration. Gateway validates JWT signatures."""
import base64
import json
import logging
import os

from .api import Binary, Redirect, dispatch
from .auth import gateway_identity
from .errors import DomainError, require
from .repository import get_repository

# Base64 and the integration envelope must fit Lambda's synchronous response limit.
MAX_INLINE_BINARY_BYTES = 4 * 1024 * 1024


def handler(event, context):
    try:
        require(os.getenv("GRANTTHREAD_MODE") == "aws", "Cloud handler configuration is invalid", "configuration_error", 503)
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path = event.get("rawPath", "/")
        if path.rstrip("/") in {"/health", "/api/health"} and method == "GET":
            from .worker import agent_configured
            return response(200, {"status": "ok", "mode": "aws", "agentConfigured": agent_configured()})
        repository = get_repository()
        identity = gateway_identity(event, repository)
        raw = event.get("body") or ""
        raw = base64.b64decode(raw, validate=True) if event.get("isBase64Encoded") else raw.encode()
        require(len(raw) <= 5 * 1024 * 1024, "Request exceeds 5 MB", "too_large", 413)
        body = json.loads(raw) if raw else {}
        require(isinstance(body, dict), "JSON body must be an object")
        result = dispatch(method, path, body, identity, repository=repository)
        if isinstance(result, Redirect):
            return {"statusCode": 302, "headers": {"Location": result.location, "Cache-Control": "no-store"}, "body": ""}
        if isinstance(result, Binary):
            require(len(result.data) <= MAX_INLINE_BINARY_BYTES,
                    'This export is too large to download through the hosted API. Use a smaller template or reporting period.',
                    'export_too_large', 413)
            name = result.name.replace('"', "").replace("\r", "").replace("\n", "").encode("ascii", "ignore").decode()
            return {"statusCode": 200, "isBase64Encoded": True, "headers": {"Content-Type": result.content_type,
                    "Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
                    "body": base64.b64encode(result.data).decode()}
        return response(200, result)
    except DomainError as exc:
        return response(exc.status, {"error": exc.message, "code": exc.code})
    except (ValueError, UnicodeDecodeError):
        return response(400, {"error": "Invalid JSON request", "code": "invalid_request"})
    except Exception:
        logging.exception("GrantThread API request failed")
        return response(500, {"error": "The request could not be completed", "code": "internal_error"})


def response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
            "body": json.dumps(body, ensure_ascii=False)}
