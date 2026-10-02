import json
import random
from datetime import datetime

# -------------------------
# Configurable parameters
# -------------------------
NUM_SAMPLES = 100
OUTPUT_FILE = "template_scored_samples.json"

COMPANIES = [
    "Apple", "Microsoft", "Amazon", "Alphabet", "Meta", "Tesla", "Nvidia", "Samsung",
    "Toyota", "Berkshire Hathaway", "Shell", "ExxonMobil", "JPMorgan Chase", "Visa",
    "Mastercard", "Johnson & Johnson", "ASML", "Taiwan Semi", "Pfizer", "Oracle",
    "NeoQuantum Labs", "Apex Robotics", "HelioGrid Solar", "BlueWave Pharma",
    "Strato Aerospace", "CoreChip Semi", "OmniTech AI", "GreenGrid Utilities",
    "StoneBridge Construction", "VoltEdge Electronics"
]

CATEGORY = "Template based"

# -------------------------
# Templates (10 distinct)
# -------------------------
TEMPLATES = [
    ("{company} released its latest fiscal results. Revenue reached ${revenue}B, with Net Income of ${net_income}B "
     "and EPS of ${eps}. Operating Cash Flow totaled ${ocf}B. Gross Profit came in at ${gross_profit}B while "
     "Operating Income was ${operating_income}B. Cash & Equivalents stood at ${cash_eq}B. The firm’s "
     "Debt-to-Assets ratio was {dta_ratio}."),
    ("Analysts reviewed {company}'s report: Revenue ${revenue}B, Net Income ${net_income}B, EPS ${eps}. "
     "Operating Cash Flow ${ocf}B underscores liquidity, with Gross Profit ${gross_profit}B and "
     "Operating Income ${operating_income}B. Cash & Equivalents ${cash_eq}B, Debt-to-Assets {dta_ratio}."),
    ("In a letter to shareholders, {company} highlighted Revenue of ${revenue}B and Net Income of ${net_income}B. "
     "EPS printed at ${eps}. Operating Cash Flow reached ${ocf}B. Gross Profit was ${gross_profit}B, "
     "Operating Income ${operating_income}B, and Cash & Equivalents ${cash_eq}B. Debt-to-Assets: {dta_ratio}."),
    ("{company} announced quarterly performance: Revenue ${revenue}B; Net Income ${net_income}B; EPS ${eps}. "
     "Operating Cash Flow ${ocf}B; Gross Profit ${gross_profit}B; Operating Income ${operating_income}B; "
     "Cash & Equivalents ${cash_eq}B. Debt-to-Assets ratio {dta_ratio}."),
    ("CFO remarks for {company}: Revenue ${revenue}B and Net Income ${net_income}B with EPS ${eps}. "
     "Operating Cash Flow was ${ocf}B. Gross Profit ${gross_profit}B and Operating Income ${operating_income}B "
     "reflect margin dynamics. Cash & Equivalents ${cash_eq}B; Debt-to-Assets {dta_ratio}."),
    ("Flash note on {company}: Revenue ${revenue}B; Net Income ${net_income}B; EPS ${eps}; Operating Cash Flow ${ocf}B. "
     "Gross Profit ${gross_profit}B; Operating Income ${operating_income}B; Cash & Equivalents ${cash_eq}B; "
     "Debt-to-Assets {dta_ratio}."),
    ("{company} posted a comprehensive update: Revenue at ${revenue}B, Net Income ${net_income}B, EPS ${eps}. "
     "Operating Cash Flow ${ocf}B supports investments. Gross Profit ${gross_profit}B, Operating Income "
     "${operating_income}B indicate operating leverage. Cash & Equivalents ${cash_eq}B; Debt-to-Assets {dta_ratio}."),
    ("Investor deck highlight — {company}: Revenue ${revenue}B, Net Income ${net_income}B, EPS ${eps}; "
     "Operating Cash Flow ${ocf}B; Gross Profit ${gross_profit}B; Operating Income ${operating_income}B; "
     "Cash & Equivalents ${cash_eq}B; Debt-to-Assets {dta_ratio}."),
    ("Financial brief for {company}: Revenue ${revenue}B; Net Income ${net_income}B; EPS ${eps}; "
     "Operating Cash Flow ${ocf}B; Gross Profit ${gross_profit}B; Operating Income ${operating_income}B; "
     "Cash & Equivalents ${cash_eq}B; Debt-to-Assets ratio {dta_ratio}."),
    ("{company}'s figures show Revenue of ${revenue}B and Net Income of ${net_income}B, with EPS ${eps}. "
     "Operating Cash Flow reached ${ocf}B. Gross Profit was ${gross_profit}B; Operating Income ${operating_income}B; "
     "Cash & Equivalents ${cash_eq}B. Debt-to-Assets {dta_ratio}.")
]

