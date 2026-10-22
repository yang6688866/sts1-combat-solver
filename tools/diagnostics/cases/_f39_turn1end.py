import json, sys
from pathlib import Path
ROOT = Path(r"E:\games\sts1-combat-solver-main")
AGENT = ROOT / "candidates" / "sts-ironclad-agent"
sys.path[:0] = [str(AGENT / "runtime" / "engine"), str(AGENT), str(AGENT / "steam"),
                str(AGENT / "sim_patch" / "alignment" / "tests"), str(AGENT / "sim_patch" / "parity")]
import slaythespire as sts
from steam.rng_contract import COMBAT_STREAMS
from sim_patch.parity.adapter import Comparator

DATA = Path(r"C:\Users\yang\Desktop\sts1-dev-defect\sts1-state_divergence-1208793710291554246-F39-v0.9.1-1021-2230.json")
data = json.loads(DATA.read_text(encoding="utf-8"))
gs0 = data["recent_battles"]["current"]["root"]["game_state"]
streams0 = gs0["full_rng_state"]["streams"]
rng = {n: {"seed0": int(streams0[n]["seed0"]) & ((1 << 64) - 1),
           "seed1": int(streams0[n]["seed1"]) & ((1 << 64) - 1),
           "counter": int(streams0[n].get("counter") or 0)} for n in COMBAT_STREAMS.values()}

gs = json.loads(json.dumps(gs0))
gs["seed"] = int(data["seed"]) % (1 << 64)
# REQ:331 state: turn 1, hp 89, Exploder0 at 2 HP, energy 0.
gs["current_hp"] = 89
cs = gs["combat_state"]
cs["turn"] = 1
cs["player"]["current_hp"] = 89
cs["player"]["energy"] = 0
cs["monsters"][0]["current_hp"] = 2

comp = Comparator(AGENT / "runtime" / "engine", AGENT)
b = comp.import_battle({"game": gs, "rng": dict(rng)}, require_search_state=True)
print("BEFORE", [(m.id, m.cur_hp) for m in b.monsters], "player", b.player.cur_hp,
      "orbs", b.player.orbs)
end = [a for a in sts.get_legal_actions(b)
       if a.action_type == sts.SearchActionType.END_TURN][0]
end.execute(b)
print("AFTER ", [(m.id, m.cur_hp) for m in b.monsters], "player", b.player.cur_hp)
print("GAME  ", "[(19,0),(19,24),(50,35),(40,26)] player 89")
