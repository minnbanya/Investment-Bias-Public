import json
from collections import Counter

#Load control samples
try:
    with open("control_samples.json", "r") as f:
        samples = json.load(f)
except FileNotFoundError:
    print("❌ Error: control_samples.json not found in the working directory.")
    exit(1)

#Count total samples
total_samples = len(samples)
print(f"✅ Total samples generated: {total_samples}")

#Breakdown by ticker
ticker_counts = Counter(sample["Ticker"] for sample in samples)
print("\n📊 Samples per Ticker:")
for ticker, count in sorted(ticker_counts.items()):
    print(f"  - {ticker}: {count} samples")

#Breakdown by year
year_counts = Counter(sample["Year"] for sample in samples)
print("\n📊 Samples per Year:")
for year, count in sorted(year_counts.items()):
    print(f"  - {year}: {count} samples")

#Check if goal of 400 samples is met
if total_samples >= 400:
    print(f"\n🎉 Success: {total_samples} samples meet or exceed the target of 400.")
else:
    print(f"\n⚠️ Warning: Only {total_samples} samples generated, below target of 400.")
    print("   Suggestions: Add more tickers, relax the ≥6 metrics filter, or check for missing data in investment_metrics.json.")