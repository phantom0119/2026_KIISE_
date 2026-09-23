#!/usr/bin/env python3
"""Create the external-download package for the DBR manuscript.

The archive contains paper-facing experiment results, audit information,
derived workload tables, figure sources, manuscript files, and the scripts
used to generate or verify them. It deliberately excludes model weights,
raw frames, embedding matrices, caches, and obsolete manuscript renderings.
"""

from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
KIISE = WORKSPACE / "2026_KIISE"
PACKAGE_DATE = date(2026, 7, 20)
PACKAGE_STEM = f"kiise_dbr_manuscript_v6_support_results_{PACKAGE_DATE:%Y%m%d}"
OUTPUT = KIISE / "manuscript" / f"{PACKAGE_STEM}.zip"
ARCHIVE_ROOT = Path(PACKAGE_STEM)

MODEL_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".gguf",
    ".h5",
    ".onnx",
    ".pb",
    ".pt",
    ".pth",
    ".safetensors",
    ".tflite",
}
INTERMEDIATE_SUFFIXES = {".npy"}
EXCLUDED_SUFFIXES = MODEL_SUFFIXES | INTERMEDIATE_SUFFIXES | {".log", ".pyc"}
EXCLUDED_PARTS = {
    ".git",
    ".omc",
    "__pycache__",
    "rendered",
    "twocol_fixed_rendered",
}
EXCLUDED_PAPER_ASSET_DIRS = {
    "20260718_editable_docx",
    "20260718_manuscript_content",
}


@dataclass(frozen=True)
class Entry:
    source: Path
    archive_path: Path
    category: str


entries: dict[str, Entry] = {}


