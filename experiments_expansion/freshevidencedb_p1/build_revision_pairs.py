#!/usr/bin/env python3
"""Build locked real-document revision pairs for FreshEvidenceDB P1-A."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TARGET_PAIRS = 100
MIN_CHARS = 200
MAX_CHARS = 100_000
MAX_CHUNKS = 128


@dataclass(frozen=True)
class RepoSpec:
    name: str
    path: Path
    doc_root: str
    extensions: tuple[str, ...]
    expected_head: str


def run_git(repo: Path, args: Iterable[str], *, text: bool = True) -> str | bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.decode("utf-8", errors="strict") if text else proc.stdout


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Hugo front matter is metadata, not evidence content.
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            text = text[end + 5 :]
    return text.strip()


def split_long(text: str, width: int = 800) -> list[str]:
    return [text[start : start + width].strip() for start in range(0, len(text), width) if text[start : start + width].strip()]


def chunks(text: str) -> list[str]:
    paragraphs = [re.sub(r"\s+", " ", part).strip() for part in re.split(r"\n\s*\n", normalize(text))]
    paragraphs = [part for part in paragraphs if part]
    merged: list[str] = []
    pending = ""
    for part in paragraphs:
        if pending:
            part = f"{pending} {part}".strip()
            pending = ""
        if len(part) < 40:
            pending = part
            continue
        merged.extend(split_long(part))
    if pending:
        if merged:
            merged[-1] = f"{merged[-1]} {pending}".strip()
        else:
            merged.append(pending)
    return merged


def candidate_commits(spec: RepoSpec) -> list[str]:
    output = run_git(
        spec.path,
        ["log", "--no-merges", "--format=%H", "--", spec.doc_root],
    )
    return [line.strip() for line in output.splitlines() if line.strip()]


def changed_paths(spec: RepoSpec, parent: str, commit: str) -> list[str]:
    output = run_git(
        spec.path,
        ["diff-tree", "--no-commit-id", "--name-status", "-r", parent, commit, "--", spec.doc_root],
    )
    paths = []
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) == 2 and fields[0] == "M" and fields[1].lower().endswith(spec.extensions):
            paths.append(fields[1])
    return sorted(paths)


def show_text(repo: Path, revision: str, path: str) -> str | None:
    try:
        raw = run_git(repo, ["show", f"{revision}:{path}"], text=False)
        return raw.decode("utf-8", errors="strict")
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        return None


def build_pairs(spec: RepoSpec) -> list[dict]:
    head = run_git(spec.path, ["rev-parse", "HEAD"]).strip()
    if head != spec.expected_head:
        raise RuntimeError(f"{spec.name}: HEAD drifted: {head} != {spec.expected_head}")
    pairs: list[dict] = []
    seen = set()
    for commit in candidate_commits(spec):
        if len(pairs) >= TARGET_PAIRS:
            break
        try:
            parent = run_git(spec.path, ["rev-parse", f"{commit}^"]).strip()
        except subprocess.CalledProcessError:
            continue
        for path in changed_paths(spec, parent, commit):
            key = (commit, path)
            if key in seen:
                continue
            old_text = show_text(spec.path, parent, path)
            new_text = show_text(spec.path, commit, path)
            if old_text is None or new_text is None:
                continue
            old_text = normalize(old_text)
            new_text = normalize(new_text)
            if not (MIN_CHARS <= len(old_text) <= MAX_CHARS and MIN_CHARS <= len(new_text) <= MAX_CHARS):
                continue
            old_chunks = chunks(old_text)
            new_chunks = chunks(new_text)
            if not old_chunks or not new_chunks or old_chunks == new_chunks:
                continue
            if len(old_chunks) > MAX_CHUNKS or len(new_chunks) > MAX_CHUNKS:
                continue
            pair_id = len(pairs)
            pairs.append(
                {
                    "doc_id": pair_id,
                    "probe": f"freshprobe{spec.name}{pair_id:04d}",
                    "commit": commit,
                    "parent": parent,
                    "path": path,
                    "old_sha256": sha256_text(old_text),
                    "new_sha256": sha256_text(new_text),
                    "old_chars": len(old_text),
                    "new_chars": len(new_text),
                    "old_chunks": len(old_chunks),
                    "new_chunks": len(new_chunks),
                    "changed_chunk_symmetric_difference": len(set(old_chunks) ^ set(new_chunks)),
                }
            )
            seen.add(key)
            break
    if len(pairs) != TARGET_PAIRS:
        raise RuntimeError(f"{spec.name}: only {len(pairs)} valid revision pairs, need {TARGET_PAIRS}")
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    base = args.base_dir.resolve()
    specs = [
        RepoSpec(
            name="flask",
            path=base / "flask",
            doc_root="docs",
            extensions=(".rst", ".md"),
            expected_head="6a2f545bfd8ed31e19066a299296917e034aca58",
        ),
        RepoSpec(
            name="kubernetes",
            path=base / "kubernetes-website",
            doc_root="content/en/docs",
            extensions=(".md",),
            expected_head="7ddeae4e0e52ce7dcb0e868106a9c15d8e3b8b02",
        ),
    ]
    payload = {
        "schema_version": 1,
        "selection_rule": "newest non-merge commits; first sorted valid modified path per commit",
        "target_pairs_per_domain": TARGET_PAIRS,
        "domains": {},
    }
    for spec in specs:
        print(f"extracting {spec.name}", flush=True)
        pairs = build_pairs(spec)
        payload["domains"][spec.name] = {
            "repo_path": str(spec.path),
            "head": spec.expected_head,
            "doc_root": spec.doc_root,
            "pairs": pairs,
        }
        print(f"{spec.name}: {len(pairs)} pairs", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
