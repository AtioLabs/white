# Show White's new 2.0 state: intents, inbox items, scouted skills (no secrets).
$h = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
$py = @"
import sqlite3, json, sys, os
h = sys.argv[1]
w = sqlite3.connect(os.path.join(h, 'white', 'world.db'))
has = lambda t: w.execute("select name from sqlite_master where name=?", (t,)).fetchone()
print('intents:', w.execute('select id, what, confidence, decision, status from intents').fetchall() if has('intents') else 'table not created yet')
print('quiet:', w.execute('select why from intent_quiet').fetchall() if has('intent_quiet') else '-')
print('signals:', w.execute('select type, summary from signals order by id desc limit 5').fetchall())
i = os.path.join(h, 'white', 'inbox.db')
if os.path.exists(i): print('inbox:', sqlite3.connect(i).execute('select name, status, substr(summary,1,60) from inbox_items').fetchall())
s = os.path.join(h, 'white', 'scout.json')
print('scouted:', [r['name'] for r in json.load(open(s))] if os.path.exists(s) else [])
"@
python -c $py $h
