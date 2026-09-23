#!/usr/bin/env python3
"""Record a compact, repeatable status snapshot for caption-model ablation."""

from __future__ import annotations

import csv
import io
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")
REPORT_ROOT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260715_caption_model_ablation" / "monitoring"
EMBEDDING_ROOT = PROJECT_ROOT / "Qwen3-VL-Embedding" / "aihub_522_embeddings"
FRAME_ROOT = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710" / "frames_src"
MODELS = ("qwen25vl_7b", "qwen3vl_8b", "qwen35_9b")
DATASETS = ("522", "meva", "uca")
GENERATION_SERVICES = (
    "kiise-caption-ablation-generate.service",
    "kiise-caption-ablation-qwen3vl.service",
    "kiise-caption-ablation-qwen35.service",
)
SERVICES = (
    *GENERATION_SERVICES,
    "kiise-caption-ablation-finalize.service",
)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def progress_bar(completed: int, total: int, width: int = 24) -> str:
    ratio = min(1.0, max(0.0, completed / total)) if total else 0.0
    filled = round(width * ratio)
    return f"[{'#' * filled}{'-' * (width - filled)}] {ratio * 100:6.2f}%"


def service_status() -> dict[str, dict[str, str]]:
    statuses = {}
    for service in SERVICES:
        result = run(
            [
                "systemctl",
                "--user",
                "show",
                service,
                "--property=ActiveState,SubState,ExecMainStatus",
            ]
        )
        values = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value
        values["command_status"] = str(result.returncode)
        statuses[service] = values
    return statuses


def gpu_status() -> tuple[list[dict], list[dict]]:
    result = run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu,uuid",
            "--format=csv,noheader,nounits",
        ]
    )
    gpus = []
    if result.returncode == 0:
        for row in csv.reader(io.StringIO(result.stdout)):
            if len(row) != 7:
                continue
            gpus.append(
                {
                    "index": int(row[0].strip()),
                    "name": row[1].strip(),
                    "memory_used_mib": int(row[2].strip()),
                    "memory_total_mib": int(row[3].strip()),
                    "utilization_pct": int(row[4].strip()),
                    "temperature_c": int(row[5].strip()),
                    "uuid": row[6].strip(),
                }
            )

    apps_result = run(
        [
            "nvidia-smi",
            "--query-compute-apps=gpu_uuid,pid,used_memory,process_name",
            "--format=csv,noheader,nounits",
        ]
    )
    apps = []
    if apps_result.returncode == 0:
        for row in csv.reader(io.StringIO(apps_result.stdout)):
            if len(row) != 4:
                continue
            apps.append(
                {
                    "gpu_uuid": row[0].strip(),
                    "pid": int(row[1].strip()),
                    "memory_used_mib": int(row[2].strip()),
                    "process_name": row[3].strip(),
                }
            )
    return gpus, apps


def lane_status(expected: dict[str, int]) -> tuple[list[dict], int]:
    lanes = []
    ready = 0
    for model in MODELS:
        for dataset in DATASETS:
            caption_root = EXPERIMENT_ROOT / model / dataset / "captions"
            generated = sum(count_jsonl(path) for path in caption_root.glob("captions_shard*.jsonl"))
            errors = sum(count_jsonl(path) for path in caption_root.glob("errors_shard*.jsonl"))
            audit_path = caption_root / "caption_output_audit.json"
            audit = read_json(audit_path)
            passed = bool(audit.get("overall_pass")) and audit.get("actual_items") == expected[dataset]
            if passed:
                ready += 1
            lanes.append(
                {
                    "model": model,
                    "dataset": dataset,
                    "expected": expected[dataset],
                    "generated_jsonl_rows": generated,
                    "errors": errors,
                    "audit_pass": passed,
                    "audit_path": str(audit_path),
                }
            )
    return lanes, ready


def embedding_blockers() -> list[dict]:
    blockers = []
    for split in ("train", "val"):
        source = FRAME_ROOT / split
        expected = {
            f"{task.parent.name}_{task.name}"
            for street in source.iterdir()
            if street.is_dir()
            for task in street.iterdir()
            if task.is_dir()
        }
        output = EMBEDDING_ROOT / split
        materialized = {path.stem for path in output.glob("*.pt")}
        completed = len(expected & materialized)
        latest_files = sorted(output.glob("*.pt"), key=lambda path: path.stat().st_mtime, reverse=True)
        latest = latest_files[0] if latest_files else None
        blockers.append(
            {
                "split": split,
                "completed_tasks": completed,
                "total_tasks": len(expected),
                "remaining_tasks": len(expected) - completed,
                "percent": round(100 * completed / len(expected), 2) if expected else 0.0,
                "latest_output": str(latest) if latest else None,
                "latest_output_at": (
                    datetime.fromtimestamp(latest.stat().st_mtime).astimezone().isoformat()
                    if latest
                    else None
                ),
            }
        )
    return blockers


