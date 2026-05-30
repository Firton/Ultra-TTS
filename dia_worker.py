#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import dia_backend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.json:
        print("Use --json and send a request JSON object on stdin.", file=sys.stderr)
        return 2

    try:
        request = json.loads(sys.stdin.read())
        result = dia_backend._generate_to_file_local(
            request["diaText"],
            Path(request["outputPath"]),
            request.get("options") or {},
        )
        print(json.dumps(result), flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
