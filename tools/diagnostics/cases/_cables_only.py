import json, sys
from pathlib import Path
ROOT = Path(r"E:\games\sts1-combat-solver-main")
AGENT = ROOT / "candidates" / "sts-ironclad-agent"
sys.path[:0] = [str(AGENT / "runtime" / "engine"), str(AGENT), str(AGENT / "steam"),
                str(AGENT / "sim_patch" / "alignment" / "tests"), str(AGENT / "sim_patch" / "parity")]
import slaythespire as sts
from steam.rng_contract import COMBAT_STREAMS
from sim_patch.parity.adapter import Comparator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _paths import LOG_DIR  # noqa: E402

DATA = LOG_DIR / "sts1-state_divergence-1208793710291554246-F39-v0.9.1-1021-2230.json"
data = json.loads(DATA.read_text(encoding="utf-8"))
gs = data["recent_battles"]["current"]["root"]["game_state"]
streams = gs["full_rng_state"]["streams"]
rng = {n: {"seed0": int(streams[n]["seed0"]) & ((1<<64)-1),
           "seed1": int(streams[n]["seed1"]) & ((1<<64)-1),
           "counter": int(streams[n].get("counter") or 0)} for n in COMBAT_STREAMS.values()}
game = dict(gs); game["seed"] = int(data["seed"]) % (1<<64)
game["relics"] = [r for r in gs["relics"] if (r.get("id") or r.get("name")) in ("Cables",)]
comp = Comparator(AGENT / "runtime" / "engine", AGENT)
b = comp.import_battle({"game": game, "rng": dict(rng)}, require_search_state=True)
end = [a for a in sts.get_legal_actions(b) if a.action_type == sts.SearchActionType.END_TURN][0]
end.execute(b)
print("Cables-only after:", [(m.id, m.cur_hp) for m in b.monsters])
print("card_random counter:", b.rngs["card_random"].counter if "card_random" in b.rngs else "n/a")

