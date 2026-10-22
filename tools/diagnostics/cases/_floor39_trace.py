"""Trace every queued action during end_turn at floor 39.

The damage pattern (every monster losing 6 while the player loses 16) does not
match a single lightning passive, so the queue itself is the evidence: print each
action as it runs, in order, with the monster HP deltas it caused.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "candidates" / "sts-ironclad-agent"
sys.path[:0] = [str(AGENT / "runtime" / "engine"), str(AGENT), str(AGENT / "steam"),
                str(AGENT / "sim_patch" / "alignment" / "tests"),
                str(AGENT / "sim_patch" / "parity")]

import slaythespire as sts  # noqa: E402
from steam.rng_contract import COMBAT_STREAMS  # noqa: E402
from sim_patch.parity.adapter import Comparator  # noqa: E402

DATA = Path(r"C:\Users\yang\Desktop\sts1-dev-defect"
            r"\sts1-state_divergence-1208793710291554246-F39-v0.9.1-1021-2230.json")


def load_view(data):
    game_state = data["recent_battles"]["current"]["root"]["game_state"]
    streams = game_state["full_rng_state"]["streams"]
    rng = {name: {"seed0": int(streams[name]["seed0"]) & ((1 << 64) - 1),
                  "seed1": int(streams[name]["seed1"]) & ((1 << 64) - 1),
                  "counter": int(streams[name].get("counter") or 0)}
           for name in COMBAT_STREAMS.values()}
    view = {"game": dict(game_state), "rng": rng}
    view["game"]["seed"] = int(data["seed"]) % (1 << 64)
    return view


def snapshot(battle):
    return (battle.player.cur_hp, [(m.name, m.cur_hp, m.alive) for m in battle.monsters])


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    comparator = Comparator(AGENT / "runtime" / "engine", AGENT)
    battle = comparator.import_battle(load_view(data), require_search_state=True)
    print("start", snapshot(battle))

    end = [a for a in sts.get_legal_actions(battle)
           if a.action_type == sts.SearchActionType.END_TURN][0]
    # Pending actions live on the battle context; draining them one at a time
    # shows the real order instead of one opaque end_turn call.
    end.execute(battle)
    print("after end_turn()", snapshot(battle))

    steps = 0
    while getattr(battle, "action_queue", None) and not battle.action_queue.empty() and steps < 200:
        prev = snapshot(battle)
        battle.action_queue.pop().execute(battle)
        steps += 1
        cur = snapshot(battle)
        if cur != prev:
            print(f"  step {steps:3d} hp {prev[0]}->{cur[0]}  {prev[1]} -> {cur[1]}")
    print("drained", steps, "actions", snapshot(battle))


if __name__ == "__main__":
    main()
