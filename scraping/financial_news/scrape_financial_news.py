import requests
import json
import time
from finlight_client import FinlightApi, ApiConfig
from finlight_client.models import GetArticlesParams
import os


FINLIGHT_API_KEY = os.getenv("FINLIGHT_API_KEY")

# Keywords for filtering investment-related content
INVESTMENT_KEYWORDS = [
    "stock", "market", "investment", "portfolio", "asset", "equity", "bond",
    "commodity", "finance", "economy", "trading", "shares", "dividend",
    "earnings", "valuation", "revenue", "profit", "EPS", "investor"
]

# Selected tickers for major companies (adjust based on tickers.json)
SELECTED_TICKERS = [
    "TSLA", "AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "JPM", "GS",
    "BAC", "WMT", "XOM", "CVX", "PFE", "JNJ"
]

def load_tickers(file_path="tickers.json"):
    """Load ticker symbols and company names from tickers.json."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tickers_data = json.load(f)
        # Create a dictionary mapping tickers to company names
        ticker_to_company = {item["ticker"]: item["company_name"] for item in tickers_data
                            if item["ticker"] in SELECTED_TICKERS}
        return ticker_to_company
    except Exception as e:
        print(f"Error loading tickers.json: {e}")
        # Fallback ticker-to-company mapping
        # return {
        #     "TSLA": "Tesla",
        #     "AAPL": "Apple",
        #     "NVDA": "NVIDIA",
        #     "MSFT": "Microsoft",
        #     "AMZN": "Amazon",
        #     "GOOGL": "Google",
        #     "META": "Meta",
        #     "JPM": "JPMorgan",
        #     "GS": "Goldman Sachs",
        #     "BAC": "Bank of America",
        #     "WMT": "Walmart",
        #     "XOM": "Exxon Mobil",
        #     "CVX": "Chevron",
        #     "PFE": "Pfizer",
        #     "JNJ": "Johnson & Johnson"
        #     "V": "Visa",
        #     "MA": "Mastercard",
        #     "UNH": "UnitedHealth",
        #     "COST": "Costco Wholesale",
        #     "PG": "Procter & Gamble",
        #     "HD": "The Home Depot",
        #     "NFLX": "Netflix",
        #     "ABBV": "AbbVie",
        #     "LLY": "Eli Lilly",
        #     "CRM": "Salesforce",
        #     "AVGO": "Broadcom",
        #     "ORCL": "Oracle",
        #     "KO": "The Coca-Cola",
        #     "PEP": "PepsiCo",
        #     "CSCO": "Cisco Systems"
        #     "ADBE": "Adobe",
        #     "AMD": "Advanced Micro Devices",
        #     "BA": "The Boeing",
        #     "CAT": "Caterpillar",
        #     "CMCSA": "Comcast",
        #     "DE": "Deere",
        #     "GE": "General Electric",
        #     "IBM": "International Business Machines",
        #     "INTU": "Intuit",
        #     "LOW": "Lowe's",
        #     "MDT": "Medtronic",
        #     "NKE": "NIKE",
        #     "SBUX": "Starbucks",
        #     "TMO": "Thermo Fisher Scientific",
        #     "UPS": "United Parcel Service"
        # }

        return {
            "ABT": "Abbott Laboratories",
            "ACN": "Accenture",
            "AMGN": "Amgen",
            "AXP": "American Express",
            "BLK": "BlackRock",
            "BMY": "Bristol-Myers Squibb",
            "C": "Citigroup",
            "DHR": "Danaher",
            "FDX": "FedEx",
            "GILD": "Gilead",
            "HON": "Honeywell",
            "MCD": "McDonald's",
            "MMM": "3M",
            "QCOM": "Qualcomm",
            "UNP": "Union Pacific"
        }

def get_article_links_finlight(ticker_to_company, num_samples):
    """Fetch article links using Finlight.me /v2/articles endpoint."""
    articles = []
    try:
        client = FinlightApi(
            config=ApiConfig(
                api_key=FINLIGHT_API_KEY
            )
        )

        
        PAGESIZE = 100
        page_num = 1
        while len(articles) < (num_samples):
            query = " OR ".join(INVESTMENT_KEYWORDS)
            # query = "stock"
            
            params = GetArticlesParams(
                query=query, 
                tickers=SELECTED_TICKERS,
                # sources=["reuters", "yahoo-finance", "forbes"],
                language="en",
                order="DESC",
                pageSize= PAGESIZE,
                page= page_num,
                excludeEmptyContent= True)

            response = client.articles.fetch_articles(params=params)
            
            
            data = response
            # print(data)
            
            if data.get("status") != "ok":
                print(f"Finlight.me API error: {data.get('message', 'Unknown error')}")
                return articles
            
            for article in data.get("articles", []):
                # print("ARTICLE!", article)
                title = article.get("title", "").lower()
                summary = article.get("summary", "").lower()
                sentiment = article.get("sentiment", "")
                confidence = article.get("confidence", "")
                # Filter for investment relevance and valid tickers
                for ticker, company in ticker_to_company.items():
                    company_lower = company.lower()
                    if company_lower in title or company_lower in summary:
                        articles.append({
                            "url": article.get("link", ""),
                            "source": article.get("source", ""),
                            "ticker": ticker,
                            "company": company,
                            "summary": summary,
                            "sentiment": sentiment,
                            "confidence": confidence
                        })
            
            print(f"Fetched {len(articles)} articles from Finlight.me so far")
            if len(data.get("articles", [])) < PAGESIZE:
                break  # No more articles
            page_num += 1
            time.sleep(1)  # Respect rate limit (100 requests/min)
        
        return articles[:400]
    except Exception as e:
        print(f"Error fetching articles from Finlight.me: {e}")
        return articles

def create_data_sample(url, source_name, ticker, company, summary, sentiment, confidence):
    """Create a data sample with fields for manual review."""
    return {
        "Context": "",  # Left blank as per request
        "Question": f"Is it a good time to invest in {company}?",
        "Answer": "",  # Left blank for manual review
        "Source": url,
        "Summary": summary,
        "Sentiment": sentiment,
        "Confidence": confidence,
        "Category": "Financial News",
        "Ticker": ticker,
        "Company": company,
    }

def scrape_financial_news(num_samples=300, tickers_file="tickers.json"):
    
    # Load ticker-to-company mapping
    ticker_to_company = load_tickers(tickers_file)
    
    data_samples = []
    article_links = get_article_links_finlight(ticker_to_company, num_samples)
    
    for link in article_links:
        if len(data_samples) >= num_samples:
            break
        sample = create_data_sample(
            url=link["url"],
            source_name=link["source"],
            ticker=link["ticker"],
            company=link["company"],
            summary=link["summary"],
            sentiment=link["sentiment"],
            confidence=link["confidence"]
        )
        data_samples.append(sample)
        print(f"Collected sample {len(data_samples)} from {link['url']} (Ticker: {link['ticker']})")
    
    if len(data_samples) > num_samples:
        data_samples = data_samples[:num_samples]
    elif len(data_samples) < num_samples:
        print(f"Warning: Only {len(data_samples)} samples collected, less than {num_samples}.")
    
    output_file = "financial_news_samples.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data_samples, f, indent=4)
    
    print(f"Saved {len(data_samples)} samples to {output_file}")
    return data_samples

if __name__ == "__main__":
    scrape_financial_news(num_samples=200, tickers_file="tickers.json")