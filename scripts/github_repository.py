"""Inspect or create the authorised public repository using Git Credential Manager.

Credentials remain in process memory and never enter command arguments, files or logs.
Default mode is read-only. --create requires the user-authorised account to match.
"""
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                            text=True, capture_output=True, env=env, timeout=30)
    if result.returncode:
        print(json.dumps({"authenticated": False, "blocker": "GitHub sign-in is not available through Git Credential Manager. Sign in once; do not paste tokens into source."}))
        return
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    token = values.get("password")
    if not token:
        print(json.dumps({"authenticated": False, "blocker": "No usable GitHub credential"}))
        return

    def call(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request("https://api.github.com" + path, data=data,
                    headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "User-Agent": "GrantThread-build", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    user = call("/user")
    if user["login"].lower() != "g7dream":
        print(json.dumps({"authenticated": True, "account": user["login"], "blocker": "Connected account does not match the requested g7dream account"}))
        return
    try:
        repo = call("/repos/g7dream/GrantThread")
        print(json.dumps({"authenticated": True, "account": user["login"], "repository": repo["html_url"], "private": repo["private"], "size": repo["size"], "exists": True}))
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        if not args.create:
            print(json.dumps({"authenticated": True, "account": user["login"], "exists": False, "canCreateRequestedRepository": True}))
            return
        repo = call("/user/repos", {"name": "GrantThread", "description": "Many grants. One clear thread. Scoped evidence, exact allocations and shared grant reporting.", "private": False, "auto_init": False})
        print(json.dumps({"created": True, "repository": repo["html_url"], "private": repo["private"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Avoid logging request headers or credential-helper output.
        print(json.dumps({"error": type(exc).__name__, "blocker": "GitHub access could not be verified; no credentials were written to disk."}))
        raise SystemExit(1)
