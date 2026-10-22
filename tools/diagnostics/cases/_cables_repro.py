"""End the recorded turn with GoldPlatedCables present, to see whether the engine lands 4 hits.

The game's RelicId name for GoldPlatedCables is "Cables".
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/runtime/engine'))
import slaythespire as sts

sys.path.insert(0, str(ROOT / 'tools'))
import repro_floor39 as R  # noqa: E402


def build(record, relic_ids, powers=(), seed=1208793710291554246):
    powers = list(powers)
    relics = []
    for rid in relic_ids:
        relics.append({'id': sts.relic_id_from_name(rid), 'counter': -1})
    snapshot = {
        'character': 'DEFECT',
        'seed': seed,
        'floor': record['floor'],
        'ascension': 1,
        'encounter': int(sts.MonsterEncounter.THREE_SHAPES),
        'turn': record['turn'],
        'player': {'gold': 0, 'current_hp': record['hp'], 'max_hp': record['max_hp'],
                   'block': record['block'], 'energy': record['energy'],
                   'energy_per_turn': 3, 'card_draw_per_turn': 5,
                   'powers': powers,
                   'orb_slots': record.get('orb_slots') or 3,
                   'orbs': [{'id': o.get('id'), 'passive': int(o.get('passive') or 0),
                             'evoke': int(o.get('evoke') or 0)}
                            for o in record.get('orbs') or []]},
        'hand': [R.card(c) for c in record['hand']],
        'draw_pile': [R.card(c) for c in record['draw']],
        'discard_pile': [R.card(c) for c in record['discard']],
        'exhaust_pile': [R.card(c) for c in record.get('exhaust') or []],
        'monsters': [{**R.monster_snap(m),
                      'move': sts.monster_move_id_from_name(R.MOVES[m['id']]),
                      'last_move': sts.monster_move_id_from_name(R.MOVES[m['id']])}
                     for m in record['monsters']],
        'target_map': list(range(len(record['monsters']))),
        'relics': relics,
        'potions': [],
    }
    return sts.BattleContext.from_snapshot(snapshot, snapshot['seed'])


def show(bc, label):
    print(label, [(str(m.id).replace('MonsterId.', ''), m.cur_hp,
                   'alive' if m.alive else 'dead') for m in bc.monsters])


def main():
    path, seed = Path(sys.argv[1]), int(sys.argv[2])
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    rec = [r for r in records if r.get('floor') == 39][-1]
    print('log end_turn:', [(m['id'], m['hp']) for m in rec['monsters']],
          'orbs', [o.get('id') for o in rec.get('orbs') or []])
    for label, relics, powers in (
            ('no relic            ', (), ()),
            ('Cables               ', ('Cables',), ()),
            ('Cables+Focus         ', ('Cables',),
             [{'id': int(sts.player_status_id_from_name('FOCUS')), 'amount': 0,
               'just_applied': False}]),
    ):
        bc = build(rec, relics, powers, seed)
        show(bc, label + ' start:')
        end = [a for a in sts.get_legal_actions(bc)
               if a.action_type == sts.SearchActionType.END_TURN][0]
        end.execute(bc)
        show(bc, label + ' after:')


if __name__ == '__main__':
    main()
