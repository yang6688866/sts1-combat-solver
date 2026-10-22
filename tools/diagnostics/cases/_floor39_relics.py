"""Find which relics cause the 3-damage sweep at floor 39.

Single removals all left the sweep intact, which only happens if two or more
relics each deal it. This removes each relic *alone* and reports the sweep,
then removes candidates pairwise to name the pair.
"""
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "candidates" / "sts-ironclad-agent"
sys.path[:0] = [str(AGENT / "runtime" / "engine"), str(AGENT), str(AGENT / "steam"),
                str(AGENT / "sim_patch" / "alignment" / "tests"),
                str(AGENT / "sim_patch" / "parity")]

import slaythespire as sts  # noqa: E402
from steam.rng_contract import COMBAT_STREAMS  # noqa: E402
from sim_patch.parity.adapter import Comparator  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _paths import LOG_DIR  # noqa: E402

DATA = LOG_DIR / "sts1-state_divergence-1208793710291554246-F39-v0.9.1-1021-2230.json"


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


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    base = load_view(data)
    names = [r.get("id") or r.get("name") for r in base["game"]["relics"]]
    comparator = Comparator(AGENT / "runtime" / "engine", AGENT)

    def sweep(kept):
        game = dict(base["game"])
        game["relics"] = [r for r in base["game"]["relics"]
                          if (r.get("id") or r.get("name")) in kept]
        battle = comparator.import_battle({"game": game, "rng": base["rng"]},
                                         require_search_state=True)
        before = [m.cur_hp for m in battle.monsters]
        end = [a for a in sts.get_legal_actions(battle)
               if a.action_type == sts.SearchActionType.END_TURN][0]
        end.execute(battle)
        after = [m.cur_hp for m in battle.monsters]
        return [b - a for b, a in zip(before, after)], battle.player.cur_hp

    print("all relics        ", sweep(set(names)))
    print("no relics         ", sweep(set()))
    print()
    for name in names:
        print(f"only {name:22s}", sweep({name}))
    print()
    for a, b in itertools.combinations(names, 2):
        delta, _ = sweep({a, b})
        if sum(delta) > 3:
            print(f"pair {a}+{b}:", delta)


if __name__ == "__main__":
    main()
