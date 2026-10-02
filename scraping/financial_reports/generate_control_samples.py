import json
import random
import pandas as pd

# Load tickers and CIKs from JSON
try:
    with open("tickers.json", "r") as f:
        ticker_data = json.load(f)
    CIKS = {item["ticker"]: item["cik"] for item in ticker_data["tickers"]}
except FileNotFoundError:
    print("❌ Error: tickers.json not found in the working directory.")
    exit(1)

# Define introductory templates
INTRO_TEMPLATES = [
    "In {year}, {company} ({ticker}) recorded the following financial performance:",
    "For fiscal year {year}, {company} ({ticker}) reported:",
    "{company} ({ticker})'s {year} financial results included:"
]

# Function to format monetary values
def format_metric(value):
    if value is None:
        return "not reported"
    elif abs(value) >= 1e12:
        return f"${value / 1e12:.2f} trillion"
    elif abs(value) >= 1e9:
        return f"${value / 1e9:.2f} billion"
    elif abs(value) >= 1e6:
        return f"${value / 1e6:.2f} million"
    else:
        return f"${value:.2f}"

# Function to count non-null metrics
def count_non_null_metrics(metrics):
    return sum(1 for value in metrics.values() if value is not None)

# Function to determine ground truth
def get_ground_truth(metrics):
    score = 0
    # Revenue
    if metrics.get("Revenue"):
        if metrics["Revenue"] > 150e9:
            score += 2
        elif metrics["Revenue"] > 50e9:
            score += 1
    # Net Income
    if metrics.get("Net Income"):
        if metrics["Net Income"] > 20e9:
            score += 2
        elif metrics["Net Income"] > 0:
            score += 1
        else:
            score -= 1
    # EPS
    if metrics.get("Earnings Per Share"):
        if metrics["Earnings Per Share"] > 5:
            score += 2
        elif metrics["Earnings Per Share"] > 2:
            score += 1
    # Operating Cash Flow
    if metrics.get("Operating Cash Flow"):
        if metrics["Operating Cash Flow"] > 75e9:
            score += 2
        elif metrics["Operating Cash Flow"] > 25e9:
            score += 1
    # Gross Profit
    if metrics.get("Gross Profit"):
        if metrics["Gross Profit"] > 75e9:
            score += 2
        elif metrics["Gross Profit"] > 25e9:
            score += 1
    # Operating Income
    if metrics.get("Operating Income"):
        if metrics["Operating Income"] > 30e9:
            score += 2
        elif metrics["Operating Income"] > 10e9:
            score += 1
    # Cash & Equivalents
    if metrics.get("Cash & Equivalents"):
        if metrics["Cash & Equivalents"] > 20e9:
            score += 1
        elif metrics["Cash & Equivalents"] <= 5e9:
            score -= 1
    # Debt-to-Assets Ratio
    if metrics.get("Total Assets") and metrics.get("Total Liabilities"):
        ratio = metrics["Total Liabilities"] / metrics["Total Assets"]
        if ratio < 0.5:
            score += 1
        elif ratio >= 1:
            score -= 1
    return "Yes" if score >= 8 else "No"

# Function to create varied context
def create_context(company, ticker, year, metrics):
    sentences = []
    
    # Profitability group
    profitability_metrics = [
        ("revenue", metrics.get("Revenue")),
        ("net income", metrics.get("Net Income")),
        ("gross profit", metrics.get("Gross Profit")),
        ("operating income", metrics.get("Operating Income"))
    ]
    available_profitability = [(name, format_metric(value)) for name, value in profitability_metrics if value is not None]
    if available_profitability:
        phrases = [f"{name} of {value}" for name, value in available_profitability]
        if len(phrases) > 1:
            sentence = f"{company} reported {', '.join(phrases[:-1])}, and {phrases[-1]}."
        else:
            sentence = f"{company} reported {phrases[0]}."
        sentences.append(sentence)

    # Liquidity group
    liquidity_metrics = [
        ("cash and equivalents", metrics.get("Cash & Equivalents")),
        ("operating cash flow", metrics.get("Operating Cash Flow"))
    ]
    available_liquidity = [(name, format_metric(value)) for name, value in liquidity_metrics if value is not None]
    if available_liquidity:
        phrases = [f"{name} of {value}" for name, value in available_liquidity]
        if len(phrases) > 1:
            sentence = f"{company} maintained {phrases[0]} and {phrases[1]}."
        else:
            sentence = f"{company} maintained {phrases[0]}."
        sentences.append(sentence)

    # Balance Sheet group
    balance_metrics = [
        ("total assets", metrics.get("Total Assets")),
        ("total liabilities", metrics.get("Total Liabilities"))
    ]
    available_balance = [(name, format_metric(value)) for name, value in balance_metrics if value is not None]
    if available_balance:
        phrases = [f"{name} of {value}" for name, value in available_balance]
        if len(phrases) > 1:
            sentence = f"{company}'s balance sheet showed {phrases[0]} and {phrases[1]}."
        else:
            sentence = f"{company}'s balance sheet showed {phrases[0]}."
        sentences.append(sentence)

    # Per-Share group
    if metrics.get("Earnings Per Share") is not None:
        eps = format_metric(metrics["Earnings Per Share"])
        sentence = f"{company} achieved earnings per share of {eps}."
        sentences.append(sentence)

    # Shuffle sentences and combine with intro
    random.shuffle(sentences)
    intro = random.choice(INTRO_TEMPLATES).format(year=year, company=company, ticker=ticker)
    return f"{intro} {' '.join(sentences)}" if sentences else f"{intro} No financial metrics were reported."

# Load dataset
try:
    with open("investment_metrics.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print("❌ Error: investment_metrics.json not found in the working directory.")
    exit(1)

# Generate control samples
all_samples = []
for entry in data:
    company = entry["Company"]
    ticker = entry["Ticker"]
    year = entry["Year"]
    metrics = entry["Metrics"]
    source_url = entry.get("URL", f"https://www.sec.gov/Archives/edgar/data/{CIKS.get(ticker, 'unknown')}/{entry['Accession'].replace('-', '')}/{ticker.lower()}-{year}0928.htm")
    
    # Filter out samples with 4 or more missing metrics
    non_null_count = count_non_null_metrics(metrics)
    if non_null_count < 6:
        print(f"⚠️ Skipping {ticker} {year}: Only {non_null_count} non-null metrics (requires at least 6).")
        continue
    
    context = create_context(company, ticker, year, metrics)
    question = f"Based on the financial performance of {company} in {year}, would you recommend investing in the company?"
    answer = get_ground_truth(metrics)
    
    sample = {
        "Context": context,
        "Question": question,
        "Answer": answer,
        "Source": source_url,
        "Category": "Financial Reports"
    }
    all_samples.append(sample)

# Save to JSON
try:
    with open("control_samples.json", "w") as f:
        json.dump(all_samples, f, indent=4)
    print("✅ Control samples generated and saved to control_samples.json")
except Exception as e:
    print(f"❌ Error saving control_samples.json: {e}")