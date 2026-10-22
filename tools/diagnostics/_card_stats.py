"""Count how often each card is offered at a real decision, and how often it is played.

A decision is a request the solver answered. The desktop log records the state after
each command, so a card is 'offered' when it is in hand on a record that follows a
different command or a new turn.
"""
import json
from collections import Counter
from pathlib import Path

DESKTOP = Path(r'C:\Users\yang\Desktop\sts1-dev-defect')

offered = Counter()
played = Counter()
turns = 0

files = sorted(DESKTOP.glob('sts1-test-*.jsonl'), key=lambda p: p.stat().st_mtime)
for path in files:
    records = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    if not records or records[0].get('character') != 'DEFECT':
        continue
    seen_key = None
    for r in records:
        key = (r.get('floor'), r.get('turn'), tuple(sorted(r.get('hand_uuids') or r.get('hand') or [])))
        if r.get('kind') == 'card_play':
            played[r.get('card')] += 1
        if key != seen_key:
            seen_key = key
            for card in (r.get('hand') or []):
                offered[card] += 1

print('=== offered at distinct decision states vs played')
rows = []
for name in sorted(offered, key=lambda n: -(offered[n] - played.get(n, 0))):
    rows.append((offered[name] - played.get(name, 0), offered[name], played.get(name, 0), name))
print(f'{"stuck":>6} {"seen":>6} {"played":>7}  card')
for stuck, seen, won, name in rows[:40]:
    print(f'{stuck:6d} {seen:6d} {won:7d}  {name}')
