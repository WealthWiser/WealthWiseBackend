from app.database import get_transactions

def analyst_agent(user):
    # txns = get_transactions(user["id"]).data
    # # Dummy analysis
    # total_spent = sum([t["amount"] for t in txns if t["type"] == "expense"])
    # total_income = sum([t["amount"] for t in txns if t["type"] == "income"])
    total_spent = 30000
    total_income = 50000
    return {"spending": total_spent, "income": total_income}
