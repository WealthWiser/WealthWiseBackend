from app.config import supabase

def get_user_by_id(user_id: str):
    return supabase.table("users").select("*").eq("id", user_id).execute()

def get_transactions(user_id: str):
    return {"table": "coming soon"}
    # return supabase.table("transactions").select("*").eq("user_id", user_id).execute()
