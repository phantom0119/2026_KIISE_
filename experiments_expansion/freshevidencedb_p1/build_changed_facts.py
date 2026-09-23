#!/usr/bin/env python3
"""Extract deterministic changed-fact cloze items from locked P1-A pairs."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
from pathlib import Path

from build_revision_pairs import normalize, sha256_text


TARGET = 25
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.:/-]*|\d+(?:\.\d+)*|[^\w\s]", re.UNICODE)


def git_show(repo: Path, revision: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return normalize(result.stdout.decode("utf-8", errors="strict"))


def answer_priority(tokens: list[str]) -> tuple[int, int]:
    text = " ".join(tokens)
    has_number_or_identifier = bool(re.search(r"\d|[_./:-]|[A-Z]{2,}", text))
    return (0 if has_number_or_identifier else 1, len(text))


def candidate_for_pair(old_text: str, new_text: str) -> dict | None:
    old_tokens = TOKEN_RE.findall(old_text)
    new_tokens = TOKEN_RE.findall(new_text)
    matcher = difflib.SequenceMatcher(a=old_tokens, b=new_tokens, autojunk=False)
    candidates = []
    old_lower = old_text.casefold()
    new_lower = new_text.casefold()
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "replace":
            continue
        old_answer_tokens = old_tokens[i1:i2]
        new_answer_tokens = new_tokens[j1:j2]
        if not (1 <= len(old_answer_tokens) <= 4 and 1 <= len(new_answer_tokens) <= 4):
            continue
        old_answer = " ".join(old_answer_tokens).strip()
        new_answer = " ".join(new_answer_tokens).strip()
        if old_answer.casefold() == new_answer.casefold():
            continue
        if not (2 <= len(old_answer) <= 60 and 2 <= len(new_answer) <= 60):
            continue
        if not re.search(r"[A-Za-z0-9]", old_answer) or not re.search(r"[A-Za-z0-9]", new_answer):
            continue
        if old_answer.casefold() in new_lower or new_answer.casefold() in old_lower:
            continue
        left = max(0, j1 - 24)
        right = min(len(new_tokens), j2 + 24)
        prefix = " ".join(new_tokens[left:j1]).strip()
        suffix = " ".join(new_tokens[j2:right]).strip()
        question = f"{prefix} ____ {suffix}".strip()
        new_evidence = " ".join(new_tokens[left:right]).strip()
        old_left = max(0, i1 - 24)
        old_right = min(len(old_tokens), i2 + 24)
        old_evidence = " ".join(old_tokens[old_left:old_right]).strip()
        if len(question) < 30 or len(old_evidence) < 20 or len(new_evidence) < 20:
            continue
        candidates.append(
            {
                "old_answer": old_answer,
                "new_answer": new_answer,
                "question": question,
                "old_evidence": old_evidence,
                "new_evidence": new_evidence,
                "priority": answer_priority(new_answer_tokens),
            }
        )
    if not candidates:
        return None
    candidates.sort(key=lambda item: item["priority"])
    result = dict(candidates[0])
    result.pop("priority")
    result["old_evidence_sha256"] = sha256_text(result["old_evidence"])
    result["new_evidence_sha256"] = sha256_text(result["new_evidence"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads(args.revision_manifest.read_text(encoding="utf-8"))
    payload = {"schema_version": 1, "facts_per_domain": TARGET, "domains": {}}
    for domain, data in source["domains"].items():
        repo = Path(data["repo_path"])
        facts = []
        for pair in data["pairs"]:
            old_text = git_show(repo, pair["parent"], pair["path"])
            new_text = git_show(repo, pair["commit"], pair["path"])
            fact = candidate_for_pair(old_text, new_text)
            if fact is None:
                continue
            fact.update(
                {
                    "fact_id": len(facts),
                    "source_doc_id": pair["doc_id"],
                    "probe": f"answerprobe{domain}{len(facts):04d}",
                    "commit": pair["commit"],
                    "parent": pair["parent"],
                    "path": pair["path"],
                }
            )
            facts.append(fact)
            if len(facts) == TARGET:
                break
        if len(facts) != TARGET:
            raise RuntimeError(f"{domain}: only {len(facts)} changed facts, need {TARGET}")
        payload["domains"][domain] = {"repo_path": str(repo), "facts": facts}
        print(f"{domain}: {len(facts)} facts", flush=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
