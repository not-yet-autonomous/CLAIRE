# Cowork Prompt — File Audit Repair (2026-05-19)

Run this after the Cycle 4 digest is confirmed good. These are mechanical file operations — no pipeline code changes.

---

## Session Start

```powershell
cd "C:\DEV\CLAIRE"
.\.venv\Scripts\Activate.ps1
python -c "import anthropic, requests; print('Deps OK')"
```

Expected: `(.venv)` in prompt + `Deps OK`

---

## Step 1: Repair root change_log.json

The file ends with a dangling `{` after the c3-prof-003 entry — truncated mid-write. Remove it and close the JSON properly.

```powershell
# Read the file, find the truncation, write the repair
python -c "
content = open('change_log.json', 'r', encoding='utf-8').read()

# The file ends with:  },\n    {\n  at the end of the changes array
# Strip the dangling open-brace entry and close the structure
# Find the last complete entry closing brace
last_good = content.rfind('    },\n    {')
if last_good == -1:
    # Try alternate — ends with }  then newline then {
    last_good = content.rfind('\n    {\n')
    if last_good > 0:
        repaired = content[:last_good] + '\n  ]\n}\n'
    else:
        print('Could not find truncation point — inspect manually')
        exit(1)
else:
    repaired = content[:last_good] + '\n    }\n  ]\n}\n'

# Verify it parses
import json
try:
    json.loads(repaired)
    print('JSON valid after repair')
    open('change_log.json', 'w', encoding='utf-8').write(repaired)
    print('Written.')
except Exception as e:
    print(f'Still invalid: {e}')
    print('Last 100 chars of repaired:', repr(repaired[-100:]))
"
```

Verify:
```powershell
python -c "import json; d=json.load(open('change_log.json')); print('Entries:', len(d['changes'])); print('Last ID:', d['changes'][-1]['id'])"
```

Expected output: `Entries: 10` and `Last ID: c3-prof-003`

---

## Step 2: Rename data\change_log.json to legacy

```powershell
Rename-Item -Path "data\change_log.json" -NewName "change_log_v1_legacy.json"
```

Verify:
```powershell
Test-Path "data\change_log_v1_legacy.json"   # True
Test-Path "data\change_log.json"              # False
```

---

## Step 3: Confirm friction_log.txt canonical location

Root `friction_log.txt` (4,298 bytes, updated 2026-05-10, Cycles 1-3 entries) is canonical.
`data\friction_log.txt` (2,585 bytes, updated 2026-04-26) is the original template with only the Apr 26 entries — not current.

No rename needed. Just confirm the files exist as expected:
```powershell
(Get-Item "friction_log.txt").Length          # Should be ~4298
(Get-Item "data\friction_log.txt").Length     # Should be ~2585
```

The data\ copy is harmless to leave as-is — it's not referenced by any pipeline script. If you want to make the distinction explicit:
```powershell
Rename-Item -Path "data\friction_log.txt" -NewName "friction_log_original_template.txt"
```

---

## Step 4: Create archive\ directory

```powershell
New-Item -ItemType Directory -Path "archive" -ErrorAction SilentlyContinue
New-Item -ItemType File -Path "archive\.gitkeep" -ErrorAction SilentlyContinue
```

---

## Step 5: Verify repair and commit

```powershell
# Quick audit check
python -c "
import json, os

files = [
    ('change_log.json', 'root canonical'),
    ('data/change_log_v1_legacy.json', 'v1.0 legacy'),
    ('data/claire_a_session_history.json', 'session history'),
    ('data/cost_log.json', 'cost log'),
    ('data/ingest_run_log.json', 'ingest log'),
]

for path, label in files:
    try:
        json.load(open(path))
        print(f'OK  {path} ({label})')
    except FileNotFoundError:
        print(f'MISSING  {path} ({label})')
    except Exception as e:
        print(f'CORRUPT  {path} ({label}): {e}')

print()
print('archive/ exists:', os.path.isdir('archive'))
print('friction_log.txt (root) exists:', os.path.isfile('friction_log.txt'))
"
```

Expected: all OK, archive exists, friction_log present.

```powershell
git add -A
git commit -m "CLAIRE file audit 2026-05-19 — repair change_log.json, rename legacy, create archive/, correct HANDOFF paths"
```

---

## Notes for future Cowork prompts

**Canonical paths confirmed by audit:**
- `change_log.json` — **root**, NOT `data\change_log.json`
- `friction_log.txt` — **root**, NOT `data\friction_log.txt`

All future prompts that read or write `change_log.json` must use the root path.

**JSON corruption (separate issue):**
`synthesis_queue_track_a/b/c.json` and `candidates_track_a/c.json` all have parse errors from truncated writes. These are regenerated outputs — fix by re-running triage and synthesis on current `raw_posts.json`. Not blocking for Build 8; address if a pipeline run fails on read.
