"""Opaque local sessions; Cognito membership comes only from validated gateway claims."""
import hashlib
import json
import os
import secrets
import time

from .errors import DomainError, require
from .seed import IDENTITIES


def local_login(repository, identity_key):
    require(os.getenv("GRANTTHREAD_MODE") != "aws", "Demo login is not available here", "not_found", 404)
    require(identity_key in IDENTITIES, "Choose a synthetic demo identity")
    identity = IDENTITIES[identity_key]
    token = secrets.token_urlsafe(40)
    digest = hashlib.sha256(token.encode()).hexdigest()
    with repository.connect() as db:
        db.execute("DELETE FROM sessions WHERE expires < ?", (int(time.time()),))
        db.execute("INSERT INTO sessions VALUES (?,?,?)", (digest, json.dumps(identity), int(time.time()) + 8 * 3600))
    return {"token": token, "user": identity}


def local_identity(repository, authorization):
    require(isinstance(authorization, str) and authorization.startswith("Bearer "), "Sign in to continue", "unauthorised", 401)
    token = authorization[7:]
    require(len(token) <= 200, "Invalid session", "unauthorised", 401)
    with repository.connect() as db:
        row = db.execute("SELECT identity,expires FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
    require(row and row[1] > time.time(), "Your session expired. Sign in again.", "unauthorised", 401)
    return json.loads(row[0])


def gateway_identity(event, repository):
    # This handler must only be invoked by the SAM-managed JWT-authorised API Gateway.
    # No Lambda function URL or client-supplied identity header is accepted.
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    require(claims.get("token_use") == "access" and claims.get("sub") and "grantthread/access" in claims.get("scope", "").split(),
            "A scoped Cognito access token is required", "unauthorised", 401)
    try:
        identity = repository.read_key("MEMBER#" + claims["sub"])
    except DomainError as exc:
        raise DomainError("This signed-in user has no GrantThread membership", "membership_required", 403) from exc
    require(identity.get("id") == claims["sub"] and identity.get("role") in {"grantee", "funder"} and identity.get("organisationId"),
            "Server membership is invalid", "forbidden", 403)
    return identity
