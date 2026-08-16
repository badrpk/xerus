from __future__ import annotations

import argparse
import json

from .memory import recall, remember, status


def main() -> int:
    parser = argparse.ArgumentParser(prog="xerus", description="Xerus disk-first memory")
    sub = parser.add_subparsers(dest="command", required=True)

    remember_p = sub.add_parser("remember", help="persist memory to disk")
    remember_p.add_argument("content")
    remember_p.add_argument("--namespace", default="general")
    remember_p.add_argument("--key", default=None)

    recall_p = sub.add_parser("recall", help="search persisted memory")
    recall_p.add_argument("query")
    recall_p.add_argument("--namespace", default=None)
    recall_p.add_argument("--limit", type=int, default=8)

    sub.add_parser("status", help="show memory backend status")

    args = parser.parse_args()
    if args.command == "remember":
        result = remember(args.content, namespace=args.namespace, memory_key=args.key)
    elif args.command == "recall":
        result = recall(args.query, namespace=args.namespace, limit=args.limit)
    else:
        result = status()

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
