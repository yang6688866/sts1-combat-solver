"""Replay floor 39 with the real exported RNG and compare against the recorded game result."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / 'candidates/sts-ironclad-agent'
sys.path[:0] = [str(ROOT), str(AGENT), str(AGENT / 'steam'), str(AGENT / 'sim_patch/alignment/tests')]

from sim_patch.parity.adapter import ActionMapper, Comparator


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def replay(data):
    cur = data['recent_battles']['current']
    root = cur['root']
    game = root['game_state']
    comparator = Comparator(AGENT / 'runtime/engine', AGENT)
    view = {'game': game, 'available_commands': root['available_commands']}
    streams = game['full_rng_state']['streams']
    from steam.rng_contract import COMBAT_STREAMS
    view['rng'] = {name: {k: int(streams[name][k]) for k in ('seed0', 'seed1', 'counter')}
                   for name in COMBAT_STREAMS.values()}
    view = {**view, 'game': {**game, 'seed': int(game['seed']) % (1 << 64)}}
    battle = comparator.import_battle(view, require_search_state=True)
    mapper = ActionMapper(comparator, battle, view)
    return battle, mapper, cur, comparator, view


def describe(battle):
    return {
        'hp': battle.player.cur_hp,
        'block': battle.player.block,
        'monsters': [(str(m.id).replace('MonsterId.', ''), m.cur_hp, bool(m.alive))
                     for m in battle.monsters],
        'orbs': list(battle.player.orbs),
        'focus': battle.player.focus,
        'rng': {k: v['counter'] for k, v in battle.rng_states.items()},
        'turn': battle.turn,
    }


def main():
    data = load(sys.argv[1])
    print('seed:', data['seed'])
    battle, mapper, cur, comparator, view = replay(data)
    d = describe(battle)
    print('imported  turn', d['turn'], 'hp', d['hp'], 'block', d['block'])
    print('  monsters:', d['monsters'])
    print('  orbs:', d['orbs'], 'focus', d['focus'])
    print('  rng counters:', d['rng'])
    print()
    print('recorded events (last one is the post-end-turn state):')
    for e in cur['events']:
        print('  ', e.get('kind'), 'f', e.get('floor'), 't', e.get('turn'),
              'hp', e.get('hp'), [(m['id'], m['hp']) for m in e.get('monsters') or []])
    last = cur['events'][-1]
    print()
    print('game   after end_turn:', [(m['id'], m['hp']) for m in last['monsters']],
          'hp', last['hp'])
    before = describe(battle)
    end = [a for a in comparator.sts.get_legal_actions(battle)
           if a.action_type == comparator.sts.SearchActionType.END_TURN]
    if not end:
        print('no END_TURN available')
        return
    end[0].execute(battle)
    after = describe(battle)
    print('engine after end_turn:', [(n, hp, alive) for n, hp, alive in after['monsters']],
          'hp', after['hp'])
    print()
    print('rng before:', before['rng'])
    print('rng after :', after['rng'])


if __name__ == '__main__':
    main()




