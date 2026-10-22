"""For each card below its usage floor, find its best record and decode the plan.

A card that never gets played may still be cheaper than the plan's own choice in
some spot; this asks the real live search for its best plan at that record and
prints whether the card appears in the first turn of the plan.
"""
import importlib
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
ROOT = TOOLS.parents[1]
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent'))
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/runtime/engine'))

import slaythespire as sts  # noqa: E402
import _card_usage as usage  # noqa: E402
import _plan_cards as planner  # noqa: E402
from _paths import behaviour_logs  # noqa: E402

native = importlib.import_module('live_combat_search')


def load(path):
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]


def decode(replay, bits):
    kind = (bits >> 16) & 0xffff
    if kind == 0:
        idx = (bits >> 8) & 0xff
        return 'CARD ' + str(replay.hand[idx].id).replace('CardId.', '')
    if kind == 3:
        return 'END TURN'
    return f'type={kind}'


def plan_for(rec, costs, budget):
    bc = planner.build(rec, costs)
    actions = dict(native.plan_reusing(bc, budget, 12.0))['actions']
    replay = bc.clone()
    rows = []
    for bits in actions:
        label = decode(replay, bits)
        if replay.outcome != sts.Outcome.UNDECIDED:
            break
        sts.SearchAction.from_bits(bits & 0xffffffff).execute(replay)
        rows.append((label, replay.turn))
    return bc, rows


def main():
    target = sys.argv[1]
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    costs = dict(usage.COSTS)
    hits = []
    for path in behaviour_logs():
        for rec in load(path):
            if rec.get('kind') != 'card_play':
                continue
            hand = rec.get('hand') or []
            if target not in hand:
                continue
            after = sum(costs.get(usage.resolve(c), 1) for c in hand
                        if c != target and not c.endswith('+'))
            hits.append((len(hand), -rec['energy'], after, path, rec))
    hits.sort(key=lambda t: (-t[0], -t[1]))
    print(f'{len(hits)} usable records with {target} in hand')
    shown = set()
    unique = []
    for hit in hits:
        key = (hit[3].name, hit[4]['floor'], hit[4]['turn'])
        if key in shown:
            continue
        shown.add(key)
        unique.append(hit)
    hits = unique
    seen = 0
    skipped = 0
    for nhand, negenergy, after, path, rec in hits:
        if seen >= 3 or skipped >= 12:
            break
        try:
            bc, rows = plan_for(rec, costs, budget)
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            print(f'  skip {path.name} f{rec["floor"]} t{rec["turn"]}: {exc}')
            continue
        seen += 1
        first = [label for label, turn in rows if turn == rec['turn']]
        want = usage.resolve(target).upper().replace(' ', '_')
        used = any(label == f'CARD {want}' for label in first)
        print(f'\n== {path.name} floor {rec["floor"]} turn {rec["turn"]} '
              f'energy {rec["energy"]} focus {rec.get("focus")} '
              f'orbs {[o.get("id") for o in rec.get("orbs") or []]}')
        print('   hand', rec['hand'])
        print('   in-game played', rec['card'], '| plan turn1 uses target:', used)
        print('   plan turn1:', first)
        if '-v' in sys.argv:
            for label, turn in rows:
                print(f'      t{turn} {label}')


if __name__ == '__main__':
    main()
