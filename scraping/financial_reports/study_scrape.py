import os, json, time, pandas as pd
from edgar import set_identity, Company, use_local_storage
import yfinance as yf

# === CONFIG ===
EMAIL = ""
RATE_SLEEP = 0.2
CACHE = True

set_identity(EMAIL)
if CACHE:
    use_local_storage()
    os.environ["EDGAR_LOCAL_DATA_DIR"] = os.path.expanduser("~/.edgar")

output = {}

def fetch_sec_sample():
    ticker = "AAPL"  # 📝 Change if you want another company
    try:
        comp = Company(ticker)
        filing = comp.get_filings(form="10-K", is_xbrl=True).latest()
        xbrl = filing.xbrl()
        facts = xbrl.facts

        # Dump all facts as a DataFrame
        df = facts.query().to_dataframe()

        output['SEC'] = {
            "Ticker": ticker,
            "Filing Date": filing.filing_date,
            "Raw Facts": df.to_dict(orient='records')
        }

        # Save CSV for easy Excel/Sheets viewing
        csv_path = "sec_sample.csv"
        df.to_csv(csv_path, index=False)
        print(f"✅ SEC sample fetched for {ticker}")
        print(f"🔹 Total facts: {len(df)}")
        print(f"📄 SEC facts also saved to {csv_path}")
    except Exception as e:
        print(f"⚠️ SEC fetch error for {ticker}:", e)

def fetch_yahoo_sample():
    ticker = "BABA"  # 📝 Change if you want another company
    try:
        info = yf.Ticker(ticker).info

        output['Yahoo'] = {
            "Ticker": ticker,
            "Raw Info": info
        }

        print(f"✅ Yahoo sample fetched for {ticker}")
        print(f"🔹 Total fields: {len(info)}")
        print("🔹 Sample keys:", list(info.keys())[:10], "...")
    except Exception as e:
        print(f"⚠️ Yahoo fetch error for {ticker}:", e)

def safe_json(obj):
    """Handle non-JSON serializable types and truncate huge lists."""
    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    if isinstance(obj, (set,)):
        return list(obj)
    if isinstance(obj, (pd.Series, pd.DataFrame)):
        return obj.to_dict()
    if isinstance(obj, list) and len(obj) > 500:
        return obj[:500] + [f"... (truncated, total={len(obj)} items)"]
    return str(obj)

def save_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True, default=safe_json)
    print(f"📦 Saved JSON: {filename}")

if __name__ == "__main__":
    fetch_sec_sample()
    fetch_yahoo_sample()

    # Save separate JSONs
    if 'SEC' in output:
        save_json(output['SEC'], "sec_sample.json")
    if 'Yahoo' in output:
        save_json(output['Yahoo'], "yahoo_sample.json")

    print("🏁 Raw data dump completed.")
