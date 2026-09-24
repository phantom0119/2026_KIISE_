#!/usr/bin/env python3
"""P3-A: combine official Wikimedia user pageviews with revision timestamps."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


PAGES = (
    "Kubernetes", "Flask_(web_framework)", "PostgreSQL", "Elasticsearch", "Redis", "Neo4j",
    "Docker_(software)", "Retrieval-augmented_generation", "Large_language_model", "Vector_database",
    "ChatGPT", "Qdrant",
)
START_API = "2025080100"
END_API = "2026073100"
START_ISO = "2025-08-01T00:00:00Z"
END_ISO = "2026-07-31T23:59:59Z"
EXPOSURE_SECONDS = 0.062469
USER_AGENT = "FreshEvidenceDB-P3/0.1 academic-research"


def get_json(session: requests.Session, url: str, params=None) -> tuple[dict, str]:
    for attempt in range(8):
        response = session.get(url, params=params, timeout=60)
        if response.status_code == 200:
            return response.json(), response.url
        if response.status_code in (429, 500, 502, 503, 504):
            retry_after = float(response.headers.get("retry-after", 0) or 0)
            time.sleep(min(30.0, max(retry_after + 1.0, 2.0 + attempt * 2.0)))
            continue
        response.raise_for_status()
    raise RuntimeError(f"request failed after retries: {url}")


def fetch_revisions(session: requests.Session, page: str) -> tuple[list[dict], list[dict]]:
    params = {
        "action": "query", "format": "json", "formatversion": "2", "prop": "revisions",
        "titles": page, "rvprop": "ids|timestamp", "rvlimit": "max",
        "rvstart": END_ISO, "rvend": START_ISO,
    }
    revisions, raw_pages = [], []
    while True:
        payload, url = get_json(session, "https://en.wikipedia.org/w/api.php", params=params)
        raw_pages.append({"url": url, "payload": payload})
        pages = payload.get("query", {}).get("pages", [])
        if pages and not pages[0].get("missing"):
            revisions.extend(pages[0].get("revisions", []))
        if "continue" not in payload:
            break
        params.update(payload["continue"])
    return revisions, raw_pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.output_dir.resolve(); raw_dir = out / "raw"; raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session(); session.headers.update({"User-Agent": USER_AGENT})
    daily_rows, summaries = [], []
    for page in PAGES:
        raw_path = raw_dir / f"{page.replace('/', '_')}.json"
        if raw_path.exists():
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            pv = raw["pageview_response"]
            revision_raw = raw["revision_responses"]
            revisions = []
            for response in revision_raw:
                pages = response["payload"].get("query", {}).get("pages", [])
                if pages and not pages[0].get("missing"):
                    revisions.extend(pages[0].get("revisions", []))
            raw_text = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        else:
            encoded = quote(page, safe="")
            pv_url = (
                "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
                f"en.wikipedia.org/all-access/user/{encoded}/daily/{START_API}/{END_API}"
            )
            pv, resolved_url = get_json(session, pv_url)
            revisions, revision_raw = fetch_revisions(session, page)
            raw = {
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "page": page, "pageview_url": resolved_url, "pageview_response": pv,
                "revision_responses": revision_raw,
            }
            raw_text = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            raw_path.write_text(raw_text + "\n", encoding="utf-8")
        views = {item["timestamp"][:8]: int(item["views"]) for item in pv.get("items", [])}
        edits = Counter(item["timestamp"][:10].replace("-", "") for item in revisions)
        page_expected = 0.0
        for day, count in sorted(views.items()):
            expected = edits[day] * count / 86400.0 * EXPOSURE_SECONDS
            page_expected += expected
            daily_rows.append({
                "page": page, "day_utc": day, "user_views": count, "revisions": edits[day],
                "expected_unsafe_observations": expected,
            })
        summaries.append({
            "page": page, "page_days": len(views), "total_user_views": sum(views.values()),
            "mean_views_day": sum(views.values()) / len(views) if views else 0,
            "peak_views_day": max(views.values()) if views else 0,
            "revisions": len(revisions), "days_with_revisions": sum(v > 0 for v in edits.values()),
            "expected_unsafe_observations_year": page_expected,
            "raw_sha256": hashlib.sha256(raw_text.encode()).hexdigest(),
        })
        print(json.dumps(summaries[-1], sort_keys=True), flush=True)
        time.sleep(1.5)

    valid = [row for row in summaries if row["page_days"] >= 300]
    total_expected = sum(row["expected_unsafe_observations_year"] for row in summaries)
    gate = (
        len(valid) >= 8 and sum(row["page_days"] for row in summaries) >= 2400
        and sum(row["revisions"] for row in summaries) >= 50
        and total_expected >= 1.0
        and sum(row["expected_unsafe_observations_year"] >= 0.05 for row in summaries) >= 3
    )
    aggregate = {
        "period": [START_ISO, END_ISO], "exposure_seconds_per_update": EXPOSURE_SECONDS,
        "pages": summaries, "valid_pages": len(valid),
        "page_days": sum(row["page_days"] for row in summaries),
        "total_user_views": sum(row["total_user_views"] for row in summaries),
        "total_revisions": sum(row["revisions"] for row in summaries),
        "total_expected_unsafe_observations": total_expected,
        "pages_at_or_above_0_05": sum(row["expected_unsafe_observations_year"] >= 0.05 for row in summaries),
        "T1": "TRACE_APPLICABILITY_PASS" if gate else "TRACE_LOW_INCIDENT_OR_AGGREGATION_LIMIT",
        "limitation": "Daily aggregate actual views; within-day query arrivals are assumed uniform/Poisson.",
    }
    with (out / "daily_trace.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(daily_rows[0])); writer.writeheader(); writer.writerows(daily_rows)
    with (out / "page_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0])); writer.writeheader(); writer.writerows(summaries)
    (out / "aggregate.json").write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# P3-A Wikimedia 실측 trace 자동 보고", "", f"- T1: **{aggregate['T1']}**",
        f"- page/day: {aggregate['valid_pages']} / {aggregate['page_days']:,}",
        f"- 실제 user views: {aggregate['total_user_views']:,}", f"- 실제 revisions: {aggregate['total_revisions']:,}",
        f"- 예상 unsafe observations/year: {total_expected:.4f}", "",
        "| page | views | revisions | expected/year |", "|---|---:|---:|---:|",
    ]
    for row in sorted(summaries, key=lambda x: x["expected_unsafe_observations_year"], reverse=True):
        lines.append(f"| {row['page']} | {row['total_user_views']:,} | {row['revisions']} | {row['expected_unsafe_observations_year']:.4f} |")
    lines.extend(["", "실제 개별 query timestamp가 아니라 일별 집계에 일중 uniform arrival을 적용한 기대값이다."])
    (out / "AUTO_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"T1": aggregate["T1"], "expected": total_expected}, sort_keys=True))


if __name__ == "__main__":
    main()
