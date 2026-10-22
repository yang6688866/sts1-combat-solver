"""Find every hand that held Barrage and report the orb count and energy at that moment."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _paths import behaviour_logs  # noqa: E402

hits = []

files = sorted(behaviour_logs(), key=lambda p: p.stat().st_mtime)
for path in files:
    records = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    if not records or records[0].get('character') != 'DEFECT':
        continue
    for r in records:
        hand = r.get('hand') or []
        if not any(c.startswith('Barrage') for c in hand):
            continue
        orbs = [o for o in (r.get('orbs') or []) if o.get('id')]
        hits.append({
            'file': path.name[:22], 'floor': r.get('floor'), 'turn': r.get('turn'),
            'kind': r.get('kind'), 'energy': r.get('energy'),
            'orbs': [o.get('id') for o in orbs], 'focus': r.get('focus'),
            'hand': hand,
        })

print('records holding Barrage:', len(hits))
for h in hits[:25]:
    print(f"{h['file']} f{h['floor']} t{h['turn']} {h['kind']:<12} energy={h['energy']} "
          f"focus={h['focus']} orbs={h['orbs']}")
    print('   hand:', h['hand'])
