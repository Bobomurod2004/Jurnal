#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from html import unescape

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAINWEB_DIR = os.path.dirname(SCRIPT_DIR)
if MAINWEB_DIR not in sys.path:
    sys.path.append(MAINWEB_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _parse_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_int_list(value):
    if isinstance(value, (list, tuple, set)):
        raw_items = value
    else:
        raw_text = _clean_text(value).strip('{}[]')
        raw_items = [item.strip().strip('"').strip("'") for item in raw_text.split(',') if item.strip()]

    result = []
    for raw_item in raw_items:
        item_id = _parse_int(raw_item)
        if item_id is not None and item_id not in result:
            result.append(item_id)
    return result


def _has_page_bounds(page_range_value):
    page_range_text = _clean_text(page_range_value)
    if not page_range_text:
        return False
    normalized = page_range_text.replace("–", "-").replace("—", "-")
    if re.search(r"([A-Za-z]?\d+)\s*-\s*([A-Za-z]?\d+)", normalized):
        return True
    if re.search(r"([A-Za-z]?\d+)", normalized):
        return True
    return False


def _build_connector():
    from modules.connector import PostgreSQLConnector
    import settings

    return PostgreSQLConnector(
        host=os.getenv("DB_HOST", settings.DB_HOST),
        port=int(os.getenv("DB_PORT", settings.DB_PORT)),
        user=os.getenv("DB_USER", settings.DB_USER),
        password=os.getenv("DB_PASSWORD", settings.DB_PASSWORD),
        database=os.getenv("DB_NAME", settings.DB_NAME),
    )


def _load_author_names(dbc):
    author_map = {}
    for row in dbc.author_profile.get().exec():
        author_id = _parse_int(row.get("id"))
        if author_id is None:
            continue
        author_map[author_id] = _clean_text(row.get("name"))
    return author_map


def _load_issue_map(dbc):
    issue_map = {}
    for issue in dbc.issues.get().exec():
        issue_id = _parse_int(issue.get("id"))
        if issue_id is None:
            continue
        issue_map[issue_id] = issue
    return issue_map


def _load_file_map(dbc):
    file_map = {}
    try:
        rows = dbc.files.get().exec() or []
    except Exception:
        return file_map
    for row in rows:
        file_id = _parse_int(row.get("id"))
        if file_id is not None:
            file_map[file_id] = row
    return file_map


def _publication_has_world_readable_access(publication):
    return not bool((publication or {}).get("is_paid") or (publication or {}).get("subscription_enable"))


def _publication_author_names(publication, author_map):
    result = []
    publication_row = publication or {}
    author_ids = []

    main_author_id = _parse_int(publication_row.get("main_author_id"))
    if main_author_id is not None:
        author_ids.append(main_author_id)

    co_author_ids = publication_row.get("subauthor_ids") or publication_row.get("sub_author_ids") or []
    author_ids.extend(_parse_int_list(co_author_ids))

    seen = set()
    for author_id in author_ids:
        name = _clean_text(author_map.get(author_id))
        if not name:
            continue
        lowered = name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(name)
    return result


def _public_pdf_exists(file_row, save_path):
    stored_path = _clean_text((file_row or {}).get("filepath"))
    root_path = os.path.abspath(os.path.join(_clean_text(save_path), "static", "uploads"))
    if not stored_path.startswith("/static/uploads/") or not _clean_text(save_path):
        return False

    candidate_path = os.path.abspath(os.path.join(_clean_text(save_path), stored_path.lstrip("/")))
    try:
        if os.path.commonpath([candidate_path, root_path]) != root_path:
            return False
    except ValueError:
        return False
    return os.path.isfile(candidate_path)


def _publication_pdf_reference_status(publication, file_map, verify_files=False, save_path=""):
    file_ids = _parse_int_list((publication or {}).get("file_ids"))
    if not file_ids:
        return "missing_pdf_reference"

    # Public download resolves newer files first, so readiness must not report
    # a stale older attachment as a blocker when a newer valid PDF is usable.
    file_rows = [file_map[file_id] for file_id in reversed(file_ids) if file_id in file_map]
    if not file_rows:
        return "missing_pdf_file_record"

    pdf_rows = []
    for file_row in file_rows:
        name = _clean_text(file_row.get("name")).lower()
        filepath = _clean_text(file_row.get("filepath")).lower()
        if name.endswith(".pdf") or filepath.endswith(".pdf"):
            pdf_rows.append(file_row)
    if not pdf_rows:
        return "invalid_pdf_file_reference"
    if not verify_files or not _clean_text(save_path):
        return "ok"
    if any(_public_pdf_exists(file_row, save_path) for file_row in pdf_rows):
        return "ok"
    return "missing_pdf_on_disk"


def _has_visible_abstract(value):
    abstract_text = re.sub(r"(?is)<[^>]+>", " ", unescape(_clean_text(value)))
    return bool(re.sub(r"\s+", " ", abstract_text).strip())


def _publication_report_item(publication, issue, author_names, file_map=None, verify_files=False, save_path=""):
    publication_row = publication or {}
    issue_row = issue or {}
    files = file_map or {}

    title = _clean_text(publication_row.get("title"))
    has_title = bool(title)
    has_authors = bool(author_names)
    has_abstract = _has_visible_abstract(publication_row.get("abstract"))
    has_issue = bool(issue_row)
    has_volume = bool(_clean_text(issue_row.get("vol_no")))
    has_issue_no = bool(_clean_text(issue_row.get("issue_no")))
    has_publish_date = bool(_parse_int(publication_row.get("date_publish")) or _parse_int(issue_row.get("year")))
    has_page_range = _has_page_bounds(publication_row.get("page_range"))
    has_doi = bool(_clean_text(publication_row.get("doi")))
    is_world_readable = _publication_has_world_readable_access(publication_row)
    pdf_reference_status = _publication_pdf_reference_status(
        publication_row,
        files,
        verify_files=verify_files,
        save_path=save_path,
    )

    blockers = []
    warnings = []

    if not has_title:
        blockers.append("missing_title")
    if not has_authors:
        blockers.append("missing_author")
    if not has_abstract:
        blockers.append("missing_abstract")
    if not has_issue:
        blockers.append("missing_issue")
    if not has_publish_date:
        blockers.append("missing_publish_date")
    if not has_volume:
        blockers.append("missing_volume")
    if not has_issue_no:
        blockers.append("missing_issue_number")
    if not has_page_range:
        blockers.append("missing_page_range")
    if is_world_readable and pdf_reference_status != "ok":
        blockers.append(pdf_reference_status)

    if not has_doi:
        warnings.append("missing_doi")

    return {
        "article_id": _parse_int(publication_row.get("id")),
        "issue_id": _parse_int(publication_row.get("issue_id")),
        "title": title,
        "is_world_readable": is_world_readable,
        "author_names": author_names,
        "has_abstract": has_abstract,
        "pdf_reference_status": pdf_reference_status,
        "blockers": blockers,
        "warnings": warnings,
        "ready": not blockers,
    }


def _build_report(dbc, limit=None, verify_files=False, save_path=""):
    author_map = _load_author_names(dbc)
    issue_map = _load_issue_map(dbc)
    file_map = _load_file_map(dbc)
    publication_rows = dbc.publications.get().exec()
    publication_rows = sorted(publication_rows, key=lambda row: _parse_int(row.get("id")) or 0, reverse=True)
    if limit and limit > 0:
        publication_rows = publication_rows[:limit]

    items = []
    blocker_counter = Counter()
    warning_counter = Counter()
    open_access_total = 0
    open_access_ready = 0

    for publication in publication_rows:
        issue_id = _parse_int(publication.get("issue_id"))
        issue = issue_map.get(issue_id)
        author_names = _publication_author_names(publication, author_map)
        item = _publication_report_item(
            publication,
            issue,
            author_names,
            file_map=file_map,
            verify_files=verify_files,
            save_path=save_path,
        )
        items.append(item)
        blocker_counter.update(item["blockers"])
        warning_counter.update(item["warnings"])

        if item["is_world_readable"]:
            open_access_total += 1
            if item["ready"]:
                open_access_ready += 1

    ready_total = sum(1 for item in items if item["ready"])
    total = len(items)
    readiness_pct = round((ready_total / total) * 100, 2) if total else 0.0
    open_access_pct = round((open_access_ready / open_access_total) * 100, 2) if open_access_total else 0.0

    summary = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_articles_checked": total,
        "ready_articles": ready_total,
        "ready_percent": readiness_pct,
        "open_access_articles": open_access_total,
        "open_access_ready_articles": open_access_ready,
        "open_access_ready_percent": open_access_pct,
        "top_blockers": blocker_counter.most_common(),
        "top_warnings": warning_counter.most_common(),
    }
    return {"summary": summary, "articles": items}


