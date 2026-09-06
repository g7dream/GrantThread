"""Loopback-only developer server. Demo identity switching is not deployed to AWS."""
import hashlib
import json
import os
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .api import Binary, dispatch
from .auth import local_identity, local_login
from .errors import DomainError, require
from .repository import get_repository
from .seed import seed_all


class Handler(BaseHTTPRequestHandler):
    server_version = "GrantThreadLocal/0.1"

    def respond(self, status, data):
        binary = isinstance(data, Binary)
        payload = data.data if binary else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", data.content_type if binary else "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if binary:
            safe_name = data.name.replace('"', "").replace("\r", "").replace("\n", "").encode("ascii", "ignore").decode()
            self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        origin = self.headers.get("Origin")
        if origin in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Authorization,Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,OPTIONS")
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def handle_request(self):
        try:
            hostname = urlparse("http://" + self.headers.get("Host", "")).hostname
            require(hostname in {"127.0.0.1", "localhost", "::1"}, "Local server accepts loopback hosts only", "forbidden", 403)
            origin = self.headers.get("Origin")
            require(not origin or origin in self.server.allowed_origins, "Origin is not allowed", "forbidden", 403)
            if self.command == "OPTIONS":
                return self.respond(204, {})
            path = urlparse(self.path).path.rstrip("/")
            length = int(self.headers.get("Content-Length", "0"))
            require(0 <= length <= 5 * 1024 * 1024, "Request body exceeds 5 MB", "too_large", 413)
            raw = self.rfile.read(length)
            body = {} if self.command == "PUT" or not raw else json.loads(raw)
            require(isinstance(body, dict), "JSON body must be an object")
            repository = self.server.repository
            if self.command == "GET" and path in {"/api/health", "/health"}:
                from .worker import agent_configured
                return self.respond(200, {"status": "ok", "mode": "local", "agentConfigured": agent_configured()})
            if self.command == "POST" and path == "/api/demo/login":
                return self.respond(200, local_login(repository, body.get("identity")))
            identity = local_identity(repository, self.headers.get("Authorization"))
            if self.command == "POST" and path == "/api/demo/reset":
                require(body.get("confirm") is True and identity["role"] == "grantee", "Confirm the synthetic data reset", "forbidden", 403)
                require(not any(j["status"] in {"queued", "running"} for org in ("brightpath", "harbour") for j in repository.read(org)["jobs"].values()),
                        "Wait for active agent work before resetting", "active_job", 409)
                seed_all(repository=repository, overwrite=True)
                current = hashlib.sha256(self.headers["Authorization"][7:].encode()).hexdigest()
                with repository.connect() as db:
                    db.execute("DELETE FROM sessions WHERE token_hash != ?", (current,))
                return self.respond(200, {"reset": True})
            result = dispatch(self.command, path, body, identity, repository=repository, raw=raw)
            self.respond(200, result)
        except DomainError as exc:
            self.respond(exc.status, {"error": exc.message, "code": exc.code})
        except (ValueError, UnicodeDecodeError):
            self.respond(400, {"error": "Request body or content length is invalid", "code": "invalid_request"})
        except Exception:
            traceback.print_exc()
            self.respond(500, {"error": "The request could not be completed. Your last confirmed state is preserved.", "code": "internal_error"})

    do_GET = handle_request
    do_POST = handle_request
    do_PUT = handle_request
    do_OPTIONS = handle_request


def main():
    require(os.getenv("GRANTTHREAD_MODE", "local") == "local", "Do not run local demo authentication in cloud mode")
    repository = get_repository()
    seed_all(repository=repository)
    port = int(os.getenv("GRANTTHREAD_PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.repository = repository
    server.allowed_origins = {"http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000"}
    print(f"GrantThread synthetic local API: http://127.0.0.1:{port}/api", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
