"""Rebuild a recorded state with correct card costs and ask the solver for a plan.

The log stores card names, not costs, so the cost table from the game data is
used here; the coarse `card()` helper in _barrage_damage defaults to cost 1 and
would make cards like Aggregate (cost 1) and Capacitor (cost 1) look cheaper than
they are in states where the snapshot's own costs differ.
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
from steam.steam_mcts import (  # noqa: E402
    MONSTER_ALIASES, MOVE_NAMES, card_snapshot)

import _card_usage as usage  # noqa: E402

native = importlib.import_module('live_combat_search')

# Logged intent -> engine move name, for monsters whose intent names carry
# information the engine does not encode in <MONSTER>_<INTENT> (a monster can
# have several moves of one intent). Verified by hand against MonsterMoves.h and
# the base-game behaviour; anything missing falls back to the first move whose
# name ends with the intent, and the engine rejects the state if that guess is
# wrong.
INTENT_MOVES = {
    ('Nemesis', 'ATTACK'): 'NEMESIS_SCYTHE',
    ('Nemesis', 'ATTACK_DEBUFF'): 'NEMESIS_ATTACK',
    ('Nemesis', 'DEBUFF'): 'NEMESIS_DEBUFF',
    ('Cultist', 'ATTACK'): 'CULTIST_DARK_STRIKE',
    ('JawWorm', 'ATTACK'): 'JAW_WORM_CHOMP',
    ('JawWorm', 'ATTACK_DEFEND'): 'JAW_WORM_THRASH',
    ('JawWorm', 'DEFEND'): 'JAW_WORM_BELLOW',
    ('GiantHead', 'ATTACK'): 'GIANT_HEAD_COUNT',
    ('GiantHead', 'ATTACK_DEBUFF'): 'GIANT_HEAD_GLARE',
    ('GiantHead', 'BUFF'): 'GIANT_HEAD_IT_IS_TIME',
    ('BookOfStabbing', 'ATTACK'): 'BOOK_OF_STABBING_MULTI_STAB',
    ('Sentry', 'ATTACK'): 'SENTRY_BEAM',
    ('Sentry', 'DEFEND'): 'SENTRY_BOLT',
    ('SpikeSlime_S', 'ATTACK'): 'SPIKE_SLIME_S_TACKLE',
    ('GremlinFat', 'ATTACK'): 'FAT_GREMLIN_SMASH',
    ('GreenLouse', 'ATTACK'): 'GREEN_LOUSE_BITE',
    ('GreenLouse', 'DEFEND'): 'GREEN_LOUSE_SPIT_WEB',
    ('Orb Walker', 'ATTACK'): 'ORB_WALKER_LASER',
    ('Orb Walker', 'ATTACK_DEBUFF'): 'ORB_WALKER_CLAW',
    ('Champ', 'ATTACK'): 'THE_CHAMP_HEAVY_SLASH',
    ('Champ', 'DEFEND'): 'THE_CHAMP_DEFENSIVE_STANCE',
    ('Champ', 'DEFEND_BUFF'): 'THE_CHAMP_GLOAT',
    ('Champ', 'BUFF'): 'THE_CHAMP_TAUNT',
    ('Champ', 'ATTACK_BUFF'): 'THE_CHAMP_ANGER',
    ('Sentry', 'DEBUFF'): 'SENTRY_BOLT',
    ('FatGremlin', 'ATTACK_DEBUFF'): 'FAT_GREMLIN_SMASH',
    ('JawWorm', 'DEFEND_BUFF'): 'JAW_WORM_BELLOW',
    ('CorruptHeart', 'ATTACK'): 'CORRUPT_HEART_BLOOD_SHOTS',
    ('CorruptHeart', 'ATTACK_DEBUFF'): 'CORRUPT_HEART_DEBILITATE',
    ('CorruptHeart', 'BUFF'): 'CORRUPT_HEART_BUFF',
    ('GremlinNob', 'ATTACK'): 'GREMLIN_NOB_RUSH',
    ('GremlinNob', 'ATTACK_DEFEND'): 'GREMLIN_NOB_SKULL_BASH',
    ('GremlinNob', 'BUFF'): 'GREMLIN_NOB_BELLOW',
    ('Looter', 'ATTACK'): 'LOOTER_MUG',
    ('Looter', 'ATTACK_DEBUFF'): 'LOOTER_LUNGE',
    ('Looter', 'DEFEND'): 'LOOTER_SMOKE_BOMB',
    ('Cultist', 'BUFF'): 'CULTIST_INCANTATION',
    ('TorchHead', 'ATTACK'): 'TORCH_HEAD_TACKLE',
    ('Repulsor', 'DEBUFF'): 'REPULSOR_REPULSE',
    ('SnakePlant', 'ATTACK'): 'SNAKE_PLANT_CHOMP',
    ('SnakePlant', 'DEFEND'): 'SNAKE_PLANT_ENFEEBLING_SPORES',
    ('Exploder', 'ATTACK'): 'EXPLODER_SLAM',
    ('RedLouse', 'ATTACK'): 'RED_LOUSE_BITE',
    ('RedLouse', 'BUFF'): 'RED_LOUSE_GROW',
    ('AcidSlime_M', 'ATTACK'): 'ACID_SLIME_M_TACKLE',
    ('AcidSlime_M', 'ATTACK_DEBUFF'): 'ACID_SLIME_M_CORROSIVE_SPIT',
    ('AcidSlime_M', 'DEBUFF'): 'ACID_SLIME_M_LICK',
    ('SlaverBlue', 'ATTACK'): 'BLUE_SLAVER_STAB',
    ('SlaverBlue', 'ATTACK_DEBUFF'): 'BLUE_SLAVER_RAKE',
    ('Shelled Parasite', 'ATTACK'): 'SHELLED_PARASITE_DOUBLE_STRIKE',
    ('Shelled Parasite', 'DEFEND'): 'SHELLED_PARASITE_FELL',
    ('Shelled Parasite', 'ATTACK_DEBUFF'): 'SHELLED_PARASITE_SUCK',
    ('Shelled Parasite', 'ATTACK_BUFF'): 'SHELLED_PARASITE_DOUBLE_STRIKE',
    ('GremlinWarrior', 'ATTACK'): 'MAD_GREMLIN_SCRATCH',
    ('FuzzyLouseNormal', 'ATTACK'): 'RED_LOUSE_BITE',
    ('FuzzyLouseNormal', 'BUFF'): 'RED_LOUSE_GROW',
    ('FuzzyLouseDefensive', 'ATTACK'): 'GREEN_LOUSE_BITE',
    ('FuzzyLouseDefensive', 'DEFEND'): 'GREEN_LOUSE_SPIT_WEB',
    ('Darkling', 'ATTACK'): 'DARKLING_NIP',
    ('Darkling', 'DEFEND'): 'DARKLING_HARDEN',
    ('Darkling', 'BUFF'): 'DARKLING_REINCARNATE',
    ('FungiBeast', 'ATTACK'): 'FUNGI_BEAST_BITE',
    ('FungiBeast', 'BUFF'): 'FUNGI_BEAST_GROW',
    ('Spiker', 'ATTACK'): 'SPIKER_CUT',
    ('Spiker', 'BUFF'): 'SPIKER_SPIKE',
    ('Lagavulin', 'ATTACK'): 'LAGAVULIN_ATTACK',
    ('Lagavulin', 'SLEEP'): 'LAGAVULIN_SLEEP',
    ('Lagavulin', 'DEBUFF'): 'LAGAVULIN_SIPHON_SOUL',
    ('CorruptHeart', 'STRONG_DEBUFF'): 'CORRUPT_HEART_DEBILITATE',
    ('SpikeSlime_M', 'DEBUFF'): 'SPIKE_SLIME_M_LICK',
    ('SpikeSlime_M', 'ATTACK_DEBUFF'): 'SPIKE_SLIME_M_FLAME_TACKLE',
    ('SpikeSlime_L', 'DEBUFF'): 'SPIKE_SLIME_L_LICK',
    ('SpikeSlime_L', 'ATTACK'): 'SPIKE_SLIME_L_TACKLE',
    ('AcidSlime_S', 'DEBUFF'): 'ACID_SLIME_S_LICK',
    ('AcidSlime_S', 'ATTACK'): 'ACID_SLIME_S_TACKLE',
    ('SlaverBoss', 'ATTACK_DEBUFF'): 'TASKMASTER_SCOURING_WHIP',
    ('TheGuardian', 'ATTACK'): 'THE_GUARDIAN_FIERCE_BASH',
    ('TheGuardian', 'DEFEND'): 'THE_GUARDIAN_DEFENSIVE_MODE',
    ('SlaverRed', 'ATTACK'): 'RED_SLAVER_STAB',
    ('SlaverRed', 'ATTACK_DEBUFF'): 'RED_SLAVER_SCRAPE',
    ('SlaverRed', 'DEBUFF'): 'RED_SLAVER_ENTANGLE',
    ('TheCollector', 'ATTACK'): 'THE_COLLECTOR_FIREBALL',
    ('TheCollector', 'BUFF'): 'THE_COLLECTOR_BUFF',
    ('TheCollector', 'STRONG_DEBUFF'): 'THE_COLLECTOR_MEGA_DEBUFF',
    ('TimeEater', 'ATTACK'): 'TIME_EATER_REVERBERATE',
    ('TimeEater', 'ATTACK_DEBUFF'): 'TIME_EATER_HEAD_SLAM',
    ('TimeEater', 'DEFEND_DEBUFF'): 'TIME_EATER_RIPPLE',
    ('TimeEater', 'BUFF'): 'TIME_EATER_HASTE',
    ('SpireSpear', 'ATTACK'): 'SPIRE_SPEAR_SKEWER',
    ('SpireSpear', 'ATTACK_DEBUFF'): 'SPIRE_SPEAR_BURN_STRIKE',
    ('TheGuardian', 'ATTACK_BUFF'): 'THE_GUARDIAN_WHIRLWIND',
    ('TheGuardian', 'DEFEND_BUFF'): 'THE_GUARDIAN_CHARGING_UP',
    ('Champ', 'ATTACK_DEBUFF'): 'THE_CHAMP_FACE_SLAP',
    ('SpireShield', 'ATTACK'): 'SPIRE_SHIELD_BASH',
    ('SpireShield', 'ATTACK_DEFEND'): 'SPIRE_SHIELD_SMASH',
    ('SpireShield', 'DEFEND'): 'SPIRE_SHIELD_FORTIFY',
    ('GremlinWizard', 'BUFF'): 'GREMLIN_WIZARD_CHARGING',
    ('GremlinWizard', 'ATTACK'): 'GREMLIN_WIZARD_ULTIMATE_BLAST',
    ('GremlinWizard', 'UNKNOWN'): 'GREMLIN_WIZARD_CHARGING',
    ('SlimeBoss', 'ATTACK'): 'SLIME_BOSS_SLAM',
    ('GremlinNob', 'ATTACK_DEBUFF'): 'GREMLIN_NOB_SKULL_BASH',
    ('AcidSlime_L', 'UNKNOWN'): 'ACID_SLIME_L_SPLIT',
    ('AcidSlime_L', 'ATTACK'): 'ACID_SLIME_L_TACKLE',
    ('AcidSlime_L', 'ATTACK_DEBUFF'): 'ACID_SLIME_L_CORROSIVE_SPIT',
    ('AcidSlime_L', 'DEBUFF'): 'ACID_SLIME_L_LICK',
    ('SnakePlant', 'STRONG_DEBUFF'): 'SNAKE_PLANT_ENFEEBLING_SPORES',
    ('SphericGuardian', 'ATTACK'): 'SPHERIC_GUARDIAN_SLAM',
    ('SphericGuardian', 'ATTACK_DEBUFF'): 'SPHERIC_GUARDIAN_ATTACK_DEBUFF',
    ('SphericGuardian', 'DEFEND'): 'SPHERIC_GUARDIAN_HARDEN',
    ('SphericGuardian', 'BUFF'): 'SPHERIC_GUARDIAN_ACTIVATE',
    ('SpireSpear', 'BUFF'): 'SPIRE_SPEAR_PIERCER',
    ('Mugger', 'ATTACK'): 'MUGGER_MUG',
    ('Mugger', 'ATTACK_DEBUFF'): 'MUGGER_LUNGE',
    ('Mugger', 'DEFEND'): 'MUGGER_SMOKE_BOMB',
    ('Lagavulin', 'STUN'): 'LAGAVULIN_SLEEP',
    ('SlimeBoss', 'ATTACK_DEBUFF'): 'SLIME_BOSS_GOOP_SPRAY',
    ('SlimeBoss', 'UNKNOWN'): 'SLIME_BOSS_PREPARING',
    ('GremlinFat', 'ATTACK_DEBUFF'): 'FAT_GREMLIN_SMASH',
    ('Lagavulin', 'STRONG_DEBUFF'): 'LAGAVULIN_SIPHON_SOUL',
    ('GreenLouse', 'DEBUFF'): 'GREEN_LOUSE_SPIT_WEB',
    ('RedLouse', 'DEBUFF'): 'RED_LOUSE_GROW',
    ('SlaverRed', 'STRONG_DEBUFF'): 'RED_SLAVER_ENTANGLE',
    ('GremlinThief', 'ATTACK'): 'SNEAKY_GREMLIN_PUNCTURE',
    ('GremlinTsundere', 'ATTACK'): 'SHIELD_GREMLIN_PROTECT',
    ('GremlinTsundere', 'DEFEND'): 'SHIELD_GREMLIN_PROTECT',
    ('Champ', 'DEBUFF'): 'THE_CHAMP_TAUNT',
    ('FuzzyLouseDefensive', 'DEBUFF'): 'GREEN_LOUSE_SPIT_WEB',
    ('TheGuardian', 'BUFF'): 'THE_GUARDIAN_WHIRLWIND',
    ('GiantHead', 'DEBUFF'): 'GIANT_HEAD_GLARE',
    ('SlimeBoss', 'STRONG_DEBUFF'): 'SLIME_BOSS_GOOP_SPRAY',
    ('Centurion', 'ATTACK'): 'CENTURION_SLASH',
    ('Darkling', 'UNKNOWN'): 'DARKLING_REINCARNATE',
    ('GremlinLeader', 'ATTACK'): 'GREMLIN_LEADER_STAB',
    ('GremlinLeader', 'DEFEND_BUFF'): 'GREMLIN_LEADER_ENCOURAGE',
    ('GremlinLeader', 'BUFF'): 'GREMLIN_LEADER_RALLY',
    ('GremlinLeader', 'UNKNOWN'): 'GREMLIN_LEADER_RALLY',
    ('Byrd', 'ATTACK'): 'BYRD_PECK',
    ('Byrd', 'ATTACK_DEFEND'): 'BYRD_SWOOP',
    ('Byrd', 'DEFEND'): 'BYRD_FLY',
    ('Byrd', 'BUFF'): 'BYRD_CAW',
    ('Byrd', 'STUN'): 'BYRD_STUNNED',
    ('SphericGuardian', 'ATTACK_DEFEND'): 'SPHERIC_GUARDIAN_ATTACK_DEBUFF',
    ('SpireShield', 'ATTACK_DEBUFF'): 'SPIRE_SHIELD_SMASH',
    ('SpikeSlime_L', 'ATTACK_DEBUFF'): 'SPIKE_SLIME_L_FLAME_TACKLE',
    ('TheCollector', 'UNKNOWN'): 'THE_COLLECTOR_SPAWN',
    ('TheCollector', 'DEFEND_BUFF'): 'THE_COLLECTOR_BUFF',
}


def snap_card(name, costs):
    up = name.endswith('+')
    base = name.rstrip('+')
    key = usage.ENUM_NAMES.get(base, usage.ALIASES.get(base, base).replace(' ', '_').upper())
    cost = costs.get(name)
    if cost is None:
        key_cost = usage.resolve(name)
        cost = costs.get(key_cost) if key_cost else None
    if cost is None:
        raise KeyError(f'no cost for {name}')
    return card_snapshot({'id': key, 'upgrades': 1 if up else 0, 'cost': cost})


def _move_id(monster, raw):
    """Resolve the logged intent to an engine move id.

    The log carries only the intent name (and sometimes an ordinal), and the
    engine names moves <MONSTER>_<NAME>, so the best guess is the first move of
    that monster whose name ends with the intent. Where that guess is wrong the
    engine rejects the snapshot and the caller skips the state.
    """
    if str(raw).isdigit():
        return int(raw)
    known = INTENT_MOVES.get((monster['id'], raw))
    if known:
        return int(sts.monster_move_id_from_name(known))
    alias = MONSTER_ALIASES.get(monster['id'], monster['id'])
    known = INTENT_MOVES.get((alias, raw))
    if known:
        return int(sts.monster_move_id_from_name(known))
    upper = MONSTER_ALIASES.get(monster['id'], monster['id']).upper().replace(' ', '_')
    candidates = [name for (mid, idx), name in sorted(MOVE_NAMES.items())
                  if mid == upper and name.endswith('_' + raw)]
    if not candidates:
        raise KeyError(f'no move name for {upper} {raw}')
    return int(sts.monster_move_id_from_name(candidates[0]))


def build(rec, costs):
    monsters = []
    for m in rec['monsters']:
        raw = str(m.get('intent_ordinal') or m['intent'])
        monsters.append({'id': int(sts.monster_id_from_name(
                             MONSTER_ALIASES.get(m['id'], m['id']).upper().replace(' ', '_'))),
                         'current_hp': m['hp'], 'max_hp': m.get('max_hp', m['hp']),
                         'block': int(m.get('block') or 0), 'half_dead': False,
                         'is_gone': False, 'misc_info': 0,
                         'move': _move_id(m, raw),
                         'last_move': 0, 'powers': []})
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
        'hand': [snap_card(c, costs) for c in rec['hand']],
        'draw_pile': [snap_card(c, costs) for c in rec['draw']],
        'discard_pile': [snap_card(c, costs) for c in rec['discard']],
        'exhaust_pile': [snap_card(c, costs) for c in rec.get('exhaust') or []],
        'monsters': monsters, 'target_map': list(range(len(monsters))),
        'relics': [], 'potions': [],
    }
    return sts.BattleContext.from_snapshot(snapshot, 1)


def main():
    path = Path(sys.argv[1])
    floor, turn = int(sys.argv[2]), int(sys.argv[3])
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else 4000
    costs = {name: cost for name, cost in usage.COSTS.items()}
    records = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    rec = next(r for r in records
               if r.get('floor') == floor and r.get('turn') == turn
               and r.get('kind') == 'card_play'
               and any(c.startswith('Barrage') for c in (r.get('hand') or [])))
    bc = build(rec, costs)
    print(f"floor {floor} turn {turn}: energy {rec['energy']} focus {rec.get('focus')} "
          f"orbs {[o.get('id') for o in rec.get('orbs') or []]}")
    print('hand:', rec['hand'], '-> costs',
          [costs[usage.resolve(c)] for c in rec['hand']])
    print('in-game play:', rec['card'])
    plan = dict(native.plan_reusing(bc, budget, 12.0))
    print('outcome', plan.get('outcome'), 'actions', plan['actions'])
    replay = bc.clone()
    for step, bits in enumerate(plan['actions'], 1):
        idx = (bits >> 8) & 0xff
        kind = bits >> 16
        label = ('CARD ' + (str(replay.hand[idx].id).replace('CardId.', '')
                            if idx < len(replay.hand) else '?')) \
            if kind == 0 else ('END TURN' if kind == 3 else f'type={kind}')
        hp0 = [m.cur_hp for m in replay.monsters]
        sts.SearchAction.from_bits(bits & 0xffffffff).execute(replay)
        hp1 = [m.cur_hp for m in replay.monsters]
        print(f'  {step}. {label:26s} energy {replay.player.energy:2d} '
              f'block {replay.player.block:3d} monsters {hp0}->{hp1}')


if __name__ == '__main__':
    main()