def allowed(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return True


def add_file(source: Path, archive_path: Path, category: str) -> None:
    if not allowed(source):
        return
    key = archive_path.as_posix()
    previous = entries.get(key)
    if previous is not None and previous.source.resolve() != source.resolve():
        raise RuntimeError(f"archive path collision: {key}")
    entries[key] = Entry(source=source, archive_path=archive_path, category=category)


def add_tree(source_dir: Path, archive_dir: Path, category: str) -> None:
    if not source_dir.exists():
        raise FileNotFoundError(source_dir)
    for source in sorted(source_dir.rglob("*")):
        if allowed(source):
            add_file(source, archive_dir / source.relative_to(source_dir), category)


def add_workspace_tree(relative_dir: str, category: str) -> None:
    source = WORKSPACE / relative_dir
    add_tree(source, Path(relative_dir), category)


# Current manuscript and the exact figures referenced by it.
for name in [
    "kiise_dbr_manuscript_v6_submission_revision.md",
    "kiise_dbr_manuscript_v6_submission_revision.docx",
    "kiise_dbr_manuscript_v6_submission_revision.pdf",
    "Figure1.png",
]:
    source = KIISE / "manuscript" / name
    add_file(source, Path("2026_KIISE/manuscript") / name, "current_manuscript")

# All paper-facing result and audit assets, except obsolete rendering previews.
paper_assets = KIISE / "paper_assets"
for child in sorted(paper_assets.iterdir()):
    if not child.is_dir() or child.name in EXCLUDED_PAPER_ASSET_DIRS:
        continue
    add_tree(
        child,
        Path("2026_KIISE/paper_assets") / child.name,
        "experiment_results_and_figures",
    )

# Canonical research notes, expansion results, code, and environment records.
for relative, category in [
    ("2026_KIISE/project_md/canonical", "canonical_experiment_notes"),
    ("2026_KIISE/experiments_expansion", "experiment_results"),
    ("2026_KIISE/scripts", "generation_and_verification_scripts"),
    ("2026_KIISE/src", "experiment_source_code"),
    ("2026_KIISE/env", "environment_specification"),
    ("2026_KIISE/infra", "database_environment_specification"),
]:
    add_workspace_tree(relative, category)

# AI Hub intersection workload: derived tables and aggregate results only.
intersection = WORKSPACE / "Datasets/processed/aihub_522_intersection/20260710"
for source in sorted(intersection.iterdir()):
    if source.is_file():
        add_file(
            source,
            Path("Datasets/processed/aihub_522_intersection/20260710") / source.name,
            "derived_workload_information",
        )
for child_name in [
    "caption_quality_pilot",
    "captions",
    "canonical",
    "canonical_trisource",
    "canonical_trisource_expanded",
    "results",
]:
    add_tree(
        intersection / child_name,
        Path("Datasets/processed/aihub_522_intersection/20260710") / child_name,
        "derived_workload_and_results",
    )
for manifest in sorted(intersection.glob("embeddings*/**/*manifest*.json")):
    add_file(
        manifest,
        Path("Datasets/processed/aihub_522_intersection/20260710")
        / manifest.relative_to(intersection),
        "embedding_provenance_only",
    )

# Non-circular VRU-Accident and intelligent-CCTV workloads.
for dataset in ["vru_accident", "aihub_intelligent_cctv"]:
    base = WORKSPACE / f"Datasets/processed/{dataset}/20260710_noncircular"
    for child_name in ["canonical", "results"]:
        add_tree(
            base / child_name,
            Path(f"Datasets/processed/{dataset}/20260710_noncircular") / child_name,
            "derived_workload_and_results",
        )

# UCA derived workload used for the external contrast. No source videos are copied.
uca_source = Path(
    "/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/canonical"
)
add_tree(
    uca_source,
    Path("Datasets/processed/uca_anchor/20260712/canonical"),
    "derived_external_validation_workload",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


records: list[dict[str, str | int]] = []
for key in sorted(entries):
    entry = entries[key]
    records.append(
        {
            "archive_path": key,
            "size_bytes": entry.source.stat().st_size,
            "sha256": digest(entry.source),
            "category": entry.category,
            "original_source": str(entry.source),
        }
    )

total_size = sum(int(record["size_bytes"]) for record in records)
readme = f"""# KIISE DBR 논문 실험 결과·정보 패키지

## 대상 원고

- `2026_KIISE/manuscript/kiise_dbr_manuscript_v6_submission_revision.md`
- 패키지 생성일: {PACKAGE_DATE.isoformat()}

## 포함 범위

- 현재 원고의 Markdown, DOCX, PDF와 원고가 참조하는 그림
- 논문의 표·그림·수치를 작성하거나 검증하는 데 사용한 집계 결과와 감사 자료
- AI Hub 교차로, VRU-Accident, 지능형 CCTV 및 UCA의 파생 질의, 관련성 정답,
  메타데이터, 영상 설명문과 검색 결과
- 그림 생성, 수치 검증, 데이터 구축과 실험 실행에 사용한 스크립트
- 실험 환경 명세, 데이터베이스 구성 파일과 정리된 실험 설명

총 {len(records):,}개 파일, 압축 전 {total_size / 1024 / 1024:.1f} MiB이다.

## 제외 범위

- 모델 가중치와 모델 배포 파일: `.safetensors`, `.bin`, `.pt`, `.pth`, `.ckpt`,
  `.onnx`, `.gguf` 등
- 원본 영상, 추출 프레임과 원천 라벨 디렉터리
- 대용량 임베딩 행렬(`.npy`)과 모델·프레임 캐시
- 가상환경, 에이전트 상태, 로그, 바이트코드와 임시 렌더링 이미지
- 이전 원고 복원본, 편집 중간본, 발표 자료 및 제3자 논문 PDF

이 패키지는 논문 작성과 결과 확인을 위한 자료 묶음이다. 원천 데이터는 각 제공처의
라이선스를 따르며, 모델과 원천 영상이 없으므로 처음부터 모든 모델 추론을 재실행하는
완전 복제 패키지는 아니다.

## 파일 목록과 무결성

- `MANIFEST.tsv`: 파일별 분류, 원래 위치, 크기와 SHA-256
- `SHA256SUMS.txt`: 압축 해제 후 파일 무결성 확인용 체크섬
"""

manifest_buffer = io.StringIO()
writer = csv.DictWriter(
    manifest_buffer,
    fieldnames=[
        "archive_path",
        "size_bytes",
        "sha256",
        "category",
        "original_source",
    ],
    delimiter="\t",
    lineterminator="\n",
)
writer.writeheader()
writer.writerows(records)
manifest = manifest_buffer.getvalue()

generated = {
    "README_KO.md": readme.encode("utf-8"),
    "MANIFEST.tsv": manifest.encode("utf-8"),
}
checksums: list[str] = []
for record in records:
    checksums.append(f"{record['sha256']}  {record['archive_path']}")
for name, content in generated.items():
    checksums.append(f"{hashlib.sha256(content).hexdigest()}  {name}")
generated["SHA256SUMS.txt"] = ("\n".join(checksums) + "\n").encode("utf-8")

if OUTPUT.exists():
    OUTPUT.unlink()
with zipfile.ZipFile(
    OUTPUT, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
) as archive:
    archive.comment = (
        "DBR manuscript experiment results and information; no model weights."
    ).encode("ascii")
    for name, content in generated.items():
        archive.writestr((ARCHIVE_ROOT / name).as_posix(), content)
    for key in sorted(entries):
        entry = entries[key]
        archive.write(entry.source, (ARCHIVE_ROOT / entry.archive_path).as_posix())

print(OUTPUT)
print(f"files={len(records) + len(generated)}")
print(f"uncompressed_mib={(total_size + sum(map(len, generated.values()))) / 2**20:.1f}")
print(f"zip_mib={OUTPUT.stat().st_size / 2**20:.1f}")
