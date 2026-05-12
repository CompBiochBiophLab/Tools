#!/usr/bin/env python3
"""Create or update WordPress posts from the terminal."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "wp-uploader" / "config.json"
VALID_STATUSES = ("draft", "publish", "pending", "private", "future")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update WordPress posts using the WordPress REST API."
    )
    parser.add_argument("--site", help="WordPress site URL, for example https://example.com")
    parser.add_argument("--user", help="WordPress username")
    parser.add_argument(
        "--password",
        help="WordPress application password. Prefer WP_APP_PASSWORD instead.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help=f"JSON config file path. Default: {DEFAULT_CONFIG_PATH}",
    )
    parser.add_argument("--title", help="Post title")
    parser.add_argument("--content-file", help="Path to a text, HTML, or Markdown file")
    parser.add_argument("--content", help="Post content passed directly as text")
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Convert Markdown content to HTML. Requires the optional 'markdown' package.",
    )
    parser.add_argument(
        "--status",
        choices=VALID_STATUSES,
        default="draft",
        help="Post status. Default: draft",
    )
    parser.add_argument("--excerpt", help="Post excerpt")
    parser.add_argument("--slug", help="Post slug")
    parser.add_argument(
        "--categories",
        help="Comma-separated category IDs, for example 2,7",
    )
    parser.add_argument("--tags", help="Comma-separated tag IDs, for example 4,9")
    parser.add_argument("--featured-media", type=int, help="WordPress media ID")
    parser.add_argument(
        "--post-id",
        type=int,
        help="Update an existing post instead of creating a new one.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the JSON payload without sending it to WordPress.",
    )
    return parser.parse_args()


def load_config(config_path: str) -> dict[str, Any]:
    path = Path(config_path).expanduser()
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as error:
        raise SystemExit(f"Error: invalid JSON config file {path}: {error}") from error


def first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def csv_ints(value: str | None, field_name: str) -> list[int] | None:
    if not value:
        return None

    try:
        return [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise SystemExit(f"Error: {field_name} must contain comma-separated numeric IDs.") from error


def read_content(args: argparse.Namespace) -> str:
    if args.content and args.content_file:
        raise SystemExit("Error: use --content or --content-file, not both.")

    if args.content:
        content = args.content
    elif args.content_file:
        path = Path(args.content_file).expanduser()
        if not path.exists():
            raise SystemExit(f"Error: content file does not exist: {path}")
        content = path.read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            raise SystemExit("Error: provide --content, --content-file, or pipe content via stdin.")
        content = sys.stdin.read()

    if args.markdown:
        try:
            import markdown  # type: ignore[import-not-found]
        except ImportError as error:
            raise SystemExit(
                "Error: --markdown requires the optional package 'markdown'. "
                "Install it with: python3 -m pip install markdown"
            ) from error
        content = markdown.markdown(content, extensions=["extra", "sane_lists"])

    return content


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    content = read_content(args)
    payload: dict[str, Any] = {
        "content": content,
        "status": args.status,
    }

    if args.title:
        payload["title"] = args.title
    elif not args.post_id:
        raise SystemExit("Error: --title is required when creating a new post.")

    optional_fields = {
        "excerpt": args.excerpt,
        "slug": args.slug,
        "featured_media": args.featured_media,
        "categories": csv_ints(args.categories, "categories"),
        "tags": csv_ints(args.tags, "tags"),
    }
    payload.update({key: value for key, value in optional_fields.items() if value is not None})
    return payload


def normalize_site_url(site: str) -> str:
    site = site.strip().rstrip("/") + "/"
    if not site.startswith(("http://", "https://")):
        raise SystemExit("Error: --site must start with http:// or https://")
    return site


def endpoint_for(site: str, post_id: int | None) -> str:
    path = "wp-json/wp/v2/posts"
    if post_id:
        path += f"/{post_id}"
    return urljoin(site, path)


def request_wordpress(
    site: str,
    user: str,
    password: str,
    payload: dict[str, Any],
    post_id: int | None,
) -> dict[str, Any]:
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        endpoint_for(site, post_id),
        data=data,
        method="POST",
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "wp-post-cli/1.0",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"WordPress returned HTTP {error.code}: {details}") from error
    except URLError as error:
        raise SystemExit(f"Connection error: {error.reason}") from error

    return json.loads(response_body)


def main() -> int:
    args = parse_args()
    payload = build_payload(args)

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    config = load_config(args.config)

    site = first_value(args.site, os.getenv("WP_SITE_URL"), config.get("site_url"))
    user = first_value(args.user, os.getenv("WP_USER"), config.get("user"))
    password = first_value(args.password, os.getenv("WP_APP_PASSWORD"), config.get("app_password"))

    if not site:
        raise SystemExit("Error: set --site, WP_SITE_URL, or site_url in the config file.")
    if not user:
        raise SystemExit("Error: set --user, WP_USER, or user in the config file.")
    if not password:
        password = getpass.getpass("WordPress application password: ")

    result = request_wordpress(normalize_site_url(site), user, password, payload, args.post_id)
    print(f"OK: post ID {result.get('id')}")
    print(f"Status: {result.get('status')}")
    print(f"Link: {result.get('link')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