def _print_console_report(report, show_problem_limit=20):
    summary = report["summary"]
    print("Google Scholar Readiness Audit")
    print("=" * 32)
    print(f"Generated at (UTC): {summary['generated_at_utc']}")
    print(f"Total checked:       {summary['total_articles_checked']}")
    print(f"Ready articles:      {summary['ready_articles']} ({summary['ready_percent']}%)")
    print(
        "Open-access ready:   "
        f"{summary['open_access_ready_articles']}/{summary['open_access_articles']} "
        f"({summary['open_access_ready_percent']}%)"
    )

    if summary["top_blockers"]:
        print("\nTop blockers:")
        for blocker_name, blocker_count in summary["top_blockers"]:
            print(f"  - {blocker_name}: {blocker_count}")
    else:
        print("\nTop blockers:\n  - none")

    if summary["top_warnings"]:
        print("\nTop warnings:")
        for warning_name, warning_count in summary["top_warnings"]:
            print(f"  - {warning_name}: {warning_count}")
    else:
        print("\nTop warnings:\n  - none")

    problems = [item for item in report["articles"] if item["blockers"]]
    if problems:
        print(f"\nArticles with blockers (showing up to {show_problem_limit}):")
        for item in problems[:show_problem_limit]:
            title = item["title"] or "(empty title)"
            blockers_text = ", ".join(item["blockers"])
            print(f"  - #{item['article_id']} | {title} | {blockers_text}")
    else:
        print("\nAll checked articles are blocker-free.")


def _parse_args():
    parser = argparse.ArgumentParser(description="Audit publication metadata readiness for Google Scholar.")
    parser.add_argument("--limit", type=int, default=0, help="Check only most recent N articles by id.")
    parser.add_argument(
        "--show-problem-limit",
        type=int,
        default=20,
        help="How many problematic articles to print in console.",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to save full JSON report.",
    )
    parser.add_argument(
        "--verify-files",
        action="store_true",
        help="Check that referenced open-access PDFs exist beneath SAVE_PATH.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    dbc = _build_connector()
    report = _build_report(
        dbc,
        limit=args.limit if args.limit > 0 else None,
        verify_files=args.verify_files,
        save_path=os.getenv("SAVE_PATH", ""),
    )
    _print_console_report(report, show_problem_limit=max(args.show_problem_limit, 1))

    if args.json_out:
        output_path = os.path.abspath(args.json_out)
        with open(output_path, "w", encoding="utf-8") as outfile:
            json.dump(report, outfile, ensure_ascii=False, indent=2)
        print(f"\nSaved JSON report: {output_path}")


if __name__ == "__main__":
    main()
