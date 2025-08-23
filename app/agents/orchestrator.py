from app.agents.analyst import analyst_agent
# from app.agents.risk import risk_agent
# from app.agents.market import market_agent
# from app.agents.educator import educator_agent

def orchestrate_query(user, message: str):
    # Simple routing logic (expand later with LangChain)
    if "spending" in message.lower():
        data = analyst_agent(user)
    # elif "risk" in message.lower():
    #     data = risk_agent(user)
    # elif "market" in message.lower():
    #     data = market_agent()
    else:
        data = {"info": "General financial guidance"}

    return data