def recent_service_errors() -> list[str]:
    result = run(
        [
            "journalctl",
            "--user",
            "-u",
            SERVICES[0],
            "-u",
            SERVICES[1],
            "-u",
            SERVICES[2],
            "-u",
            SERVICES[3],
            "--since=-35 minutes",
            "--no-pager",
            "-o",
            "cat",
        ]
    )
    pattern = re.compile(r"traceback|\berror\b|failed|out of memory|\boom\b|killed", re.IGNORECASE)
    return [line.strip() for line in result.stdout.splitlines() if pattern.search(line)][-20:]


def delta(current: dict, previous: dict) -> dict:
    previous_blockers = {row["split"]: row for row in previous.get("embedding_blockers", [])}
    blocker_delta = {}
    for row in current["embedding_blockers"]:
        old = previous_blockers.get(row["split"], {})
        blocker_delta[row["split"]] = row["completed_tasks"] - int(old.get("completed_tasks", row["completed_tasks"]))

    previous_lanes = {
        (row["model"], row["dataset"]): row for row in previous.get("lanes", [])
    }
    lane_delta = {}
    for row in current["lanes"]:
        key = (row["model"], row["dataset"])
        old = previous_lanes.get(key, {})
        change = row["generated_jsonl_rows"] - int(
            old.get("generated_jsonl_rows", row["generated_jsonl_rows"])
        )
        if change:
            lane_delta[f"{key[0]}/{key[1]}"] = change
    return {"embedding_tasks": blocker_delta, "caption_rows": lane_delta}


def overall_state(snapshot: dict) -> str:
    if snapshot["final_artifacts"]["verdict_json"]:
        return "finalized"
    if snapshot["recent_service_errors"] or any(row["errors"] for row in snapshot["lanes"]):
        return "attention_required"
    if snapshot["ready_lanes"] == 9:
        return "downstream_processing"
    generators = [snapshot["services"].get(service, {}) for service in GENERATION_SERVICES]
    if any(generator.get("ActiveState") == "active" for generator in generators):
        return "caption_generation"
    if snapshot["ready_lanes"] > 3:
        return "caption_generation"
    return "waiting_for_gpu"


def downstream_ready_lanes() -> int:
    return sum(
        (
            EXPERIMENT_ROOT
            / model
            / dataset
            / "results"
            / "b0_b5"
            / "metrics_dual_summary.csv"
        ).is_file()
        for model in MODELS
        for dataset in DATASETS
    )


