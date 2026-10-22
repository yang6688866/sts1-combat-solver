"""Probe floor 39: attribute the 6-per-monster damage to a specific relic.

Every configuration imports the same snapshot and runs end_turn once; only the
relic bit mask changes, so any damage difference belongs to the removed relic.
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

RELICS = {"CRACKED_CORE": 101, "POCKETWATCH": 54, "MERCURY_HOURGLASS": 40,
          "BAG_OF_PREPARATION": 92, "GIRYA": 109, "SLAVERS_COLLAR": 127,
          "VAJRA": 132, "GOLD_PLATED_CABLES": 110, "MANGO": 146,
          "CALLING_BELL": 135, "STRAWBERRY": 169, "MUMMIFIED_HAND": 41,
          "FOSSILIZED_HELIX": 107}


def rng_view(game_state):
    streams = game_state["full_rng_state"]["streams"]
    out = {}
    for stream_name in COMBAT_STREAMS.values():
        src = streams[stream_name]
        out[stream_name] = {"seed0": int(src["seed0"]) & ((1 << 64) - 1),
                            "seed1": int(src["seed1"]) & ((1 << 64) - 1),
                            "counter": int(src.get("counter") or 0)}
    return out


def clear_relic(battle, value):
    if value < 64:
        battle.player.relicBits0 &= ~(1 << value)
    else:
        battle.player.relicBits1 &= ~(1 << (value - 64))


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    game_state = data["recent_battles"]["current"]["root"]["game_state"]
    comparator = Comparator(AGENT / "runtime" / "engine", AGENT)
    view = {"game": dict(game_state), "rng": rng_view(game_state)}
    view["game"]["seed"] = int(data["seed"]) % (1 << 64)

    def run(label, drop=None, orbs=False, drop_all=False):
        game = dict(view["game"])
        if drop_all:
            game["relics"] = []
        elif drop is not None:
            game["relics"] = [r for r in game.get("relics") or []
                              if (r.get("id") or r.get("name")) != drop]
        if orbs:
            combat = dict(game["combat_state"])
            player = dict(combat["player"])
            player["orbs"] = []
            combat["player"] = player
            game["combat_state"] = combat
        local = {"game": game, "rng": view["rng"]}
        battle = comparator.import_battle(local, require_search_state=True)
        before = [(m.name, m.cur_hp) for m in battle.monsters]
        hp_before = battle.player.cur_hp
        rng_before = {k: v["counter"] for k, v in battle.rng_states.items()}
        end = [a for a in sts.get_legal_actions(battle)
               if a.action_type == sts.SearchActionType.END_TURN][0]
        end.execute(battle)
        after = [(m.name, m.cur_hp, m.alive) for m in battle.monsters]
        rng_after = {k: v["counter"] for k, v in battle.rng_states.items()}
        drained = {k: (rng_before[k], rng_after[k])
                   for k in rng_after if rng_after[k] != rng_before[k]}
        print(f"{label:26s} hp {hp_before}->{battle.player.cur_hp} {after} rng={drained}")

    run("baseline")
    run("no orbs", orbs=True)
    run("no relics at all", drop_all=True)
    for name in RELICS:
        run(f"without {name}", drop=name)


if __name__ == "__main__":
    main()
