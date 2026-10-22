"""Find every hand that held Barrage and report the orb count and energy at that moment."""
import json
from pathlib import Path

DESKTOP = Path(r'C:\Users\yang\Desktop\sts1-dev-defect')
hits = []

files = sorted(DESKTOP.glob('sts1-test-*.jsonl'), key=lambda p: p.stat().st_mtime)
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
