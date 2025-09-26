import requests
import json
import os
from app.config import supabase
from app.aimodels.openai_service import generate_structured_response_openai
from openai import APIStatusError

# --- Helper Functions ---

def analyze_transactions(transactions: list) -> dict:
    """Calculates financial summary from transactions."""
    if not transactions:
        return {"total_income": 0, "total_expenses": 0, "net_savings": 0, "transaction_count": 0}

    total_income = sum(float(txn.get('credit', 0) or 0) for txn in transactions)
    total_expenses = sum(float(txn.get('debit', 0) or 0) for txn in transactions)
    net_savings = total_income - total_expenses

    net_monthly_savings = round(net_savings, 2)

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_savings": round(net_savings, 2),
        "net_monthly_savings": net_monthly_savings,
        "transaction_count": len(transactions)
    }

def fetch_market_data() -> dict:
    """Fetches stocks, mutual funds, AND the latest financial news."""
    api_key = os.getenv("INDIAN_STOCK_API_KEY")
    if not api_key:
        return {"error": "API key is not configured."}
    base_url = "https://stock.indianapi.in"
    headers = {'X-Api-Key': api_key}

    def process_stock_data(stock_list: list) -> list:
        # Extracts key info from complex stock objects
        processed_list = []
        if not isinstance(stock_list, list): return processed_list
        for stock in stock_list:
            processed_list.append({"company": stock.get("company"), "price": stock.get("price"), "percent_change": stock.get("percent_change"), "overall_rating": stock.get("overall_rating")})
        return processed_list

    def process_mutual_fund_data(mf_list: list) -> list:
        # Processes mutual fund data to extract key info
        processed_list = []
        if not isinstance(mf_list, list): return processed_list
        for mf in mf_list:
            processed_list.append({"fund_name": mf.get("fund_name"),"1_year_return": mf.get("1_year_return"), "3_year_return": mf.get("3_year_return")})
        return processed_list

    def process_news_data(news_list: list) -> list:
        # Extracts just the title and summary to keep the prompt lean
        processed_list = []
        if not isinstance(news_list, list): return processed_list
        for article in news_list:
             processed_list.append({"title": article.get("title"), "summary": article.get("summary")})
        return processed_list

    try:
        # Make all API calls, including the new /news endpoint
        bse_res = requests.get(f"{base_url}/BSE_most_active", headers=headers)
        nse_res = requests.get(f"{base_url}/NSE_most_active", headers=headers)
        mf_res = requests.get(f"{base_url}/mutual_funds", headers=headers)
        news_res = requests.get(f"{base_url}/news", headers=headers)

        # Check for errors
        for res in [bse_res, nse_res, mf_res, news_res]:
            res.raise_for_status()

        bse_data = bse_res.json()
        nse_data = nse_res.json()
        mf_data = mf_res.json()
        news_data = news_res.json()

        # Flatten the nested mutual fund data structure
        all_mfs = []
        if isinstance(mf_data, dict):
            for main_category, sub_categories in mf_data.items():
                if isinstance(sub_categories, dict):
                    for sub_category, funds in sub_categories.items():
                        if isinstance(funds, list):
                            all_mfs.extend(funds)

        # Sort mutual funds by 1-year return
        sorted_mfs = sorted([mf for mf in all_mfs if mf.get("1_year_return") is not None], key=lambda x: x["1_year_return"], reverse=True)

        return {
            "bse_most_active": process_stock_data(bse_data[:5]),
            "nse_most_active": process_stock_data(nse_data[:5]),
            "popular_mutual_funds": process_mutual_fund_data(sorted_mfs[:5]),
            "latest_news": process_news_data(news_data[:4]) # Take the top 4 news articles
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market data: {e}")
        return {"error": str(e)}

# --- Main Orchestration Function (Enhanced) ---
async def generate_investment_advice(user_id: str, risk_profile: str, investment_goal: str, investment_horizon: str) -> dict:
    response = supabase.table("transactions").select("*").eq("user_id", user_id).execute()
    financial_summary = analyze_transactions(response.data)
    market_data = fetch_market_data()

    if "error" in market_data:
         return {"error": f"Failed to fetch market data: {market_data['error']}"}

    # The new prompt now includes a section for news analysis
    prompt = f"""
    You are an expert financial advisor for the Indian market named WealthWise. Your goal is to provide a practical, personalized, and actionable investment plan. Generate a response in valid JSON.

    **USER CONTEXT:**
    - Risk Tolerance: "{risk_profile}"
    - Stated Investment Goal: "{investment_goal}"
    - Investment Horizon: "{investment_horizon}"
    - Estimated Net Monthly Savings: {financial_summary['net_monthly_savings']} INR

    **MARKET CONTEXT:**
    - Today's Most Active Stocks (NSE): {json.dumps(market_data['nse_most_active'])}
    - Top Performing Mutual Funds: {json.dumps(market_data['popular_mutual_funds'])}
    - Recent Financial News: {json.dumps(market_data['latest_news'])}

    **YOUR TASK:**
    Based on all the above information, generate a practical investment plan.
    1. **First, analyze the 'Recent Financial News' to determine the overall market sentiment. Synthesize this into a very short, one-sentence insight.**
    2. Suggest a mix of 1-2 stocks AND 1-2 mutual funds that align with the user's profile and the market sentiment.
    3. Calculate and recommend a monthly SIP amount based on their net monthly savings.
    4. For each suggestion, provide a brief 'reasoning'.
    5. Provide a 'summary' of the strategy and a 'disclaimer'.

    **OUTPUT FORMAT (must be valid JSON):**
    {{
      "market_insight": "A very short, one-sentence summary of the current market sentiment based on the news.",
      "summary": "A brief overview of the investment strategy...",
      "recommended_monthly_sip": "A calculated SIP amount in INR...",
      "recommendations": [
        {{
          "instrument_name": "Name of Stock/Fund",
          "type": "Stock or Mutual Fund",
          "reasoning": "Why this is recommended for their specific goal and horizon...",
          "risk_level_match": "Explains how it matches their risk profile."
        }}
      ],
      "disclaimer": "This is AI-generated advice for informational purposes only..."
    }}
    """

    ai_advice_json = {}
    try:
        ai_response_text = await generate_structured_response_openai(prompt)
        ai_advice_json = json.loads(ai_response_text)
    except Exception as e:
        ai_advice_json = {"error": "An unexpected error occurred during AI advice generation.", "details": str(e)}

    # We no longer need to pass the full market data to the frontend if the AI is summarizing it
    # But for now, we'll keep it for debugging purposes.
    return {
        "user_id": user_id,
        "risk_profile": risk_profile,
        "investment_goal": investment_goal,
        "investment_horizon": investment_horizon,
        "financial_summary": financial_summary,
        "market_data_used": market_data, # Renamed for clarity
        "ai_advice": ai_advice_json
    }