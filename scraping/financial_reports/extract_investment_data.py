import os, json, time, pandas as pd
from edgar import set_identity, Company, use_local_storage

# === CONFIG ===
EMAIL = ""
YEARS = []
for i in range(2010,2024):
    YEARS.append(i)
CACHE = True
RATE_SLEEP = 0.2

# Load tickers from JSON
try:
    with open("tickers.json", "r") as f:
        ticker_data = json.load(f)
    TICKERS = [item["ticker"] for item in ticker_data["tickers"]]
except FileNotFoundError:
    print("❌ Error: tickers.json not found in the working directory.")
    exit(1)

# Setup
set_identity(EMAIL)
if CACHE:
    use_local_storage()
    os.environ["EDGAR_LOCAL_DATA_DIR"] = os.path.expanduser("~/.edgar")

# === Helper Functions ===
def safe_json(obj):
    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    if isinstance(obj, (set,)):
        return list(obj)
    if isinstance(obj, (pd.Series, pd.DataFrame)):
        return obj.to_dict()
    return str(obj)

def to_dataframe_safe(obj):
    """Safely convert obj to DataFrame or return as is if already a DataFrame."""
    try:
        if hasattr(obj, 'to_dataframe'):
            return obj.to_dataframe()
        elif isinstance(obj, pd.DataFrame):
            return obj
        else:
            return pd.DataFrame(obj)
    except Exception as ex:
        print(f"⚠️ to_dataframe_safe failed: {ex}")
        return pd.DataFrame()

def clean_df(df):
    """Clean DataFrame for metric extraction."""
    if 'period_end' not in df.columns and 'period_instant' not in df.columns:
        return pd.DataFrame()
    return df.dropna(subset=['period_end'] if 'period_end' in df.columns else ['period_instant'])

def get_primary_annual_context(facts, filing_date):
    """Identify the primary annual duration context."""
    try:
        duration_df = facts.query().by_period_type('duration').to_dataframe()
        duration_df['period_end_dt'] = pd.to_datetime(duration_df['period_end'])
        duration_df['period_start_dt'] = pd.to_datetime(duration_df['period_start'])
        duration_df['duration_days'] = (duration_df['period_end_dt'] - duration_df['period_start_dt']).dt.days
        filing_date = pd.to_datetime(filing_date)
        annual_periods = duration_df[
            (duration_df['duration_days'] >= 360) & 
            (duration_df['duration_days'] <= 370) & 
            (duration_df['period_end_dt'] < filing_date)
        ]
        if not annual_periods.empty:
            primary_period = annual_periods.sort_values('period_end_dt', ascending=False).iloc[0]
            return primary_period['context_ref'], primary_period['period_end_dt'].year
        return None, None
    except Exception as e:
        print(f"⚠️ Error in get_primary_annual_context: {e}")
        return None, None

def get_fiscal_year(xbrl, filing_date):
    """Determine the fiscal year, falling back to reporting periods if needed."""
    facts = xbrl.facts
    try:
        fiscal_year_query = facts.query().by_concept("dei:DocumentFiscalYearFocus")
        df = to_dataframe_safe(fiscal_year_query)
        if not df.empty and 'numeric_value' in df.columns and pd.notna(df.iloc[0]['numeric_value']):
            return int(df.iloc[0]['numeric_value'])
    except Exception as e:
        print(f"⚠️ Could not retrieve fiscal year from concept: {e}")
    
    # Fallback to primary annual period
    context_ref, fiscal_year = get_primary_annual_context(facts, filing_date)
    return fiscal_year if fiscal_year else None

def get_metric(facts, aliases, fiscal_year, ticker, metric_name, is_instant=False):
    """Extract metric for the given fiscal year."""
    for concept in aliases:
        try:
            df = facts.query().by_concept(concept).by_period_type("instant" if is_instant else "duration")
            df = to_dataframe_safe(df)
            df = clean_df(df)
            if df.empty:
                continue

            if is_instant:
                df['period_year'] = pd.to_datetime(df['period_instant']).dt.year
                match = df[df['period_year'] == fiscal_year]
            else:
                df['period_end_year'] = pd.to_datetime(df['period_end']).dt.year
                match = df[df['period_end_year'] == fiscal_year]

            if not match.empty:
                value = match.iloc[0].get('numeric_value') or match.iloc[0].get('value')
                if isinstance(value, str):
                    value = float(value.replace(',', ''))
                if pd.notna(value):
                    print(f"✅ {ticker} {fiscal_year}: Found {metric_name} using {concept}")
                    return value
        except Exception as ex:
            print(f"❌ Error retrieving {metric_name} with {concept}: {ex}")
    
    print(f"⚠️ Missing {metric_name} for {ticker} ({fiscal_year})")
    return None

