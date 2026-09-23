#!/usr/bin/env python3
"""P3-D: exhaustive finite-state safety exploration for four artifact types."""

from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path


ARTIFACTS = ("dense", "sparse", "graph", "cache")
FULL = (1 << len(ARTIFACTS)) - 1


@dataclass(frozen=True)
class State:
    active: int = 1
    ready: int = 0
    live_old: bool = True
    coordinator_generation: int = 0


def invariant(state: State) -> tuple[bool, str]:
    if state.active == 1 and not state.live_old:
        return False, "active v1 was garbage-collected"
    if state.active == 2 and state.ready != FULL:
        return False, "active v2 references incomplete artifact set"
    return True, ""


def transitions(state: State, protocol: str):
    for index, name in enumerate(ARTIFACTS):
        bit = 1 << index
        if not state.ready & bit:
            yield f"stage_{name}", State(state.active, state.ready | bit, state.live_old, state.coordinator_generation)
        else:
            yield f"retry_{name}", state
    if state.active == 1 and (protocol == "eager" or state.ready == FULL):
        yield "publish_v2", State(2, state.ready, state.live_old, state.coordinator_generation)
    if state.active == 2 and state.live_old:
        yield "gc_v1", State(2, state.ready, False, state.coordinator_generation)
    yield "coordinator_crash_restart", State(
        state.active, state.ready, state.live_old, min(2, state.coordinator_generation + 1)
    )
    yield "query", state


def explore(protocol: str):
    initial = State()
    queue = deque([initial]); parent = {initial: None}; action = {initial: None}
    violations = []
    while queue:
        state = queue.popleft()
        ok, reason = invariant(state)
        if not ok:
            path = []
            cursor = state
            while parent[cursor] is not None:
                path.append(action[cursor]); cursor = parent[cursor]
            violations.append({"reason": reason, "path": list(reversed(path)), "state": state.__dict__})
            continue
        for event, nxt in transitions(state, protocol):
            if nxt not in parent:
                parent[nxt] = state; action[nxt] = event; queue.append(nxt)
    return {"protocol": protocol, "reachable_states": len(parent), "violations": violations}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(); out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    staged = explore("staged"); eager = explore("eager")
    gate = not staged["violations"] and bool(eager["violations"])
    result = {
        "artifact_types": list(ARTIFACTS), "staged": staged, "eager_sanity": eager,
        "T_state": "STATE_MACHINE_SAFETY_PASS" if gate else "STATE_MACHINE_SAFETY_FAIL",
    }
    (out / "model_check.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# P3-D finite-state 자동 보고", "", f"- 판정: **{result['T_state']}**",
        f"- staged reachable states: {staged['reachable_states']}, violations: {len(staged['violations'])}",
        f"- eager reachable states: {eager['reachable_states']}, violations: {len(eager['violations'])}", "",
    ]
    if eager["violations"]:
        lines.append(f"- eager 최소 반례: `{' → '.join(eager['violations'][0]['path'])}`")
    (out / "AUTO_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"T_state": result["T_state"], "staged_states": staged["reachable_states"], "eager_counterexamples": len(eager["violations"])}))


if __name__ == "__main__":
    main()
