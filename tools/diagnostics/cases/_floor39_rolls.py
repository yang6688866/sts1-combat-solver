"""Log each lightning passive's chosen target at floor 39.

The damage totals match between game and engine only if the random-target rolls
agree; printing every roll (range, index, monster) shows where they diverge.
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


MASK = (1 << 64) - 1


def xorshift(seed0, seed1):
    s1, s0 = seed0, seed1
    seed0 = s0
    s1 = (s1 ^ (s1 << 23)) & MASK
    seed1 = (s1 ^ s0 ^ (s1 >> 17) ^ (s0 >> 26)) & MASK
    return seed0, seed1, (seed1 + s0) & MASK


def draw(seed0, seed1, n):
    while True:
        seed0, seed1, out = xorshift(seed0, seed1)
        bits = out >> 1
        value = bits % n
        if bits - value + n - 1 < (1 << 63):
            return seed0, seed1, value


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    view = load_view(data)
    start = view["rng"]["cardRandomRng"]
    s0, s1 = start["seed0"], start["seed1"]
    print(f"card_random seed {s0} {s1} counter {start['counter']}")
    print("rolls with range 4 (all four alive):")
    a, b = s0, s1
    for i in range(6):
        a, b, v = draw(a, b, 4)
        print(f"  draw {i}: {v}")
    print("rolls with range 3 (one dead):")
    a, b = s0, s1
    for i in range(6):
        a, b, v = draw(a, b, 3)
        print(f"  draw {i}: {v}")

    comparator = Comparator(AGENT / "runtime" / "engine", AGENT)
    battle = comparator.import_battle(view, require_search_state=True)
    print("\nmonsters at import:", [(i, m.name, m.cur_hp, m.alive, m.half_dead)
                                    for i, m in enumerate(battle.monsters)])
    print("monsters alive:", battle.monsters.get_alive_count())
    end = [x for x in sts.get_legal_actions(battle)
           if x.action_type == sts.SearchActionType.END_TURN][0]
    end.execute(battle)
    print("after:", [(m.name, m.cur_hp, m.alive, m.half_dead) for m in battle.monsters])
    print("player hp", battle.player.cur_hp)


if __name__ == "__main__":
    main()
