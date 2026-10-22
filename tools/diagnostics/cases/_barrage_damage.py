"""Play Barrage from a recorded hand and report the damage it actually deals."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _barrage_engine import ALIASES, card  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/runtime/engine'))
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent'))
import slaythespire as sts  # noqa: E402
from steam.steam_mcts import MOVE_NAMES  # noqa: E402


def build(rec):
    monsters = []
    for m in rec['monsters']:
        monsters.append({'id': int(sts.monster_id_from_name(m['id'].upper())),
                         'current_hp': m['hp'], 'max_hp': m.get('max_hp', m['hp']),
                         'block': 0, 'half_dead': False, 'is_gone': False,
                         'move': int(sts.monster_move_id_from_name(
                             MOVE_NAMES.get(('NEMESIS', int(m['move_id'])), 'INVALID'))),
                         'last_move': 0, 'misc_info': 0, 'powers': []})
    snapshot = {
        'character': 'DEFECT', 'seed': 1, 'floor': rec['floor'], 'ascension': 1,
        'encounter': int(sts.MonsterEncounter.THREE_SHAPES), 'turn': rec['turn'],
        'player': {'gold': 0, 'current_hp': rec['hp'], 'max_hp': rec['max_hp'],
                   'block': rec['block'], 'energy': rec['energy'],
                   'energy_per_turn': 3, 'card_draw_per_turn': 5,
                   'powers': ([{'id': sts.player_status_id_from_name('FOCUS'),
                                'amount': int(rec['focus'])}] if rec.get('focus') else []),
                   'orb_slots': rec.get('orb_slots') or 3,
                   'orbs': [{'id': o.get('id'), 'passive': int(o.get('passive') or 0),
                             'evoke': int(o.get('evoke') or 0)}
                            for o in rec.get('orbs') or []]},
        'hand': [card(c) for c in rec['hand']],
        'draw_pile': [card(c) for c in rec['draw']],
        'discard_pile': [card(c) for c in rec['discard']],
        'exhaust_pile': [card(c) for c in rec.get('exhaust') or []],
        'monsters': monsters, 'target_map': list(range(len(monsters))),
        'relics': [], 'potions': [],
    }
    return sts.BattleContext.from_snapshot(snapshot, 1)


def barrage_action(bc):
    for a in sts.get_legal_actions(bc):
        if a.action_type != sts.SearchActionType.CARD or a.source_idx >= len(bc.hand):
            continue
        if 'BARRAGE' in str(bc.hand[a.source_idx].id):
            return a
    return None


def main():
    path = Path(sys.argv[1])
    floor, turn = int(sys.argv[2]), int(sys.argv[3])
    records = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    rec = next(r for r in records
               if r.get('floor') == floor and r.get('turn') == turn
               and any(c.startswith('Barrage') for c in (r.get('hand') or [])))
    before = [m['hp'] for m in rec['monsters']]
    bc = build(rec)
    hp_before = [m.cur_hp for m in bc.monsters if m.alive]
    action = barrage_action(bc)
    if action is None:
        print('Barrage not offered')
        return
    print('energy', rec['energy'], 'focus', rec.get('focus'),
          'orbs', [o.get('id') for o in rec.get('orbs') or []])
    print('Barrage offered as action', action)
    # Barrage's damage number is whatever it will hit for; the engine settles
    # queue effects when the action executes.
    action.execute(bc)
    hp_after = [m.cur_hp for m in bc.monsters if m.alive]
    print('monster hp', hp_before, '->', hp_after,
          'damage', sum(hp_before) - sum(hp_after))


if __name__ == '__main__':
    main()
