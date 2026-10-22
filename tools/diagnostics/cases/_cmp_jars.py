import zipfile, hashlib, os, json, sys

cands = {
    'installed mods': r'E:\SteamLibrary\steamapps\common\SlayTheSpire\mods\STS1CombatSolver-defect-1021.jar',
    'my build': r'E:\games\sts1-combat-solver-main\overlay\build\STS1CombatSolver.jar',
    'workshop-disable': r'E:\SteamLibrary\steamapps\workshop\content\646570\3814773843\STS1CombatSolver.jar.disable',
}

for k, p in cands.items():
    if not os.path.exists(p):
        print(k, 'MISSING')
        continue
    b = open(p, 'rb').read()
    z = zipfile.ZipFile(p)
    try:
        props = z.read('solver.properties').decode('utf-8')
    except KeyError:
        props = '<none>'
    try:
        j = json.loads(z.read('ModTheSpire.json').decode('utf-8'))
        ver = j.get('version')
        name = j.get('name', '')[:40]
    except Exception as e:
        ver = 'ERR ' + str(e)
        name = ''
    print('---', k)
    print('   size', len(b), 'sha', hashlib.sha256(b).hexdigest()[:16], 'ver', ver)
    print('   name', repr(name))
    print('   props:', props.replace('\n', ' | '))
