"""Prepare only public Vite settings from an existing stack-output JSON file.

This offline command never accesses AWS or modifies a stack. Its default output
is a reviewable file under artifacts; copy it into frontend/.env.production.local
after checking the chosen account, stack and site. It will not overwrite a file
unless --overwrite is passed explicitly.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from release_config import ENV_KEYS, ReleaseError, config_from_outputs, read_json

ROOT = Path(__file__).resolve().parents[1]


def render_env(config: dict, base: str) -> str:
    lines = ["# Public build settings only. No AWS credentials or client secrets.", f"VITE_BASE_PATH={base}"]
    lines.extend(f"{ENV_KEYS[key]}={config[key]}" for key in ENV_KEYS)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", type=Path, required=True, help="Saved public CloudFormation stack outputs JSON")
    parser.add_argument("--site-url", required=True, help="Exact registered callback URL, including subfolder and trailing slash")
    parser.add_argument("--base", default="/grantthread/")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "frontend.env.production")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        config = config_from_outputs(read_json(args.outputs.read_text(encoding="utf-8-sig")), args.site_url, args.base)
        if args.output.resolve() == args.outputs.resolve():
            raise ReleaseError("Output must not overwrite the input stack outputs")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w" if args.overwrite else "x", encoding="utf-8", newline="\n") as target:
            target.write(render_env(config, args.base))
    except FileExistsError:
        parser.exit(2, "Output already exists; inspect it, then use --overwrite if replacement is intended.\n")
    except (OSError, ReleaseError) as exc:
        parser.exit(2, f"Public configuration could not be prepared: {exc}\n")
    print(json.dumps({"output": str(args.output), "siteUrl": args.site_url, "basePath": args.base,
                      "verification": "offline configuration only; cloud sign-in and API access still require testing"}))


if __name__ == "__main__":
    main()
