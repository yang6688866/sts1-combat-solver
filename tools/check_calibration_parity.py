"""Account for every checkpoint of a character's calibration captures.

The Watcher captures in `fixtures/calibration/WATCHER` hold 1052 checkpoints, and the work on
the character is staged: the stance state machine landed first, its cards come later. So the
question this answers is not "does everything pass" but "where did every one of the 1052 go" --
how many were compared against the simulator, how many the capture never recorded enough to
compare, and how many the simulator cannot import yet. The three numbers must add up to the
checkpoint count; nothing may be dropped between them. A compared checkpoint can still skip a
field the capture never recorded; those are listed under the three numbers instead of being
counted as compared-and-agreed.

Run it against any character directory:
    python tools/check_calibration_parity.py fixtures/calibration/WATCHER
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'overlay'))
sys.path.insert(0, str(REPO / 'tools'))
from backend import Advisor  # noqa: E402
import check_coverage_gaps as gaps  # noqa: E402
import parity_differences  # noqa: E402

UNIMPLEMENTED = re.compile(r'unknown enum name: (\w+)')
COMPARED, UNOBSERVABLE, UNIMPORTABLE, FAILED = 'compared', 'unobservable', 'not importable', 'failed'


def field_name(path):
    """Turn `/game/combat_state/hand/retain` into `hand.retain` for the summary."""
    parts = [part for part in path.split('/') if part]
    return '.'.join(parts[-2:]) if len(parts) >= 2 else path


def classify(search, case, checkpoint, root, rng_names):
    """Put one checkpoint in exactly one bucket: compared, unobservable, or not importable.

    Returns `(bucket, cause, unrecorded)`. `unrecorded` names the fields the comparison had to
    skip because the capture never recorded them: a checkpoint can be compared overall and still
    hide such a field, so they are listed on top of the three buckets instead of inflating them.
    """
    observation = checkpoint['observation']
    phase = observation.get('phase')
    if phase == 'GAME_OVER':
        return UNIMPORTABLE, 'fight is over (GAME_OVER)', ()
    if not observation.get('monsters'):
        # A reward, a card pick, a campfire: there is no board, so nothing here is a combat
        # comparison. Named by phase rather than skipped, so these stay in the denominator.
        return UNIMPORTABLE, f'out of combat ({phase})', ()
    if (observation['monsters'] or [{}])[0].get('intent') == gaps.DEBUG_INTENT:
        return UNOBSERVABLE, 'monster-intent-never-announced', ()
    what = f'{case["id"]} after {checkpoint["after"]} actions'
    try:
        view = gaps.to_view(observation, root, rng_names, case.get('character', 'DEFECT'))
        battle = search.comparator.import_battle(view, require_search_state=True)
        result = search.comparator.compare_battle(view, battle)
    except (ValueError, KeyError) as error:
        cause = gaps.unobservable(error)
        if cause is not None:
            return UNOBSERVABLE, cause[0], ()
        name = UNIMPLEMENTED.search(str(error))
        if name:
            return UNIMPORTABLE, f'unimplemented card {name.group(1)}', ()
        return UNIMPORTABLE, f'not importable ({error})', ()
    found = [d for d in result['differences'] if parity_differences.kept(d)]
    if found:
        return FAILED, f'{what}: {len(found)} differences; first: {json.dumps(found[0], ensure_ascii=False)}', ()
    unrecorded = [field_name(g['path']) for g in result['gaps']
                  if g.get('kind') == 'missing_observation']
    return COMPARED, None, unrecorded


def main():
    from sim_patch.parity.adapter import RNG_NAMES

    targets = [Path(arg) for arg in sys.argv[1:]] or sorted(REPO.glob('fixtures/calibration/*'))
    paths = []
    for target in targets:
        if target.is_dir():
            paths.extend(sorted(target.rglob('*.json.gz')))
            paths.extend(sorted(target.rglob('*.json')))
        else:
            paths.append(target)
    if not paths:
        print(f'no fixtures found under {", ".join(str(t) for t in targets)}')
        return 1

    root = json.loads((REPO / 'overlay' / 'test' / 'live-root.json').read_text(encoding='utf-8'))
    search = Advisor().search
    totals = Counter()
    causes = Counter()
    unrecorded_fields = Counter()
    failures = []
    for path in paths:
        case = gaps.read_case(path)
        counts = Counter()
        for checkpoint in case['checkpoints']:
            bucket, cause, unrecorded = classify(search, case, checkpoint, root, RNG_NAMES)
            counts[bucket] += 1
            causes[(bucket, cause)] += 1
            unrecorded_fields.update(unrecorded)
            if bucket == FAILED:
                failures.append(cause)
        assert sum(counts.values()) == len(case['checkpoints']), f'{case["id"]}: {counts}'
        totals.update(counts)
        print(f'{case["id"]:24s} {len(case["checkpoints"]):5d} checkpoints: '
              f'{counts[COMPARED]:5d} compared, {counts[UNOBSERVABLE]:5d} unobservable, '
              f'{counts[UNIMPORTABLE]:5d} not importable, {counts[FAILED]:5d} disagree')

    checkpoints = sum(totals.values())
    summary = (f'{totals[COMPARED]} compared, {totals[UNOBSERVABLE]} unobservable, '
               f'{totals[UNIMPORTABLE]} not importable')
    if totals[FAILED]:
        summary += f', {totals[FAILED]} disagree'
    print(f'\n{len(paths)} fixtures, {checkpoints} checkpoints: {summary}')
    for (bucket, cause), count in sorted(causes.items(), key=lambda item: (-item[1], str(item[0]))):
        if cause is not None:
            print(f'  {count:5d}  {bucket}: {cause}')
    if unrecorded_fields:
        print('\nfields inside compared checkpoints that the capture never recorded '
              '(these stay in "compared"; listed so nothing looks checked that was not):')
        for name, count in unrecorded_fields.most_common():
            print(f'  {count:5d}  {name}')
    if failures:
        print(f'\n{totals[FAILED]} checkpoint(s) disagree with the simulator:')
        for failure in failures:
            print('  ' + failure)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
