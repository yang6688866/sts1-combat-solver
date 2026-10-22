import json
f = r'C:\Users\yang\Desktop\sts1-dev-defect\sts1-test-17237950363417997370.jsonl'
lines = [json.loads(l) for l in open(f, encoding='utf-8') if l.strip()]

# search all records for powers / loop hints
keys = set()
for r in lines:
    keys.update(r.keys())
print('all keys:', sorted(keys))

# find any record containing 'Loop' card
for i, r in enumerate(lines):
    s = json.dumps(r, ensure_ascii=False)
    if "'Loop'" in s or '"Loop"' in s:
        print(i, r.get('kind'), r.get('floor'), r.get('turn'), [c for c in (r.get('hand') or []) if 'Loop' in c])
