"""Compare Barrage's actual simulated value against the other candidates in a recorded hand."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/runtime/engine'))
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent'))
import slaythespire as sts

sys.path.insert(0, str(ROOT))
from tools._barrage_engine import card, ALIASES  # noqa: E402


def build(path, floor, turn):
    records = [json.loads(l) for l in Path(path).read_text(encoding='utf-8').splitlines() if l.strip()]
    rec = next(r for r in records
               if r.get('floor') == floor and r.get('turn') == turn
               and any(c.startswith('Barrage') for c in (r.get('hand') or [])))
    monsters = []
    for m in rec['monsters']:
        mid = int(sts.monster_id_from_name(m['id'].upper()))
        monsters.append({'id': mid, 'current_hp': m['hp'], 'max_hp': m['hp'], 'block': 0,
                         'half_dead': False, 'is_gone': False,
                         'move': int(sts.monster_move_id_from_name('INVALID')),
                         'last_move': int(sts.monster_move_id_from_name('INVALID')),
                         'powers': []})
    powers = [{'id': int(sts.player_status_id_from_name('FOCUS')), 'amount': int(rec.get('focus') or 0),
               'just_applied': False}] if rec.get('focus') else []
    orb_ids = [o.get('id') for o in rec.get('orbs') or [] if o.get('id')]
    snapshot = {
        'character': 'DEFECT', 'seed': 1, 'floor': floor, 'ascension': 1,
        'encounter': int(sts.MonsterEncounter.INVALID), 'turn': turn,
        'player': {'gold': 0, 'current_hp': rec['hp'], 'max_hp': rec['max_hp'],
                   'block': rec['block'], 'energy': rec['energy'],
                   'energy_per_turn': 3, 'card_draw_per_turn': 5,
                   'powers': powers,
                   'orb_slots': len(orb_ids),
                   'orbs': [{'id': o.get('id'), 'passive': int(o.get('passive') or 0),
                             'evoke': int(o.get('evoke') or 0)}
                            for o in rec.get('orbs') or []]},
        'hand': [card(c) for c in rec['hand']],
        'draw_pile': [card(c) for c in rec['draw']],
        'discard_pile': [card(c) for c in rec['discard']],
        'exhaust_pile': [card(c) for c in rec.get('exhaust') or []],
        'monsters': monsters,
        'target_map': list(range(len(monsters))),
        'relics': [], 'potions': [],
    }
    return snapshot, rec


def name_of(bc, idx):
    if idx < 0 or idx >= len(bc.hand):
        return f'<idx {idx}>'
    return str(bc.hand[idx].id).replace('CardId.', '')


def main():
    path, floor, turn = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    snapshot, rec = build(path, floor, turn)
    bc = sts.BattleContext.from_snapshot(snapshot, 1)
    print('player hp', bc.player.cur_hp, 'energy', bc.player.energy,
          'focus', bc.player.focus, 'orbs', [o['id'] for o in bc.player.orbs])
    print('monsters:', [(str(m.id).replace('MonsterId.', ''), m.cur_hp)
                        for m in bc.monsters])
    print()
    for a in sts.get_legal_actions(bc):
        if a.action_type != sts.SearchActionType.CARD:
            continue
        label = name_of(bc, a.source_idx)
        if a.target_idx >= 0 and a.target_idx < len(bc.monsters):
            label += f' -> {str(bc.monsters[a.target_idx].id).replace("MonsterId.", "")}'
        if 'BARRAGE' not in name_of(bc, a.source_idx):
            continue
        # play it and read the damage that actually landed
        copy = sts.BattleContext.from_snapshot(snapshot, 1)
        before = copy.monsters[0].cur_hp
        sts.play(copy, a)
        after = copy.monsters[0].cur_hp
        print(f'{label}: monster hp {before} -> {after}, damage {before - after}')
        print('  action =', a)


if __name__ == '__main__':
    main()
