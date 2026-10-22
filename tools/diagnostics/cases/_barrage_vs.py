"""Compare what Barrage does against the cheapest alternative in the same hand."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _barrage_damage import build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/runtime/engine'))
import slaythespire as sts


def name_of(card):
    return str(card.id).replace('CardId.', '')


def offers(bc):
    out = {}
    for a in sts.get_legal_actions(bc):
        if a.action_type != sts.SearchActionType.CARD or a.source_idx >= len(bc.hand):
            continue
        out.setdefault(name_of(bc.hand[a.source_idx]), a)
    return out


def main():
    path = Path(sys.argv[1])
    floor, turn = int(sys.argv[2]), int(sys.argv[3])
    records = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    rec = next(r for r in records
               if r.get('floor') == floor and r.get('turn') == turn
               and any(c.startswith('Barrage') for c in (r.get('hand') or [])))
    base = build(rec)
    print(f"floor {floor} turn {turn}: energy {rec['energy']} focus {rec.get('focus')} "
          f"orbs {[o.get('id') for o in rec.get('orbs') or []]}")
    print('hand:', rec['hand'])
    print()
    for label, action in offers(base).items():
        bc = build(rec)
        acts = offers(bc)
        a = acts.get(label)
        hp0 = sum(m.cur_hp for m in bc.monsters if m.alive)
        energy0 = bc.player.energy
        a.execute(bc)
        hp1 = sum(m.cur_hp for m in bc.monsters if m.alive)
        dealt = hp0 - hp1
        block = bc.player.block
        print(f'  {label:22s} damage {dealt:3d}  block {block - rec["block"]:3d}  '
              f'energy {energy0}->{bc.player.energy}')


if __name__ == '__main__':
    main()
