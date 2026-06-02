# Copyright (c) 2026 James Cole. Licensed under the MIT License.
"""
CLAIRE — Build 10: Ingestion Layer
Sources: HackerNews API + dev.to API
Output:  data/raw_posts.json

Run:     python claire_ingest.py
         python claire_ingest.py --dry-run   (fetch counts only, no write)
         python claire_ingest.py --source hackernews
         python claire_ingest.py --source forum
         python claire_ingest.py --source all
"""

import json
import os
import time
import argparse
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

import psutil
import requests
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

RAW_POSTS_PATH  = DATA_DIR / "raw_posts.json"
RUN_LOG_PATH    = DATA_DIR / "ingest_run_log.json"
LOCK_PATH       = DATA_DIR / "ingest.lock"

HN_HEADERS      = {"User-Agent": "CLAIRE/0.1 personal-use-signal-pipeline"}

HN_DELAY        = 0.5   # HackerNews is more permissive

# Load full config
try:
    with open(BASE_DIR / "config.json") as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    raise SystemExit("CLAIRE: config.json not found. Run from project root.")
except json.JSONDecodeError as e:
    raise SystemExit(f"CLAIRE: config.json is malformed — {e}")

_REQUIRED_KEYS = [
    ("ingestion", "comments_per_post"),
    ("ingestion", "hn_search_terms"),
    ("ingestion", "hn_results_per_query"),
    ("ingestion", "hn_min_points"),
    ("triage", "noise_prefilter", "min_score"),
    ("triage", "noise_prefilter", "min_comments"),
]
for _path in _REQUIRED_KEYS:
    _node = CONFIG
    for _key in _path:
        if not isinstance(_node, dict) or _key not in _node:
            raise SystemExit(f"CLAIRE: config.json missing required key: {' > '.join(_path)}")
        _node = _node[_key]

COMMENTS_PER_POST   = CONFIG["ingestion"]["comments_per_post"]

# HackerNews: search terms to query via Algolia API
HN_SEARCH_TERMS      = CONFIG["ingestion"]["hn_search_terms"]
HN_RESULTS_PER_QUERY = CONFIG["ingestion"]["hn_results_per_query"]
HN_MIN_POINTS        = CONFIG["ingestion"]["hn_min_points"]

# dev.to practitioner articles
DEVTO_BASE_URL   = "https://dev.to/api"
DEVTO_TAGS       = CONFIG["devto"]["tags"]          # list of {name, min_reactions}
DEVTO_PER_PAGE   = 30                               # articles per tag fetch
DEVTO_PAGES      = CONFIG["devto"]["pages_per_tag"] # pages per tag (30 x N candidates per tag)

# Noise prefilter thresholds (applied before triage — saves Haiku calls)
MIN_SCORE    = CONFIG["triage"]["noise_prefilter"]["min_score"]
MIN_COMMENTS = CONFIG["triage"]["noise_prefilter"]["min_comments"]

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

_LOG_FORMAT  = "%(asctime)s  %(levelname)-8s  %(message)s"
_LOG_DATEFMT = "%H:%M:%S"
_formatter   = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATEFMT)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)

_file_handler = logging.FileHandler(LOGS_DIR / "ingest.log", encoding="utf-8")
_file_handler.setFormatter(_formatter)

logging.root.setLevel(logging.INFO)
logging.root.addHandler(_console_handler)
logging.root.addHandler(_file_handler)

log = logging.getLogger("claire.ingest")

# ─────────────────────────────────────────────────────────────────────────────
# LOCK
# ─────────────────────────────────────────────────────────────────────────────

def _acquire_lock():
    """
    Create data/ingest.lock with current PID. If the lock already exists,
    check whether the owning process is still alive:
      - Alive  → exit cleanly. Task Scheduler overlap, do nothing.
      - Dead   → stale lock from a prior crash. Remove it and proceed.
    """
    if LOCK_PATH.exists():
        try:
            lock_data = json.loads(LOCK_PATH.read_text())
            pid       = lock_data.get("pid")
            started   = lock_data.get("started_at", "unknown")
        except (ValueError, KeyError, OSError):
            pid, started = None, "unknown"

        if pid and psutil.pid_exists(pid):
            log.warning(
                f"CLAIRE ingest already running — PID {pid} started {started}. "
                f"Exiting to avoid concurrent writes."
            )
            raise SystemExit(0)
        else:
            log.warning(f"Stale lock found (PID {pid} no longer active). Removing and proceeding.")
            LOCK_PATH.unlink(missing_ok=True)

    LOCK_PATH.write_text(json.dumps({
        "pid":        os.getpid(),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }))
    log.info(f"Lock acquired — PID {os.getpid()}")


