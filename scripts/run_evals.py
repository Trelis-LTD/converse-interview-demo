from __future__ import annotations

import argparse
import os
from pathlib import Path

from converse_sdk.evals import EvalsClient, EvalsError, load_cases, validate_case
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the guided interview eval suite")
    parser.add_argument("--modality", choices=("text", "voice"), default="text")
    parser.add_argument("--repetitions", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()
    api_key = os.getenv("CONVERSE_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("CONVERSE_API_KEY is required in .env")

    documents = [
        validate_case(document, modality=args.modality)
        for document in load_cases(PROJECT_ROOT / "evals")
    ]
    client = EvalsClient(
        api_key,
        base_url=os.getenv("CONVERSE_API_BASE_URL", "https://converse.trelis.com"),
    )
    try:
        cases = client.upsert_cases(documents)
        run = client.start_run(
            [case["id"] for case in cases],
            modality=args.modality,
            repetitions=args.repetitions,
        )
        print(f"Dashboard: {client.dashboard_url(run['id'])}")
        run = client.wait(run["id"])
    except (EvalsError, TimeoutError) as exc:
        raise SystemExit(str(exc)) from None

    for attempt in run.get("attempts", []):
        reason = attempt.get("termination_reason") or ""
        print(f"{attempt['status']:<9} {attempt['case_name']} {reason}")
    print(f"Run status: {run['status']}")
    if run.get("status") != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
