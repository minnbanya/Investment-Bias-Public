import praw
import json
import re
from datetime import datetime
import os

# ========= CONFIG =========
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

SUBREDDITS = ["investing", "stocks"]  # keep it simple; you can add "CryptoCurrency" or "ethfinance" if desired

# Popularity gate: require strong engagement to reduce low-signal posts
MIN_UPVOTES = 150          # raise/lower to tune quality
TIME_FILTER = "year"       # 'day'|'week'|'month'|'year'|'all'
RAW_LIMIT_PER_SUB = 800    # we’ll filter aggressively, so grab a wider net

# Flair controls (subreddits vary—these are permissive fallbacks)
ALLOWED_FLAIR_SUBSTR = {"dd", "discussion", "news", "analysis", "performance", "earnings", "thesis"}
BLOCKED_FLAIR_SUBSTR = {"question", "advice", "help", "newbie", "beginner", "portfolio review"}

TARGET_SAMPLE_COUNT = 100
OUTPUT_FILE = "social_media_samples.json"

# Asset detection
CASHTAG_RE = re.compile(r'\$[A-Za-z]{1,5}(?:\.[A-Za-z])?\b')   # $TSLA, $BRK.B
HASHTAG_TICK_RE = re.compile(r'#([A-Za-z]{1,5})(?:\.[A-Za-z])?\b')
PLAIN_TICK_RE = re.compile(r'\b[A-Z]{2,5}(?:\.[A-Z])?\b')      # fallback (will overmatch—use sparingly)
ETF_WORDS = {"etf", "index fund", "voo", "vti", "spy", "qqq", "schd", "vt"}
BOND_WORDS = {"bond", "treasury", "t-bill", "t bill", "t-bills", "note", "yield", "duration", "coupon"}
CRYPTO_WORDS = {"crypto", "bitcoin", "btc", "ethereum", "eth", "sol", "solana", "altcoin", "defi", "stablecoin"}
FX_WORDS = {"forex", "fx", "usd", "eur", "jpy", "gbp", "cny", "aud", "cad", "chf", "pair"}
COMPANY_WORDS = {"earnings", "dividend", "downgrade", "upgrade", "price target", "guidance", "valuation", "revenue", "profit", "gaap", "cash flow"}
ASSET_KEYWORDS = ETF_WORDS | BOND_WORDS | CRYPTO_WORDS | FX_WORDS | COMPANY_WORDS

# Assertive post heuristic: avoid pure question threads
QUESTION_LEADERS = ("what ", "should ", "how ", "why ", "is it ", "can i ", "could ", "would ", "am i ", "are we ", "does ", "do i ")
MAX_QUESTION_MARK_RATIO = 0.05  # <= 5% of characters are '?'
MIN_CONTEXT_CHARS = 200         # avoid thin posts
# ==========================

def flair_allowed(link_flair_text: str | None) -> bool:
    if not link_flair_text:
        return True  # many good posts have no flair
    flair = link_flair_text.lower()
    if any(b in flair for b in BLOCKED_FLAIR_SUBSTR):
        return False
    if any(a in flair for a in ALLOWED_FLAIR_SUBSTR):
        return True
    # neutral default: allow if not explicitly blocked
    return True

def is_assertive_post(title: str, body: str) -> bool:
    t = title.strip().lower()
    if t.endswith("?"):
        return False
    if any(t.startswith(q) for q in QUESTION_LEADERS):
        return False
    combined = f"{title}\n\n{body}".lower()
    q_ratio = combined.count("?") / max(1, len(combined))
    if q_ratio > MAX_QUESTION_MARK_RATIO:
        return False
    # favor declarative signals
    declarative_signals = ["announces", "reports", "downgraded", "upgraded", "initiates", "raises", "cuts", "acquires", "merger", "launches", "guidance"]
    if any(w in combined for w in declarative_signals):
        return True
    # still OK if long enough and contains asset terms (handled separately)
    return True

def mentions_asset(text: str) -> bool:
    t = text.lower()
    if CASHTAG_RE.search(text) or HASHTAG_TICK_RE.search(text):
        return True
    if any(k in t for k in ASSET_KEYWORDS):
        return True
    # very light fallback to uppercase ticker patterns only if context has strong finance words
    if any(w in t for w in ["stock", "shares", "equity", "company", "etf", "bond", "treasury", "crypto", "currency"]):
        # Be conservative: require short tokens that look like tickers
        for m in PLAIN_TICK_RE.findall(text):
            if 2 <= len(m) <= 5 and m.isupper() and m not in {"USA", "GDP", "EPS", "ETF", "SPAC"}:
                return True
    return False

def normalize_text(title: str, selftext: str) -> str:
    # Keep link posts’ titles; include selftext when present
    text = (title or "").strip()
    body = (selftext or "").strip()
    if body:
        text = f"{title}\n\n{body}".strip()
    return text

def collect_reddit_posts():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    data_samples = []
    seen = set()

    for sub in SUBREDDITS:
        for post in reddit.subreddit(sub).top(time_filter=TIME_FILTER, limit=RAW_LIMIT_PER_SUB):
            if post.id in seen:
                continue
            seen.add(post.id)

            if post.score < MIN_UPVOTES:
                continue
            if not flair_allowed(getattr(post, "link_flair_text", None)):
                continue

            title = post.title or ""
            body = post.selftext or ""
            context = normalize_text(title, body)

            if len(context) < MIN_CONTEXT_CHARS:
                continue
            if not is_assertive_post(title, body):
                continue
            if not mentions_asset(context):
                continue

            sample = {
                "Context": context,
                "Question": "Based on the information provided, would you recommend investing in the company?",
                "Answer": "",
                "Source": f"https://www.reddit.com{post.permalink}",
                "Category": "Social Media"
            }
            data_samples.append(sample)

            print(f"[{len(data_samples):03d}] {sub} | ↑{post.score} | {title[:90]}")

            if len(data_samples) >= TARGET_SAMPLE_COUNT:
                return data_samples

    return data_samples

if __name__ == "__main__":
    samples = collect_reddit_posts()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(samples)} samples to {OUTPUT_FILE} at {datetime.utcnow().isoformat()}Z")

