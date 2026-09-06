"""Package compiled public assets only. Never collect frontend/.env or backend records."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="/grantthread/")
    args = parser.parse_args()
    if not re.fullmatch(r"/(?:[a-z0-9-]+/)*", args.base):
        raise SystemExit("Base must be a lowercase absolute path with a trailing slash")
    dist = ROOT / "frontend" / "dist"
    if not (dist / "index.html").is_file():
        raise SystemExit("Build the frontend first")
    index = (dist / "index.html").read_text(encoding="utf-8")
    if args.base != "/" and args.base + "assets/" not in index:
        raise SystemExit("Build with VITE_BASE_PATH matching --base before packaging")
    output = ROOT / "artifacts" / "GrantThread-cpanel.zip"
    output.parent.mkdir(exist_ok=True)
    rewrite = f"""Options -Indexes
DirectoryIndex index.html
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteBase {args.base}
# Application uses hash routes; unknown non-file paths receive the SPA.
RewriteCond %{{REQUEST_FILENAME}} !-f
RewriteCond %{{REQUEST_FILENAME}} !-d
RewriteRule ^ index.html [L]
</IfModule>
<IfModule mod_headers.c>
Header always set X-Content-Type-Options nosniff
Header always set Referrer-Policy strict-origin-when-cross-origin
Header always set X-Frame-Options DENY
<FilesMatch "^(index\\.html|config\\.json)$">
Header set Cache-Control "no-store"
</FilesMatch>
</IfModule>
"""
    # The parent directory handles mixed-case directory names before the subfolder is resolved.
    segment = args.base.strip("/")
    parent_rule = ""
    if segment:
        parent_rule = f"RewriteEngine On\nRewriteCond %{{REQUEST_URI}} !^{re.escape(args.base)}\nRewriteRule ^{re.escape(segment)}(?:/(.*))?$ {args.base}$1 [R=302,L,NC]\n"
    readme = f"""GrantThread public frontend package — synthetic data only

Upload the ZIP contents into a dedicated existing domain's {args.base} directory.
www.spaceship.com is the provider's website, not your owned deployment domain.
Back up destination files before upload. Do not replace another website.

This package needs the AWS API and Cognito public build settings before it is a live application.
Configure frontend/.env.local with the SAM outputs and VITE_BASE_PATH={args.base}, rebuild and repackage.
No credentials or backend data belong in this ZIP. The source repository contains full setup instructions.

For /GrantThread and other letter-case variants to reach {args.base}, merge this block into
the PARENT document root .htaccess, before any existing catch-all rule (do not overwrite it):

{parent_rule}
Use temporary redirects for initial testing; switch 302 to301 only after verifying your domain.
"""
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(dist.rglob("*")):
            if file.is_file() and file.name != ".htaccess":
                archive.write(file, file.relative_to(dist).as_posix())
        archive.writestr(".htaccess", rewrite)
        archive.writestr("DEPLOYMENT.txt", readme)
        archive.write(ROOT / "LICENSE", "LICENSE.txt")
        notices = []
        for package in ["react", "react-dom", "lucide-react"]:
            licence = ROOT / "frontend" / "node_modules" / package / "LICENSE"
            if not licence.is_file():
                raise SystemExit(f"Missing third-party licence for {package}; install locked frontend dependencies first")
            notices.append(package + "\n" + licence.read_text(encoding="utf-8"))
        notices.append("Inter font: see INTER-LICENSE.txt in this package.")
        archive.writestr("THIRD_PARTY_NOTICES.txt", "\n\n".join(notices))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (output.parent / "GrantThread-cpanel.sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(json.dumps({"zip": str(output), "sha256": digest, "bytes": output.stat().st_size, "base": args.base, "cloudConfigured": "requires verified SAM outputs"}))


if __name__ == "__main__":
    main()
