"""The product is not a dormant palace. The agent uses it in work."""

from __future__ import annotations

from pathlib import Path

from fourdmem.api import Store
from fourdmem.store.kinds import Kind


HILBERT = "Hilbert encode/decode is a bijection on Lattice4.\n"
CATS = "I saw cats on screen.\n"
GOAL = "prove Hilbert 4D encode/decode is bijective"


def test_good_stays_bad_untied_not_deleted(tmp_path: Path) -> None:
    st = Store(tmp_path / ".fourdmem")
    st.set_goal(GOAL)

    good = st.store(HILBERT, title="Hilbert bijection")
    bad = st.store(CATS, title="cats on screen")

    assert good.kind == Kind.GOOD.value
    assert bad.kind == Kind.BAD.value
    assert good.w == 8
    assert bad.w == -8

    recalled = st.recall()
    assert "Hilbert" in recalled
    assert "cats" not in recalled.lower()

    # Bad is not gone. It is just not tied to the plan.
    assert st.cas_get(bad.oid) == CATS.encode()
    assert "cats" in st.recall(kind=Kind.BAD).lower()
    assert bad.oid not in (st._plans[GOAL].good)
    assert good.oid in st._plans[GOAL].good
    assert good.oid not in st._plans[GOAL].bad


def test_kind_is_creation_goal_not_live_prompt(tmp_path: Path) -> None:
    st = Store(tmp_path / ".fourdmem")
    st.set_goal(GOAL)
    cats = st.store(CATS)
    assert cats.kind == "bad"
    assert cats.goal_at_store == GOAL

    # Switching the live prompt must not retie cats onto a new plan.
    st.set_goal("write a poem about cats")
    assert "cats" not in st.recall().lower()
    assert cats.oid in st._plans[GOAL].bad
    assert cats.oid not in st._plans["write a poem about cats"].good


def test_judge_reties(tmp_path: Path) -> None:
    st = Store(tmp_path / ".fourdmem")
    st.set_goal(GOAL)
    mem = st.store(CATS, kind=Kind.BAD)
    st.judge(mem.oid, Kind.GOOD)
    assert mem.oid in st._plans[GOAL].good
    assert mem.oid not in st._plans[GOAL].bad
    assert "cats" in st.recall().lower()


def test_cas_roundtrip(tmp_path: Path) -> None:
    st = Store(tmp_path / ".fourdmem")
    st.set_goal(GOAL)
    mem = st.store(HILBERT)
    assert st.cas_get(mem.oid) == HILBERT.encode()
