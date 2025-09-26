import os
import json
from openai import AsyncOpenAI, APIStatusError

# --- Configuration & Initialization ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# --- In-memory store for chat histories ---
# Key: user_id (str), Value: list of message objects
chat_histories = {}


# --- Function for Structured, One-off Responses (like advice) ---
async def generate_structured_response_openai(prompt: str) -> str:
    """
    For one-off, complex prompts that require a structured JSON response.
    This function does NOT use chat history.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful financial advisor API that returns responses in valid JSON format."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in generating structured response from OpenAI: {e}")
        return json.dumps({"error": "Failed to get response from OpenAI", "details": str(e)})


# --- NEW Function for Conversational Chat ---
async def get_chat_response_openai(user_id: str, user_message: str) -> str:
    """
    Handles conversational chat, maintaining history for each user.
    """
    global chat_histories

    # Retrieve or initialize the chat history for the user
    if user_id not in chat_histories:
        chat_histories[user_id] = [
            {
                "role": "system",
                "content": """
                You are WealthWise, a friendly and helpful financial assistant.
                Your primary role is to answer questions related to finance, investing, budgeting, and market trends in India.
                If a user asks a question unrelated to finance, politely steer the conversation back to financial topics.
                Keep your answers concise and easy to understand.
                """
            }
        ]

    # Add the new user message to the history
    chat_histories[user_id].append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o", # Using a powerful model for good conversation
            messages=chat_histories[user_id] # Send the entire history
        )

        assistant_reply = response.choices[0].message.content

        # Add the assistant's reply to the history for future context
        chat_histories[user_id].append({"role": "assistant", "content": assistant_reply})

        return assistant_reply

    except APIStatusError as e:
        print(f"OpenAI API error in chat for user {user_id}: {e}")
        # Remove the last user message on failure so they can retry
        chat_histories[user_id].pop()
        return "Sorry, I'm having trouble connecting to my services. Please try again in a moment."
    except Exception as e:
        print(f"An unexpected error occurred in chat for user {user_id}: {e}")
        chat_histories[user_id].pop()
        return "I've run into an unexpected problem. Please try asking your question again."