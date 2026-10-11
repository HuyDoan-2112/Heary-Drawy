#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from services.api.app.contracts.schemas import ContractBundle

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "schema.json"


def build_schema() -> dict:
    schema = ContractBundle.model_json_schema(mode="validation")
    schema["title"] = "Heary Drawy contracts"
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return schema


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if contracts/schema.json is stale")
    args = parser.parse_args()

    rendered = json.dumps(build_schema(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not SCHEMA_PATH.exists():
            raise SystemExit(f"{SCHEMA_PATH} does not exist")
        current = SCHEMA_PATH.read_text()
        if current != rendered:
            raise SystemExit("contracts/schema.json is stale. Run npm run generate:contracts.")
        return 0

    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
