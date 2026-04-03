from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import requests


DEFAULT_URL = "https://api.tavily.com/search"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search the web with Tavily.")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument(
        "--topic",
        choices=("general", "news"),
        default="general",
        help="Search topic",
    )
    parser.add_argument("--max-results", type=int, default=5, help="Maximum number of results")
    parser.add_argument(
        "--include-answer",
        action="store_true",
        default=True,
        help="Include Tavily's synthesized answer",
    )
    parser.add_argument(
        "--include-raw-content",
        action="store_true",
        help="Include raw content when available",
    )
    return parser.parse_args()


def main() -> int:
    configure_stdout()
    args = parse_args()
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print(
            json.dumps(
                {"error": "Missing TAVILY_API_KEY environment variable."},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    payload = {
        "api_key": api_key,
        "query": args.query,
        "topic": args.topic,
        "max_results": args.max_results,
        "include_answer": args.include_answer,
        "include_raw_content": args.include_raw_content,
    }

    try:
        response = requests.post(DEFAULT_URL, json=payload, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(json.dumps({"error": f"Tavily request failed: {exc}"}, ensure_ascii=False, indent=2))
        return 2

    try:
        data = response.json()
    except ValueError:
        print(
            json.dumps(
                {
                    "error": "Tavily returned a non-JSON response.",
                    "status_code": response.status_code,
                    "body": response.text[:1000],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    print(json.dumps(_normalize_response(data), ensure_ascii=False, indent=2))
    return 0


def _normalize_response(data: dict[str, Any]) -> dict[str, Any]:
    results = []
    for item in data.get("results", []) or []:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
                "score": item.get("score"),
                "published_date": item.get("published_date"),
            }
        )

    return {
        "query": data.get("query"),
        "answer": data.get("answer"),
        "response_time": data.get("response_time"),
        "results": results,
    }


if __name__ == "__main__":
    sys.exit(main())
