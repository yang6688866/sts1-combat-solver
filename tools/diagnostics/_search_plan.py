"""Ask the real native search what it plans in a recorded Defect state.

The snapshot is rebuilt from a recorded card_play record (which carries the
pre-play hand, energy, focus and orbs), so the plan can be compared with what
the solver actually did in game. The log's shorthand intents are mapped back to
the engine's move ids; anything unmapped aborts instead of guessing.
"""
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _barrage_damage import build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'candidates/sts-ironclad-agent/runtime'
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent'))
sys.path.insert(0, str(RUNTIME / 'engine'))
import slaythespire as sts  # noqa: E402
from steam.steam_mcts import MOVE_NAMES  # noqa: E402

native = importlib.import_module('live_combat_search')

# Raw Java move numbers, mapped through the same table the live importer uses so
# a wrong move can never silently fake a plan. Extend per monster as needed.
INTENT = {
    ('Nemesis', 'ATTACK'): 2,
    ('Nemesis', 'ATTACK_DEBUFF'): 3,
    ('Nemesis', 'DEBUFF'): 4,
}


def name_of(card):
    return str(card.id).replace('CardId.', '')


def main():
    path = Path(sys.argv[1])
    floor, turn = int(sys.argv[2]), int(sys.argv[3])
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
    records = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    rec = next(r for r in records
               if r.get('floor') == floor and r.get('turn') == turn
               and r.get('kind') == 'card_play'
               and any(c.startswith('Barrage') for c in (r.get('hand') or [])))
    moved = {}
    for m in rec['monsters']:
        moved[m['id']] = INTENT[(m['id'], m['intent'])]
    patched = dict(rec, monsters=[dict(m, move_id=moved[m['id']]) for m in rec['monsters']])
    bc = build(patched)
    for m, src in zip(bc.monsters, rec['monsters']):
        if int(m.move_id) == 0:
            raise SystemExit(f"move id did not take for {src['id']}")
    print(f"floor {floor} turn {turn}: energy {rec['energy']} focus {rec.get('focus')} "
          f"orbs {[o.get('id') for o in rec.get('orbs') or []]}")
    print('hand:', rec['hand'])
    print('in-game play:', rec['card'])
    plan = dict(native.plan_reusing(bc, budget, 12.0))
    print('plan keys:', sorted(plan))
    print('outcome', plan.get('outcome'), 'value', plan.get('value'))
    replay = bc.clone()
    for step, bits in enumerate(plan['actions'], 1):
        idx = (bits >> 8) & 0xff
        kind = bits >> 16
        label = ('CARD ' + (name_of(replay.hand[idx]) if idx < len(replay.hand) else '?')) \
            if kind == 0 else ('END TURN' if kind == 3 else f'type={kind}')
        hp0 = [m.cur_hp for m in replay.monsters]
        action = sts.SearchAction.from_bits(bits & 0xffffffff)
        action.execute(replay)
        hp1 = [m.cur_hp for m in replay.monsters]
        print(f'  {step}. {label:26s} energy {replay.player.energy:2d} '
              f'block {replay.player.block:3d} monsters {hp0}->{hp1}')


if __name__ == '__main__':
    main()
