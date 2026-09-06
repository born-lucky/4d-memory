"""Working memory store: two kinds, judged at creation, bad untied from the plan."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fourdmem.store.cas import CAS, oid_hex
from fourdmem.store.kinds import TAU, Kind, classify, jaccard


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_to_cell(digest: bytes, kind: Kind) -> tuple[int, int, int, int]:
    x = digest[0] % 16
    y = digest[1] % 16
    z = digest[2] % 8
    return (x, y, z, kind.w)


def first_line(text: str) -> str:
    return text.strip("\n").split("\n", 1)[0]


@dataclass
class Memory:
    oid: str
    title: str
    text: str
    kind: str
    goal_at_store: str
    w: int
    coord: list[int]
    created_at: str
    landmark: str | None = None

    @property
    def kind_enum(self) -> Kind:
        return Kind(self.kind)


@dataclass
class Plan:
    goal: str
    good: list[str] = field(default_factory=list)
    bad: list[str] = field(default_factory=list)


class Store:
    """Agent-facing harness. Default recall is the plan's good list only."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else Path.cwd() / ".fourdmem"
        self.root.mkdir(parents=True, exist_ok=True)
        self.cas = CAS(self.root)
        self._index_path = self.root / "index.json"
        self._meta_path = self.root / "meta.json"
        self._memories: dict[str, Memory] = {}
        self._goal: str = ""
        self._plans: dict[str, Plan] = {}
        self._load()

    def _load(self) -> None:
        if self._index_path.exists():
            raw = json.loads(self._index_path.read_text(encoding="utf-8"))
            self._memories = {k: Memory(**v) for k, v in raw.get("memories", {}).items()}
            self._plans = {k: Plan(**v) for k, v in raw.get("plans", {}).items()}
        if self._meta_path.exists():
            meta = json.loads(self._meta_path.read_text(encoding="utf-8"))
            self._goal = meta.get("goal", "")

    def _save(self) -> None:
        blob = {
            "memories": {k: asdict(v) for k, v in self._memories.items()},
            "plans": {k: asdict(v) for k, v in self._plans.items()},
        }
        self._index_path.write_text(json.dumps(blob, indent=2, sort_keys=True), encoding="utf-8")
        self._meta_path.write_text(
            json.dumps({"goal": self._goal}, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _plan(self, goal: str) -> Plan:
        if goal not in self._plans:
            self._plans[goal] = Plan(goal=goal)
        return self._plans[goal]

    @property
    def goal(self) -> str:
        return self._goal

    def set_goal(self, text: str) -> str:
        self._goal = text.strip()
        self._plan(self._goal)
        digest = self.cas.put("goal", self._goal.encode("utf-8"))
        self._save()
        return oid_hex(digest)

    def store(
        self,
        text: str,
        *,
        title: str | None = None,
        kind: Kind | str | None = None,
        landmark: str | None = None,
        goal: str | None = None,
    ) -> Memory:
        body = text if text.endswith("\n") else text + "\n"
        goal_at_store = (goal if goal is not None else self._goal).strip()
        if not goal_at_store:
            raise ValueError("set a goal before storing — kind is judged against the creating prompt")
        if kind is None:
            decided = classify(goal_at_store, body)
        else:
            decided = Kind(kind)
        digest = self.cas.put("blob", body.encode("utf-8"))
        hx = oid_hex(digest)
        mem = Memory(
            oid=hx,
            title=title or first_line(body)[:80],
            text=body,
            kind=decided.value,
            goal_at_store=goal_at_store,
            w=decided.w,
            coord=list(hash_to_cell(digest, decided)),
            created_at=_now(),
            landmark=landmark if decided is Kind.GOOD else None,
        )
        # Bad is never tied to the plan graph. Good is.
        plan = self._plan(goal_at_store)
        if decided is Kind.GOOD:
            if hx not in plan.good:
                plan.good.append(hx)
            if hx in plan.bad:
                plan.bad.remove(hx)
        else:
            if hx not in plan.bad:
                plan.bad.append(hx)
            if hx in plan.good:
                plan.good.remove(hx)
            mem.landmark = None
        self._memories[hx] = mem
        self._save()
        return mem

    def judge(self, oid: str, kind: Kind | str) -> Memory:
        mem = self._memories[oid]
        decided = Kind(kind)
        mem.kind = decided.value
        mem.w = decided.w
        mem.coord = [mem.coord[0], mem.coord[1], mem.coord[2], decided.w]
        plan = self._plan(mem.goal_at_store)
        if decided is Kind.GOOD:
            if oid not in plan.good:
                plan.good.append(oid)
            if oid in plan.bad:
                plan.bad.remove(oid)
        else:
            if oid not in plan.bad:
                plan.bad.append(oid)
            if oid in plan.good:
                plan.good.remove(oid)
            mem.landmark = None
        self._save()
        return mem

    def cas_get(self, oid: str) -> bytes:
        _, body = self.cas.get(bytes.fromhex(oid))
        return body

    def recall(
        self,
        *,
        kind: Kind = Kind.GOOD,
        goal: str | None = None,
        cap_lines: int = 32,
    ) -> str:
        """Default kind=good: the plan, unclouded. Bad is a separate explicit call."""
        goal_text = (goal if goal is not None else self._goal).strip()
        if not goal_text:
            return ""
        plan = self._plan(goal_text)
        oids = plan.good if kind is Kind.GOOD else plan.bad
        lines: list[str] = []
        for oid in oids:
            mem = self._memories.get(oid)
            if mem is None:
                continue
            if mem.kind != kind.value:
                continue
            lines.append(f"{mem.title} {oid}")
            lines.append(first_line(mem.text))
            if len(lines) >= cap_lines:
                break
        return "\n".join(lines) + ("\n" if lines else "")

    def status(self) -> dict[str, Any]:
        plan = self._plans.get(self._goal)
        return {
            "goal": self._goal,
            "good": len(plan.good) if plan else 0,
            "bad": len(plan.bad) if plan else 0,
            "tau": TAU,
            "root": str(self.root),
        }

    def score_at_store(self, text: str, goal: str | None = None) -> float:
        g = (goal if goal is not None else self._goal).strip()
        return jaccard(g, text)
