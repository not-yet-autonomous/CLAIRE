# Reddit App Registration — CLAIRE Build 1 Prerequisite
# Estimated time: 10 minutes

---

## Step 1 — Reddit Account

You need a Reddit account. Use an existing one or create a dedicated
bot account. A dedicated account is cleaner — it keeps CLAIRE's
API credentials separate from personal Reddit use.

If creating a new account: reddit.com/register
Suggested username pattern: YourName_CLAIRE or similar.

---

## Step 2 — Register the App

1. Log in to the account you'll use for CLAIRE
2. Go to: https://www.reddit.com/prefs/apps
3. Scroll to the bottom — click "create another app" (or "create an app"
   if this is a fresh account)

---

## Step 3 — Fill Out the App Form

| Field | Value |
|-------|-------|
| Name | CLAIRE |
| App type | **script** ← critical, select this one |
| Description | Personal Claude config improvement pipeline |
| About URL | leave blank |
| Redirect URI | http://localhost:8080 (required but unused for script type) |

Click "create app."

---

## Step 4 — Collect Your Credentials

After creation you'll see:

```
CLAIRE
personal use script

[your client_id appears here — under the app name, looks like: abc123XYZ]

secret: [your client_secret appears here]
```

**client_id** = the string directly under "personal use script" and your app name.
It is NOT labeled. It's the shorter string, ~14 characters.

**client_secret** = labeled "secret." Longer string.

Copy both now. You won't see the secret again without regenerating it.

---

## Step 5 — Set Environment Variables

Windows (PowerShell — set permanently via System Properties > Environment Variables):

```powershell
[System.Environment]::SetEnvironmentVariable("REDDIT_CLIENT_ID", "your_client_id", "User")
[System.Environment]::SetEnvironmentVariable("REDDIT_CLIENT_SECRET", "your_secret", "User")
[System.Environment]::SetEnvironmentVariable("REDDIT_USER_AGENT", "CLAIRE/0.1 by /u/YOUR_REDDIT_USERNAME", "User")
```

Or add to a .env file in the claire/ directory (requires python-dotenv in Build 1):

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=CLAIRE/0.1 by /u/YOUR_REDDIT_USERNAME
```

Never hardcode credentials in any .py file.
Never commit a .env file to version control.

---

## Step 6 — Verify Access Tier

CLAIRE uses a **read-only script** instance. This means:
- No posting, no voting, no moderation actions
- 60 requests/minute (OAuth authenticated)
- PRAW handles rate limiting automatically — no manual throttling needed

No additional API approval required for read-only script access.
Reddit's paid API tiers apply to high-volume commercial use — CLAIRE's
weekly batch is well within free tier limits.

---

## Ready for Build 1

Once env vars are set, Build 1 (claire_ingest.py) can be scaffolded.
