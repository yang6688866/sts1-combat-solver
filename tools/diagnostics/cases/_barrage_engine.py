"""Rebuild a recorded hand that held Barrage and ask the engine for its legal actions."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'candidates/sts-ironclad-agent/runtime/engine'))
import slaythespire as sts

ALIASES = {
    'Strike_B': 'STRIKE_BLUE', 'Defend_B': 'DEFEND_BLUE', 'Zap': 'ZAP',
    'Dualcast': 'DUALCAST', 'Glacier': 'GLACIER', 'Reboot': 'REBOOT',
    'Injury': 'INJURY', 'Slimed': 'SLIMED', 'Dazed': 'DAZED', 'Void': 'VOID',
    'Wound': 'WOUND', 'Writhe': 'WRITHE', 'Burn': 'BURN', 'Doubt': 'DOUBT',
    'Barrage': 'BARRAGE', 'Steam': 'STEAM_BARRIER', 'Storm': 'STORM',
    'Capacitor': 'CAPACITOR', 'Consume': 'CONSUME', 'Chill': 'CHILL',
    'Buffer': 'BUFFER', 'Sunder': 'SUNDER', 'Melter': 'MELTER',
    'Aggregate': 'AGGREGATE', 'Skim': 'SKIM', 'Turbo': 'TURBO',
    'Recycle': 'RECYCLE', 'Chaos': 'CHAOS', 'Rebound': 'REBOUND',
    'Recursion': 'RECURSION', 'Stack': 'STACK', 'Leap': 'LEAP',
    'Hologram': 'HOLOGRAM', 'Streamline': 'STREAMLINE', 'Blizzard': 'BLIZZARD',
    'Electrodynamics': 'ELECTRODYNAMICS', 'Defragment': 'DEFRAGMENT',
    'Coolheaded': 'COOLHEADED', 'Cold Snap': 'COLD_SNAP',
    'Genetic Algorithm': 'GENETIC_ALGORITHM', 'Compile Driver': 'COMPILE_DRIVER',
    'Machine Learning': 'MACHINE_LEARNING', 'Heatsinks': 'HEATSINKS',
    'Static Discharge': 'STATIC_DISCHARGE', 'Go for the Eyes': 'GO_FOR_THE_EYES',
    'White Noise': 'WHITE_NOISE', 'Creative AI': 'CREATIVE_AI',
    'Self Repair': 'SELF_REPAIR', 'Boot Sequence': 'BOOT_SEQUENCE',
    'Auto Shields': 'AUTO_SHIELDS', 'Charge Battery': 'CHARGE_BATTERY',
    'Double Energy': 'DOUBLE_ENERGY', 'Loop': 'LOOP',
    'Multi-Cast': 'MULTI_CAST', 'Fusion': 'FUSION', 'Redo': 'REDO',
    'Core Surge': 'CORE_SURGE', 'Echo Form': 'ECHO_FORM',
    'Biased Cognition': 'BIASED_COGNITION', 'Fission': 'FISSION',
    'Seek': 'SEEK', 'Rainbow': 'RAINBOW', 'TURBO': 'TURBO',
    'Master of Strategy': 'MASTER_OF_STRATEGY', 'Deep Breath': 'DEEP_BREATH',
    'Purity': 'PURITY', 'Apotheosis': 'APOTHEOSIS',
    'Conserve Battery': 'CHARGE_BATTERY', 'Hello World': 'HELLO_WORLD',
    'Barrage': 'BARRAGE', 'Dark Shackles': 'DARK_SHACKLES',
    'Reinforced Body': 'REINFORCED_BODY', 'Thunderclap': 'THUNDERCLAP',
}


def card(name):
    up = name.endswith('+')
    base = name.rstrip('+')
    key = ALIASES.get(base, base.replace(' ', '_').upper())
    try:
        cid = int(sts.card_id_from_name(key))
    except ValueError:
        # Unknown alias: fall back to a harmless card so the rest of the hand still
        # reproduces; report it so the alias table can be filled in.
        print(f'  [alias missing] {name}', file=sys.stderr)
        cid = int(sts.card_id_from_name('STRIKE_BLUE'))
    return {'id': cid, 'upgrades': 1 if up else 0, 'cost': 1, 'misc': 0}


def main():
    path = Path(sys.argv[1])
    floor, turn = int(sys.argv[2]), int(sys.argv[3])
    records = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    rec = next(r for r in records
               if r.get('floor') == floor and r.get('turn') == turn
               and any(c.startswith('Barrage') for c in (r.get('hand') or [])))
    print('floor', floor, 'turn', turn, 'energy', rec['energy'], 'focus', rec['focus'])
    print('log hand :', rec['hand'])
    print('log orbs :', [o.get('id') for o in rec.get('orbs') or []])
    print('log monsters:', [(m['id'], m['hp']) for m in rec['monsters']])

    monsters = []
    for m in rec['monsters']:
        mid = int(sts.monster_id_from_name(m['id'].upper()))
        monsters.append({'id': mid, 'current_hp': m['hp'], 'max_hp': m['hp'], 'block': 0,
                         'half_dead': False, 'is_gone': False,
                         'move': int(sts.monster_move_id_from_name('INVALID')),
                         'last_move': int(sts.monster_move_id_from_name('INVALID')),
                         'powers': []})
    snapshot = {
        'character': 'DEFECT', 'seed': 1, 'floor': floor, 'ascension': 1,
        'encounter': int(sts.MonsterEncounter.THREE_SHAPES), 'turn': turn,
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
        'monsters': monsters,
        'target_map': list(range(len(monsters))),
        'relics': [], 'potions': [],
    }
    bc = sts.BattleContext.from_snapshot(snapshot, 1)
    print('engine hand:', [str(c.id).replace('CardId.', '') for c in bc.hand])
    print('engine orbs:', list(bc.player.orbs), 'slots', bc.player.orb_slots,
          'focus', bc.player.focus)

    actions = sts.get_legal_actions(bc)
    print()
    print('=== legal card actions involving BARRAGE')
    found = False
    for a in actions:
        if a.action_type != sts.SearchActionType.CARD:
            continue
        if a.source_idx >= len(bc.hand):
            continue
        name = str(bc.hand[a.source_idx].id).replace('CardId.', '')
        if 'BARRAGE' in name:
            found = True
            print('  ', a, 'target_idx', a.target_idx)
    if not found:
        print('   NONE — Barrage is not in the legal action list')
    print()
    print('total legal CARD actions:', sum(1 for a in actions
                                           if a.action_type == sts.SearchActionType.CARD))


if __name__ == '__main__':
    main()
