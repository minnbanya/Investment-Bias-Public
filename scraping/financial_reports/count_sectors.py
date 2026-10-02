import json
from collections import Counter

# Load tickers from JSON
try:
    with open("tickers.json", "r") as f:
        ticker_data = json.load(f)
    tickers = ticker_data["tickers"]
except FileNotFoundError:
    print("❌ Error: tickers.json not found in the working directory.")
    exit(1)

# Count tickers per sector
sector_counts = Counter(ticker["sector"] for ticker in tickers)
total_tickers = len(tickers)

# Print sector distribution
print(f"✅ Total tickers: {total_tickers}")
print("\n📊 Sector Distribution:")
for sector, count in sorted(sector_counts.items(), key=lambda x: (-x[1], x[0])):
    percentage = (count / total_tickers) * 100
    print(f"  - {sector}: {count} tickers ({percentage:.2f}%)")