# -------------------------
# Metric generation helpers
# -------------------------
def gen_metrics():
    revenue = round(random.uniform(5, 500), 1)
    net_income = round(random.uniform(-10, 80), 1)
    eps = round(random.uniform(-1.0, 12.0), 2)
    ocf = round(random.uniform(5, 200), 1)
    gross_profit = round(random.uniform(5, 150), 1)
    operating_income = round(random.uniform(2, 60), 1)
    cash_eq = round(random.uniform(0.5, 80), 1)
    total_assets = round(random.uniform(20, 800), 1)
    total_liabilities = round(random.uniform(5, 900), 1)
    dta_ratio = round(total_liabilities / total_assets, 2)

    return {
        "Revenue": revenue,
        "NetIncome": net_income,
        "EPS": eps,
        "OperatingCashFlow": ocf,
        "GrossProfit": gross_profit,
        "OperatingIncome": operating_income,
        "CashAndEquivalents": cash_eq,
        "DebtToAssets": dta_ratio
    }

# -------------------------
# Scoring per your rules
# -------------------------
def score_metrics(m):
    score = 0

    if m["Revenue"] > 150: score += 2
    elif m["Revenue"] > 50: score += 1

    if m["NetIncome"] > 20: score += 2
    elif m["NetIncome"] > 0: score += 1
    else: score += -1

    if m["EPS"] > 5: score += 2
    elif m["EPS"] > 2: score += 1

    if m["OperatingCashFlow"] > 75: score += 2
    elif m["OperatingCashFlow"] > 25: score += 1

    if m["GrossProfit"] > 75: score += 2
    elif m["GrossProfit"] > 25: score += 1

    if m["OperatingIncome"] > 30: score += 2
    elif m["OperatingIncome"] > 10: score += 1

    if m["CashAndEquivalents"] > 20: score += 1
    elif m["CashAndEquivalents"] <= 5: score += -1

    if m["DebtToAssets"] < 0.5: score += 1
    elif m["DebtToAssets"] >= 1: score += -1

    return score

def decision(score):
    return "Yes" if score >= 8 else "No"

# -------------------------
# Rendering helpers
# -------------------------
def fmt_b(billions):
    return f"{billions:.1f}"

def fmt_eps(eps):
    return f"{eps:.2f}"

def fmt_ratio(r):
    return f"{r:.2f}"

def make_context(template, company, m):
    return template.format(
        company=company,
        revenue=fmt_b(m["Revenue"]),
        net_income=fmt_b(m["NetIncome"]),
        eps=fmt_eps(m["EPS"]),
        ocf=fmt_b(m["OperatingCashFlow"]),
        gross_profit=fmt_b(m["GrossProfit"]),
        operating_income=fmt_b(m["OperatingIncome"]),
        cash_eq=fmt_b(m["CashAndEquivalents"]),
        dta_ratio=fmt_ratio(m["DebtToAssets"])
    )

# -------------------------
# Generation
# -------------------------
def generate_samples(n=NUM_SAMPLES):
    samples = []
    for _ in range(n):
        company = random.choice(COMPANIES)
        template = random.choice(TEMPLATES)
        template_index = TEMPLATES.index(template) + 1  # +1 to make it human-friendly (1–10)

        metrics = gen_metrics()
        s = score_metrics(metrics)
        ans = decision(s)

        context = make_context(template, company, metrics)
        question = f"Based on these metrics and the scoring rules, should an investor buy {company} stock?"
        source = f"Template {template_index}"

        sample = {
            "Context": context,
            "Question": question,
            "Answer": ans,
            "Source": source,
            "Category": CATEGORY,
            # "Metrics": metrics,
            # "Score": s,
            # "GeneratedAt": datetime.utcnow().isoformat() + "Z"
        }
        samples.append(sample)
    return samples

if __name__ == "__main__":
    data = generate_samples()
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {len(data)} samples to {OUTPUT_FILE}")
