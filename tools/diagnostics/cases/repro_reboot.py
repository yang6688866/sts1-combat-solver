"""Rebuild the recorded Reboot decision and print the reshuffled draw pile.

The game logs a pile bottom first, so a pile's last entry is its top card.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/runtime/engine'))
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/steam'))
import slaythespire as sts
import steam_mcts

ALIASES = {'Strike_B': 'STRIKE_BLUE', 'Defend_B': 'DEFEND_BLUE', 'Zap': 'ZAP',
           'Dualcast': 'DUALCAST', 'Glacier': 'GLACIER', 'Reboot': 'REBOOT',
           'Injury': 'INJURY', 'Slimed': 'SLIMED'}


def card(name):
    return {'id': int(sts.card_id_from_name(ALIASES.get(name, name))),
            'upgrades': 0, 'cost': 1, 'misc': 0}


def build(record):
    monster = {'id': 'Cultist', 'current_hp': record['monsters'][0]['hp'],
               'max_hp': 53, 'block': 0, 'move_id': 1, 'last_move_id': -1, 'powers': []}
    snapshot = {
        'character': 'DEFECT',
        'seed': 12138488402917110601,
        'floor': record['floor'],
        'ascension': 1,
        'encounter': int(sts.MonsterEncounter.CULTIST),
        'turn': record['turn'],
        'player': {'gold': 0, 'current_hp': record['hp'], 'max_hp': record['max_hp'],
                   'block': record['block'], 'energy': record['energy'],
                   'energy_per_turn': 3, 'card_draw_per_turn': 5},
        'hand': [card(c) for c in record['hand']],
        'draw_pile': [card(c) for c in record['draw']],
        'discard_pile': [card(c) for c in record['discard']],
        'exhaust_pile': [card(c) for c in record.get('exhaust') or []],
        'monsters': [steam_mcts.monster_snapshot(monster)],
        'target_map': [0],
        'relics': [],
        'potions': [],
    }
    return sts.BattleContext.from_snapshot(snapshot, snapshot['seed'])


def names(cards):
    return [str(c.id).replace('CardId.', '') for c in cards]


def main():
    path = Path(sys.argv[1])
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    record = records[-1]
    print('record:', record['kind'], record['card'], f"floor {record['floor']} turn {record['turn']}")
    print('log hand    :', record['hand'])
    print('log draw    :', record['draw'], '(last entry is the top)')
    print('log discard :', record['discard'], '(last entry is the top)')
    battle = build(record)
    print()
    print('engine hand    :', names(battle.hand))
    print('engine draw    :', names(battle.draw_pile), '(last entry is the top)')
    print('engine discard :', names(battle.discard_pile), '(last entry is the top)')
    play = [a for a in sts.get_legal_actions(battle) if a.action_type == sts.SearchActionType.CARD]
    target = None
    for action in play:
        if 0 <= action.source_idx < len(battle.hand) and names([battle.hand[action.source_idx]])[0] == 'REBOOT':
            target = action
            break
    if target is None:
        print('Reboot is not playable from this state')
        return
    target.execute(battle)
    print()
    print('after Reboot -> hand :', names(battle.hand))
    print('after Reboot -> draw :', names(battle.draw_pile), '(last entry is the top)')


if __name__ == '__main__':
    main()