def _release_lock():
    """Remove the lockfile on clean exit or after any exception in main()."""
    LOCK_PATH.unlink(missing_ok=True)
    log.info("Lock released.")


def load_existing_cache():
    """Load existing raw_posts.json for deduplication. Returns dict keyed by post_id."""
    if RAW_POSTS_PATH.exists():
        try:
            with open(RAW_POSTS_PATH) as f:
                data = json.load(f)
            return {p["post_id"]: p for p in data.get("posts", [])}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            corrupt_path = RAW_POSTS_PATH.with_name("raw_posts.json.corrupt")
            RAW_POSTS_PATH.rename(corrupt_path)
            log.warning(
                f"raw_posts.json was corrupt — renamed to {corrupt_path.name}. Starting fresh."
            )
            return {}
    return {}


def save_cache(posts_by_id: dict, run_meta: dict):
    """Write final cache to raw_posts.json."""
    output = {
        "meta": run_meta,
        "posts": list(posts_by_id.values()),
    }
    with open(RAW_POSTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    log.info(f"Saved {len(posts_by_id)} posts → {RAW_POSTS_PATH}")


def noise_prefilter(score: int, comment_count: int) -> bool:
    """Return True if post should be dropped before triage. AND logic per config."""
    return score < MIN_SCORE and comment_count < MIN_COMMENTS


def stable_id(*parts) -> str:
    """Generate a stable post_id from source-specific identifiers."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def safe_get(url, headers, params=None, delay=2.1, retries=3, raw=False):
    """GET with retry logic and rate limit delay.

    raw=True: return response text instead of parsed JSON.
    Raises requests.HTTPError immediately on 403 (not retriable — caller handles it).
    """
    rate_limit_hits = 0
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=15)
        except requests.RequestException as e:
            log.warning(f"Request error (attempt {attempt+1}): {e}")
            time.sleep(delay * 2)
            continue

        if r.status_code == 429:
            rate_limit_hits += 1
            if rate_limit_hits > 5:
                log.error(f"Too many rate limit responses for {url} — aborting.")
                return None
            wait = int(r.headers.get("Retry-After", 30))
            log.warning(f"Rate limited (hit {rate_limit_hits}). Waiting {wait}s...")
            time.sleep(wait)
            continue

        if r.status_code == 403:
            r.raise_for_status()  # not retriable — propagate to caller

        if r.status_code == 200:
            time.sleep(delay)
            if raw:
                return r.text
            try:
                return r.json()
            except ValueError:
                log.warning(f"Non-JSON response from {url} (attempt {attempt+1}) — body: {r.text[:200]!r}")
                time.sleep(delay)
                continue

        log.warning(f"HTTP {r.status_code} for {url}")
        time.sleep(delay)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# HACKERNEWS INGESTION
# ─────────────────────────────────────────────────────────────────────────────

def fetch_hn_search(query: str, results: int = 30) -> list:
    """
    Query HackerNews via Algolia API — no auth, no rate limit concerns.
    https://hn.algolia.com/api
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {
        "query":       query,
        "tags":        "story",          # top-level posts only (no comments)
        "numericFilters": f"points>{HN_MIN_POINTS}",    # rough noise filter equivalent
        "hitsPerPage": results,
    }
    log.info(f"HackerNews search: '{query}'")
    data = safe_get(url, HN_HEADERS, params=params, delay=HN_DELAY)
    if not data or not isinstance(data, dict):
        return []
    return data.get("hits", [])


def fetch_hn_comments(story_id: str, max_comments: int = 20) -> list:
    """
    Fetch top-level comments for an HN story via Algolia item endpoint.
    """
    url = f"https://hn.algolia.com/api/v1/items/{story_id}"
    data = safe_get(url, HN_HEADERS, delay=HN_DELAY)
    if not data or not isinstance(data, dict):
        return []

    comments = []
    for child in data.get("children", [])[:max_comments]:
        text = (child.get("text") or "").strip()
        if text:
            comments.append({
                "author": child.get("author", ""),
                "score":  child.get("points", 0),
                "body":   text[:800],
            })
    return comments


def normalize_hn_post(hit: dict) -> dict | None:
    """Convert Algolia HN hit to CLAIRE normalized format."""
    story_id    = hit.get("objectID", "")
    score       = hit.get("points", 0)
    num_comments = hit.get("num_comments", 0)
    title       = (hit.get("title") or "").strip()

    if not story_id or not title:
        return None

    if noise_prefilter(score, num_comments):
        return None

    hn_permalink = f"https://news.ycombinator.com/item?id={story_id}"
    external_url = hit.get("url") or ""

    return {
        "post_id":            f"hn_{story_id}",
        "source_platform":    "hackernews",
        "source_type":        "search",
        "subreddit_category": "native",   # HN = always native AI discussion
        "subreddit":          "hackernews",
        "title":              title[:500],
        "body":               (hit.get("story_text") or "")[:2000],
        "score":              score,
        "comment_count":      num_comments,
        "url":                hn_permalink,
        "external_url":       external_url,
        "permalink":          hn_permalink,
        "author_flair":       "",
        "created_utc":        hit.get("created_at_i", 0),
        "fetched_at":         datetime.now(timezone.utc).isoformat(),
        "comments":           [],
        "triage":             {},
    }


def ingest_hackernews(existing_cache: dict, dry_run: bool) -> dict:
    """Full HackerNews ingestion pass."""
    new_posts = {}
    stats = {"fetched": 0, "prefiltered": 0, "deduplicated": 0, "new": 0}

    seen_story_ids = set()  # dedup across queries

    for query in HN_SEARCH_TERMS:
        hits = fetch_hn_search(query, results=HN_RESULTS_PER_QUERY)
        for hit in hits:
            stats["fetched"] += 1
            story_id = hit.get("objectID", "")

            if story_id in seen_story_ids:
                stats["deduplicated"] += 1
                continue
            seen_story_ids.add(story_id)

            post = normalize_hn_post(hit)
            if post is None:
                stats["prefiltered"] += 1
                continue

            pid = post["post_id"]
            if pid in existing_cache:
                stats["deduplicated"] += 1
                continue

            new_posts[pid] = post
            stats["new"] += 1

    log.info(f"HackerNews stats: {stats}")

    # Comment fetch
    if not dry_run:
        total = len(new_posts)
        for i, (pid, post) in enumerate(new_posts.items(), 1):
            story_id = pid.replace("hn_", "")
            log.info(f"HN comments [{i}/{total}] {pid}")
            post["comments"] = fetch_hn_comments(story_id, max_comments=COMMENTS_PER_POST)
            if i % 10 == 0:
                log.info(f"Burst protection — sleeping 15s after {i} comment fetches.")
                time.sleep(15)

    return new_posts


# ─────────────────────────────────────────────────────────────────────────────
# DEV.TO PRACTITIONER ARTICLES
# ─────────────────────────────────────────────────────────────────────────────

def fetch_devto_tag(tag: str, page: int = 1) -> list:
    """Fetch articles for a tag from dev.to public API.

    GET https://dev.to/api/articles?tag={tag}&per_page=30&page=N
    No auth required. Returns list of article dicts.
    """
    url    = f"{DEVTO_BASE_URL}/articles"
    params = {"tag": tag, "per_page": DEVTO_PER_PAGE, "page": page}
    headers = {
        "User-Agent":  "CLAIRE-ingest/1.0",
        "Accept":      "application/json",
    }
    resp = safe_get(url, headers=headers, params=params, delay=2.0)
    if resp is None:
        return []
    if isinstance(resp, list):
        log.info(f"dev.to tag={tag} page={page}: {len(resp)} articles")
        return resp
    log.warning(f"dev.to tag={tag} page={page}: unexpected response type {type(resp)}")
    return []


def normalize_devto_article(article: dict, min_reactions: int = 2) -> dict | None:
    """Convert dev.to article dict to CLAIRE normalized format.

    min_reactions is supplied per-tag by ingest_devto() from config["devto"]["tags"].
    """
    article_id    = article.get("id")
    title         = (article.get("title") or "").strip()
    body          = (article.get("description") or "").strip()
    reactions     = article.get("positive_reactions_count", 0)
    comments      = article.get("comments_count", 0)
    published_at  = article.get("published_at", "")
    url           = article.get("url") or article.get("canonical_url") or ""
    tag_list      = article.get("tag_list") or []

    if not article_id or not title:
        return None

    if reactions < min_reactions:
        return None

    # Parse created_utc
    try:
        created_utc = int(datetime.fromisoformat(
            published_at.replace("Z", "+00:00")).timestamp()) if published_at else 0
    except Exception:
        created_utc = 0

    return {
        "post_id":            f"devto_{article_id}",
        "source_platform":    "devto",
        "source_type":        "practitioner_article",
        "subreddit_category": "native",
        "subreddit":          "devto_anthropic",
        "title":              title[:500],
        "body":               body[:2000],
        "score":              reactions,
        "comment_count":      comments,
        "url":                url,
        "permalink":          url,
        "author_flair":       ", ".join(tag_list[:5]),
        "created_utc":        created_utc,
        "fetched_at":         datetime.now(timezone.utc).isoformat(),
        "comments":           [],   # comment fetch not implemented — body+description sufficient
        "triage":             {},
    }


def ingest_devto(existing_cache: dict, dry_run: bool) -> dict:
    """Full dev.to practitioner article ingestion pass."""
    new_posts = {}
    stats     = {"fetched": 0, "prefiltered": 0, "deduplicated": 0, "new": 0}
    seen_ids  = set()

    for tag_cfg in DEVTO_TAGS:
        tag           = tag_cfg["name"]
        min_reactions = tag_cfg["min_reactions"]
        for page in range(1, DEVTO_PAGES + 1):
            articles = fetch_devto_tag(tag, page=page)
            if not articles:
                break

            for article in articles:
                article_id = article.get("id")
                stats["fetched"] += 1

                if article_id in seen_ids:
                    stats["deduplicated"] += 1
                    continue
                seen_ids.add(article_id)

                pid = f"devto_{article_id}"
                if pid in existing_cache:
                    stats["deduplicated"] += 1
                    continue

                post = normalize_devto_article(article, min_reactions=min_reactions)
                if post is None:
                    stats["prefiltered"] += 1
                    continue

                new_posts[pid] = post
                stats["new"]  += 1

            time.sleep(1.5)  # polite delay between pages

    log.info(f"dev.to stats: {stats}")
    log.info(f"dev.to: {stats['new']} new posts")
    return new_posts


# ─────────────────────────────────────────────────────────────────────────────
# RUN LOG
# ─────────────────────────────────────────────────────────────────────────────

def append_run_log(meta: dict):
    """Append run summary to ingest_run_log.json for audit trail."""
    runs = []
    if RUN_LOG_PATH.exists():
        try:
            with open(RUN_LOG_PATH) as f:
                runs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            runs = []
    runs.append(meta)
    # Keep last 52 runs (one year of weekly runs)
    runs = runs[-52:]
    with open(RUN_LOG_PATH, "w") as f:
        json.dump(runs, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CLAIRE ingestion layer")
    parser.add_argument("--dry-run",  action="store_true", help="Fetch metadata only, skip comments, no write")
    parser.add_argument("--source",   choices=["hackernews", "forum", "both", "all", "gha"], default="all")
    args = parser.parse_args()

    _acquire_lock()
    try:
        _main(args)
    finally:
        _release_lock()


def _main(args):
    run_start = datetime.now(timezone.utc)
    log.info(f"CLAIRE ingest started — source={args.source} dry_run={args.dry_run}")

    existing_cache = load_existing_cache()
    log.info(f"Loaded {len(existing_cache)} existing posts from cache")

    all_new = {}

    if args.source in ("hackernews", "both", "all", "gha"):
        hn_posts = ingest_hackernews(existing_cache, args.dry_run)
        all_new.update(hn_posts)
        log.info(f"HackerNews: {len(hn_posts)} new posts")

    if args.source in ("forum", "all", "gha"):
        forum_posts = ingest_devto(existing_cache, args.dry_run)
        all_new.update(forum_posts)
        log.info(f"dev.to: {len(forum_posts)} new posts")

    # Merge new posts into existing cache
    merged = {**existing_cache, **all_new}

    run_meta = {
        "run_at":         run_start.isoformat(),
        "source":         args.source,
        "dry_run":        args.dry_run,
        "existing_posts": len(existing_cache),
        "new_posts":      len(all_new),
        "total_posts":    len(merged),
        "hn_new":         len([p for p in all_new.values() if p["source_platform"] == "hackernews"]),
        "forum_new":      len([p for p in all_new.values() if p["source_platform"] == "devto"]),
    }

    if not args.dry_run:
        save_cache(merged, run_meta)
        append_run_log(run_meta)
    else:
        log.info(f"DRY RUN — would write {len(merged)} posts. No files written.")
        log.info(json.dumps(run_meta, indent=2))

    log.info("CLAIRE ingest complete.")
    log.info(f"Run summary: {run_meta}")


if __name__ == "__main__":
    main()
