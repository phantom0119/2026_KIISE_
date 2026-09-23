#!/usr/bin/env python3
"""FreshEvidenceDB P2-A: timestamp-calibrated exposure analysis."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import statistics
import subprocess
from pathlib import Path


RATES_QPS = (0.1, 1.0, 10.0, 20.0, 100.0)
PROTOCOLS = ("cross_naive", "cross_read_filter", "cross_staged")


def commit_times(repo: str, commits: list[str]) -> list[int]:
    output = subprocess.check_output(
        ["git", "-C", repo, "show", "-s", "--format=%H %ct", *commits], text=True
    )
    wanted = set(commits)
    mapping = {}
    for line in output.splitlines():
        commit, timestamp = line.split()
        if commit in wanted:
            mapping[commit] = int(timestamp)
    if len(mapping) != len(wanted):
        raise RuntimeError(f"missing commit timestamps: {len(wanted) - len(mapping)}")
    return sorted(set(mapping.values()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision-manifest", required=True, type=Path)
    parser.add_argument("--p1-aggregate", required=True, type=Path)
    parser.add_argument("--p1-repeat-summary", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    revisions = json.loads(args.revision_manifest.read_text(encoding="utf-8"))
    p1 = json.loads(args.p1_aggregate.read_text(encoding="utf-8"))["aggregate"]
    repeat_rows = list(csv.DictReader(args.p1_repeat_summary.open(encoding="utf-8")))
    output = {"domains": {}, "rates_qps": list(RATES_QPS)}
    applicable = False
    for domain, data in revisions["domains"].items():
        timestamps = commit_times(data["repo_path"], [pair["commit"] for pair in data["pairs"]])
        duration_seconds = timestamps[-1] - timestamps[0]
        duration_days = duration_seconds / 86400.0
        update_rate = len(timestamps) / duration_days
        gaps = [right - left for left, right in zip(timestamps, timestamps[1:])]
        domain_result = {
            "unique_commits": len(timestamps),
            "trace_start_utc": dt.datetime.fromtimestamp(timestamps[0], dt.timezone.utc).isoformat(),
            "trace_end_utc": dt.datetime.fromtimestamp(timestamps[-1], dt.timezone.utc).isoformat(),
            "trace_days": duration_days,
            "updates_per_day": update_rate,
            "interarrival_hours_p50": statistics.median(gaps) / 3600.0,
            "interarrival_hours_p95": sorted(gaps)[int(0.95 * (len(gaps) - 1))] / 3600.0,
            "protocols": {},
        }
        for protocol in PROTOCOLS:
            rows = [
                row for row in repeat_rows
                if row["domain"] == domain and row["protocol"] == protocol
            ]
            p50_wave_ms = statistics.mean(float(row["p50_wave_ms"]) for row in rows)
            p95_wave_ms = statistics.mean(float(row["p95_wave_ms"]) for row in rows)
            conditional_error = float(p1[domain][protocol]["answer_error_rate"])
            per_doc_p50_seconds = p50_wave_ms / 1000.0 / 10.0
            per_doc_p95_seconds = p95_wave_ms / 1000.0 / 10.0
            error_seconds_p50 = per_doc_p50_seconds * conditional_error
            error_seconds_p95 = per_doc_p95_seconds * conditional_error
            break_even = math.inf if error_seconds_p50 == 0 else 1.0 / (update_rate * error_seconds_p50)
            if break_even <= 20.0:
                applicable = True
            domain_result["protocols"][protocol] = {
                "conditional_stress_error_rate": conditional_error,
                "per_doc_duration_p50_seconds": per_doc_p50_seconds,
                "per_doc_duration_p95_seconds": per_doc_p95_seconds,
                "error_seconds_per_update_p50": error_seconds_p50,
                "error_seconds_per_update_p95": error_seconds_p95,
                "time_exposure_fraction_p50": update_rate * error_seconds_p50 / 86400.0,
                "time_exposure_fraction_p95": update_rate * error_seconds_p95 / 86400.0,
                "break_even_qps_for_one_error_day": None if math.isinf(break_even) else break_even,
                "expected_errors_per_day": {
                    str(rate): update_rate * error_seconds_p50 * rate for rate in RATES_QPS
                },
            }
        output["domains"][domain] = domain_result
    output["gate_T1"] = "APPLICABLE_HIGH_TRAFFIC" if applicable else "NICHE_OR_BATCH_ONLY"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "exposure.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# FreshEvidenceDB P2-A timestamp-calibrated exposure",
        "",
        f"- T1: **{output['gate_T1']}**",
        "- Git timestamp는 실제지만 query rate는 scenario grid다.",
        "",
        "| domain | updates/day | protocol | error-sec/update | break-even qps | errors/day @20qps |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for domain, data in output["domains"].items():
        for protocol, row in data["protocols"].items():
            break_even = row["break_even_qps_for_one_error_day"]
            break_text = "∞" if break_even is None else f"{break_even:.2f}"
            lines.append(
                f"| {domain} | {data['updates_per_day']:.4f} | {protocol} | "
                f"{row['error_seconds_per_update_p50']:.6f} | {break_text} | "
                f"{row['expected_errors_per_day']['20.0']:.4f} |"
            )
    lines.append("")
    (args.output_dir / "AUTO_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"gate_T1": output["gate_T1"]}, sort_keys=True))


if __name__ == "__main__":
    main()