def markdown(snapshot: dict) -> str:
    candidate_lanes = [row for row in snapshot["lanes"] if row["model"] != "qwen25vl_7b"]
    candidate_done = sum(min(row["generated_jsonl_rows"], row["expected"]) for row in candidate_lanes)
    candidate_total = sum(row["expected"] for row in candidate_lanes)
    candidate_delta = sum(
        snapshot["delta"]["caption_rows"].get(f"{row['model']}/{row['dataset']}", 0)
        for row in candidate_lanes
    )
    lines = [
        "# VLM 캡션 모델 비교 모니터",
        "",
        f"- 시각: {snapshot['observed_at_kst']}",
        f"- 상태: `{snapshot['state']}`",
        f"- 완료 lane: `{snapshot['ready_lanes']}/9`",
        f"- 최근 서비스 오류: `{len(snapshot['recent_service_errors'])}`",
        "",
        "## 저장량 기반 프로그래스바",
        "",
        "> 행 수와 산출물 존재 여부 기준이며, 남은 시간 비율이 아니다.",
        "",
        "| 범위 | 프로그래스바 | 실제 값 | 최근 구간 증가 |",
        "|---|---|---:|---:|",
        f"| 후속 모델 캡션 전체 | `{progress_bar(candidate_done, candidate_total)}` | "
        f"{candidate_done}/{candidate_total} | {candidate_delta:+d} |",
    ]
    for model in ("qwen3vl_8b", "qwen35_9b"):
        model_lanes = [row for row in snapshot["lanes"] if row["model"] == model]
        done = sum(min(row["generated_jsonl_rows"], row["expected"]) for row in model_lanes)
        total = sum(row["expected"] for row in model_lanes)
        change = sum(
            snapshot["delta"]["caption_rows"].get(f"{row['model']}/{row['dataset']}", 0)
            for row in model_lanes
        )
        lines.append(
            f"| {model} 캡션 | `{progress_bar(done, total)}` | {done}/{total} | {change:+d} |"
        )
    lines.extend(
        [
            f"| 전체 캡션 감사 lane | `{progress_bar(snapshot['ready_lanes'], 9)}` | "
            f"{snapshot['ready_lanes']}/9 | - |",
            f"| canonical/임베딩/검색 lane | `{progress_bar(snapshot['downstream_ready_lanes'], 9)}` | "
            f"{snapshot['downstream_ready_lanes']}/9 | - |",
            f"| 최종 판정 | `{progress_bar(int(snapshot['final_artifacts']['verdict_json']), 1)}` | "
            f"{int(snapshot['final_artifacts']['verdict_json'])}/1 | - |",
            "",
            "## GPU",
            "",
            "| GPU | 메모리 | 사용률 | 온도 | 프로세스 |",
            "|---:|---:|---:|---:|---|",
        ]
    )
    apps_by_uuid: dict[str, list[str]] = {}
    for app in snapshot["gpu_apps"]:
        apps_by_uuid.setdefault(app["gpu_uuid"], []).append(
            f"{app['process_name']} (pid {app['pid']}, {app['memory_used_mib']}MiB)"
        )
    for gpu in snapshot["gpus"]:
        apps = "; ".join(apps_by_uuid.get(gpu["uuid"], [])) or "-"
        lines.append(
            f"| {gpu['index']} | {gpu['memory_used_mib']}/{gpu['memory_total_mib']} MiB | "
            f"{gpu['utilization_pct']}% | {gpu['temperature_c']}C | {apps} |"
        )

    lines.extend(["", "## 병행 Qwen3-VL embedding GPU 작업", "", "| split | 완료 | 진행률 | 30분 증가 | 최근 파일 |", "|---|---:|---:|---:|---|"])
    for row in snapshot["embedding_blockers"]:
        change = snapshot["delta"]["embedding_tasks"].get(row["split"], 0)
        latest = Path(row["latest_output"]).name if row["latest_output"] else "-"
        lines.append(
            f"| {row['split']} | {row['completed_tasks']}/{row['total_tasks']} | "
            f"{row['percent']:.2f}% | {change:+d} | {latest} |"
        )

    lines.extend(
        [
            "",
            "## 캡션 lane",
            "",
            "| 모델 | 데이터셋 | 프로그래스바 | JSONL/예상 | 최근 구간 증가 | 오류 | 감사 |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in snapshot["lanes"]:
        key = f"{row['model']}/{row['dataset']}"
        change = snapshot["delta"]["caption_rows"].get(key, 0)
        lines.append(
            f"| {row['model']} | {row['dataset']} | "
            f"`{progress_bar(row['generated_jsonl_rows'], row['expected'], width=16)}` | "
            f"{row['generated_jsonl_rows']}/{row['expected']} | {change:+d} | {row['errors']} | "
            f"{'PASS' if row['audit_pass'] else 'WAIT'} |"
        )

    if snapshot["recent_service_errors"]:
        lines.extend(["", "## 최근 오류", ""])
        lines.extend(f"- `{line}`" for line in snapshot["recent_service_errors"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    previous = read_json(REPORT_ROOT / "LATEST.json")
    input_manifest = read_json(EXPERIMENT_ROOT / "inputs" / "input_manifest.json")
    expected = {
        dataset: int(input_manifest.get("datasets", {}).get(dataset, {}).get("items", 0))
        for dataset in DATASETS
    }
    gpus, apps = gpu_status()
    lanes, ready = lane_status(expected)
    snapshot = {
        "observed_at_kst": datetime.now().astimezone().isoformat(timespec="seconds"),
        "services": service_status(),
        "gpus": gpus,
        "gpu_apps": apps,
        "lanes": lanes,
        "ready_lanes": ready,
        "downstream_ready_lanes": downstream_ready_lanes(),
        "embedding_blockers": embedding_blockers(),
        "recent_service_errors": recent_service_errors(),
        "final_artifacts": {
            "results_md": (REPORT_ROOT.parent / "CAPTION_MODEL_ABLATION_RESULTS.md").is_file(),
            "verdict_json": (REPORT_ROOT.parent / "VERDICT.json").is_file(),
        },
    }
    snapshot["delta"] = delta(snapshot, previous)
    snapshot["state"] = overall_state(snapshot)

    latest_json = REPORT_ROOT / "LATEST.json"
    latest_json.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORT_ROOT / "LATEST.md").write_text(markdown(snapshot), encoding="utf-8")
    with (REPORT_ROOT / "history.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    print(markdown(snapshot), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
