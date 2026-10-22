"""Rebuild the recorded floor-39 end-turn and print each monster's hp.

The game logs a pile bottom first, so a pile's last entry is its top card.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/runtime/engine'))
import slaythespire as sts

ALIASES = {'Strike_B': 'STRIKE_BLUE', 'Defend_B': 'DEFEND_BLUE', 'Zap': 'ZAP',
           'Dualcast': 'DUALCAST', 'Glacier': 'GLACIER', 'Reboot': 'REBOOT',
           'Injury': 'INJURY', 'Slimed': 'SLIMED', 'Self Repair': 'SELF_REPAIR',
           'Machine Learning': 'MACHINE_LEARNING', 'Echo Form': 'ECHO_FORM',
           'Biased Cognition': 'BIASED_COGNITION', 'Capacitor': 'CAPACITOR',
           'Chill': 'CHILL', 'Dazed': 'DAZED', 'Steam': 'STEAM_BARRIER',
           'Biased Cognition+': 'BIASED_COGNITION', 'Capacitor+': 'CAPACITOR',
           'Coolheaded+': 'COOLHEADED', 'Consume+': 'CONSUME',
           'Defragment+': 'DEFRAGMENT', 'Double Energy+': 'DOUBLE_ENERGY',
           'Echo Form+': 'ECHO_FORM', 'Machine Learning+': 'MACHINE_LEARNING',
           'Recycle+': 'RECYCLE', 'Turbo+': 'TURBO', 'Buffer+': 'BUFFER',
           'CurseOfTheBell': 'CURSE_OF_THE_BELL', 'Purity': 'PURITY',
           'Writhe': 'WRITHE', 'Sunder': 'SUNDER', 'Defragment': 'DEFRAGMENT',
           'Machine Learning': 'MACHINE_LEARNING'}

MONSTERS = {'Exploder': 'EXPLODER', 'Spiker': 'SPIKER', 'Repulsor': 'REPULSOR'}


def up_of(name):
    return 1 if name.endswith('+') else 0


def card(name):
    base = ALIASES.get(name, name.replace('+', ''))
    base = ALIASES.get(base, base.replace(' ', '_').upper())
    return {'id': int(sts.card_id_from_name(base)), 'upgrades': up_of(name),
            'cost': 1, 'misc': 0}


MOVES = {'Exploder': 'EXPLODER_SLAM', 'Spiker': 'SPIKER_CUT', 'Repulsor': 'REPULSOR_BASH'}


def monster_snap(m):
    mid = int(sts.monster_id_from_name(MONSTERS.get(m['id'], m['id'].upper())))
    mv = int(sts.monster_move_id_from_name(MOVES[m['id']]))
    return {'id': mid, 'current_hp': m['hp'], 'max_hp': m['hp'], 'block': 0,
            'half_dead': False, 'is_gone': False,
            'move': mv, 'last_move': mv, 'powers': []}


LOOP_LAYERS = int(sys.argv[2]) if len(sys.argv) > 2 else 0


def build(record):
    powers = []
    if LOOP_LAYERS:
        powers.append({'id': int(sts.player_status_id_from_name('LOOP')),
                       'amount': LOOP_LAYERS, 'just_applied': False})
    snapshot = {
        'character': 'DEFECT',
        'seed': 1208793710291554246,
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
        'hand': [card(c) for c in record['hand']],
        'draw_pile': [card(c) for c in record['draw']],
        'discard_pile': [card(c) for c in record['discard']],
        'exhaust_pile': [card(c) for c in record.get('exhaust') or []],
        'monsters': [monster_snap(m) for m in record['monsters']],
        'target_map': list(range(len(record['monsters']))),
        'relics': [],
        'potions': [],
    }
    return sts.BattleContext.from_snapshot(snapshot, snapshot['seed'])


def show(bc, label):
    print(label, [(str(m.id).replace('MonsterId.', ''), m.cur_hp,
                   'alive' if m.alive else 'dead') for m in bc.monsters])


def main():
    path = Path(sys.argv[1])
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    record = records[-1]
    print('record:', record['kind'], f"floor {record['floor']} turn {record['turn']}")
    print('log monsters:', [(m['id'], m['hp']) for m in record['monsters']])
    bc = build(record)
    show(bc, 'engine       :')
    print('turn:', bc.turn, 'orbs:', list(bc.player.orbs), 'focus:', bc.player.focus)
    # end the turn: the game resolves orb passives at end of turn
    end = [a for a in sts.get_legal_actions(bc)
           if a.action_type == sts.SearchActionType.END_TURN]
    if not end:
        print('no END_TURN action available')
        return
    end[0].execute(bc)
    show(bc, 'after end    :')


if __name__ == '__main__':
    main()