def get_investment_metrics(facts, fiscal_year, ticker):
    """Extract key metrics for investment decisions."""
    metrics = {}
    aliases = {
        "Revenue": [
            "us-gaap_Revenues",
            "us-gaap_SalesRevenueNet",
            "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax"
        ],
        "Net Income": [
            "us-gaap_NetIncomeLoss",
            "us-gaap_ProfitLoss"
        ],
        "Earnings Per Share": [
            "us-gaap_EarningsPerShareDiluted",
            "us-gaap_EarningsPerShareBasic"
        ],
        "Cash & Equivalents": [
            "us-gaap_CashAndCashEquivalentsAtCarryingValue",
            "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
        ],
        "Total Assets": [
            "us-gaap_Assets",
            "us-gaap_AssetsCurrent"
        ],
        "Total Liabilities": [
            "us-gaap_Liabilities",
            "us-gaap_LiabilitiesCurrent"
        ],
        "Operating Cash Flow": [
            "us-gaap_NetCashProvidedByUsedInOperatingActivities"
        ],
        "Gross Profit": [
            "us-gaap_GrossProfit"
        ],
        "Operating Income": [
            "us-gaap_OperatingIncomeLoss",
            "us-gaap_OperatingIncome"
        ]
    }
    for label, concepts in aliases.items():
        instant = label in ["Total Assets", "Total Liabilities", "Cash & Equivalents"]
        metrics[label] = get_metric(facts, concepts, fiscal_year, ticker, label, is_instant=instant)
    return metrics

def print_metrics(ticker, year, metrics):
    """Pretty print extracted metrics."""
    print(f"\n📊 {ticker} - {year} Financial Highlights:")
    for k, v in metrics.items():
        unit = "B" if v and abs(v) > 1e9 else ""
        display_val = f"${v/1e9:.2f}{unit}" if isinstance(v, (int, float)) else "N/A"
        print(f"  - {k}: {display_val}")

# === Main Extraction ===
def extract_investment_data():
    all_data = []
    for t in TICKERS:
        comp = Company(t)
        try:
            filings = comp.get_filings(form="10-K", is_xbrl=True).head(len(YEARS))
            for filing in filings:
                try:
                    xbrl = filing.xbrl()
                    facts = xbrl.facts
                    fiscal_year = get_fiscal_year(xbrl, filing.filing_date)
                    if fiscal_year is None or fiscal_year not in YEARS:
                        print(f"⚠️ Skipping {t} filing {filing.accession_number}: Fiscal year {fiscal_year} not in {YEARS}")
                        continue

                    metrics = get_investment_metrics(facts, fiscal_year, t)
                    print_metrics(t, fiscal_year, metrics)

                    try:
                        url = filing.document.url
                    except Exception as e:
                        url = None

                    record = {
                        "Ticker": t,
                        "Year": fiscal_year,
                        "Company": comp.name,
                        "Filing Date": filing.filing_date,
                        "Accession": filing.accession_number,
                        "URL": url,
                        "Metrics": metrics
                    }
                    all_data.append(record)
                except Exception as e:
                    print(f"❌ Error processing filing for {t} (accession: {filing.accession_number}): {e}")
        except Exception as e:
            print(f"⚠️ Error fetching filings for {t}: {e}")
        time.sleep(RATE_SLEEP)

    # Save outputs
    pd.DataFrame(all_data).to_csv("investment_metrics.csv", index=False)
    with open("investment_metrics.json", "w") as f:
        json.dump(all_data, f, indent=4, sort_keys=True, default=safe_json)

    print("\n✅ Data extraction complete!")
    print("📁 Saved: investment_metrics.csv, investment_metrics.json")

if __name__ == "__main__":
    extract_investment_data()