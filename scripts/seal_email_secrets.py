"""One-use transfer: seal three existing Email Secrets to GitHub's runtime Environment key."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path

from nacl.public import PublicKey, SealedBox

NAMES = ("EMAIL_USERNAME", "EMAIL_PASSWORD", "EMAIL_RECIPIENTS")
SOURCE = "murphyGo/ai-trend-report"
REF = "refs/heads/codex/ai-report-key-reuse-20261005"
DESTINATION = "murphyGo/investo-runtime"
ENVIRONMENT = "codex-runtime"
# Public encryption material fetched from the destination Environment API.
KEY_ID = "3380204578043523366"
PUBLIC_KEY = "XWBPDGeitkEtOsOssTG4+Wbe56TAy43cjwy5jZAfbXc="


def seal(values: Mapping[str, str], public_key: str) -> dict[str, str]:
    if set(values) != set(NAMES):
        raise ValueError("unexpected_secret_names")
    encoded = {name: values[name].encode("utf-8") for name in NAMES}
    if any(not value or len(value) >= 48 * 1024 for value in encoded.values()):
        raise ValueError("missing_or_oversized_secret")
    box = SealedBox(PublicKey(base64.b64decode(public_key, validate=True)))
    return {
        name: base64.b64encode(box.encrypt(value)).decode("ascii")
        for name, value in encoded.items()
    }


def main() -> int:
    try:
        if (
            os.environ.get("GITHUB_REPOSITORY") != SOURCE
            or os.environ.get("GITHUB_REF") != REF
            or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
        ):
            raise ValueError("unexpected_execution_context")
        run_id = os.environ["GITHUB_RUN_ID"]
        code_sha = os.environ["GITHUB_SHA"]
        if not run_id.isdecimal() or not re.fullmatch(r"[0-9a-f]{40}", code_sha):
            raise ValueError("invalid_run_identity")
        payload = {
            "source": SOURCE,
            "destination": DESTINATION,
            "environment": ENVIRONMENT,
            "run_id": run_id,
            "code_sha": code_sha,
            "key_id": KEY_ID,
            "sealed": seal({name: os.environ.get(name, "") for name in NAMES}, PUBLIC_KEY),
        }
        path = Path(os.environ["RUNNER_TEMP"]) / "ai-report-email-secrets.sealed.json"
        # Exclusive creation rejects pre-existing paths and symlinks.
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w") as output:
            json.dump(payload, output)
        print("Sealed three existing Email Secrets for the fixed runtime Environment.")
        return 0
    except Exception:
        # Never print exception objects, values, hashes, ciphertext or lengths.
        print("Secret sealing failed; no plaintext diagnostics emitted.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
