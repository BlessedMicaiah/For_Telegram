import os
import traceback
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from openai import OpenAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import Any, Dict, List, Optional
from pydantic import Field, BaseModel

# Load environment variables
load_dotenv()

# Get API keys from .env file
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Validate API Keys
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing Telegram Bot Token! Set TELEGRAM_BOT_TOKEN in your environment variables.")
if not DEEPSEEK_API_KEY:
    raise ValueError("Missing Deepseek API Key! Set DEEPSEEK_API_KEY in your environment variables.")

# Set up message histories (per user)
user_message_histories = {}

# Initialize the Deepseek client
try:
    print("Initializing Deepseek client...")
    openai_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    
    # Test connection
    test_response = openai_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": "You are a helpful assistant"}, 
                  {"role": "user", "content": "Say OK"}],
        stream=False
    )
    print("Deepseek client initialized successfully!")
    
except Exception as e:
    print(f"ERROR initializing Deepseek client: {str(e)}")
    print("Please check your Deepseek API key and network connection.")
    traceback.print_exc()
    raise

# Simple function to process a conversation and return a response
def process_conversation(user_id: str, new_message: str) -> str:
    """
    Process a user message and return an AI response using Deepseek.
    
    Args:
        user_id: The user's unique ID for retrieving their chat history
        new_message: The newest message from the user
        
    Returns:
        The AI's response text
    """
    try:
        # Get or initialize chat history for this user
        if user_id not in user_message_histories:
            print(f"Creating new message history for user {user_id}")
            user_message_histories[user_id] = ChatMessageHistory()
        
        chat_history = user_message_histories[user_id]
        
        # Add the user's message to history
        chat_history.add_user_message(new_message)
        
        # Build the messages list for the API call
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides clear, accurate, and friendly responses."}
        ]
        
        # Add chat history messages
        for msg in chat_history.messages:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                messages.append({"role": "system", "content": msg.content})
        
        print(f"Sending {len(messages)} messages to Deepseek API")
        
        # Call Deepseek API
        response = openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        
        # Extract the response text
        ai_response = response.choices[0].message.content
        
        # Add the AI response to history
        chat_history.add_ai_message(ai_response)
        
        return ai_response
        
    except Exception as e:
        print(f"Error processing conversation: {str(e)}")
        traceback.print_exc()
        return f"Sorry, I encountered an error processing your message. Error details: {str(e)}"

# Define a function for the /start command
async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    # Initialize chat history for new users
    if user_id not in user_message_histories:
        user_message_histories[user_id] = ChatMessageHistory()
    
    await update.message.reply_text("Hello! I am Testo powered by Deepseek AI. Ask me anything!")

# Define the function to handle incoming user messages
async def chat(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        user_message = update.message.text
        print(f"Received message from user {user_id}: {user_message}")
        
        # Get AI response
        print("Sending request to Deepseek API...")
        ai_response = process_conversation(user_id, user_message)
        
        print(f"Received response: {ai_response[:30]}...")
        await update.message.reply_text(ai_response)
        
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        print(f"ERROR: {error_msg}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        await update.message.reply_text(f"⚠️ Sorry, I encountered an error processing your message.\nError details: {str(e)}")

# Main function to start the bot
def main():
    print("Starting bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    is_render = os.environ.get('RENDER') == 'true'
    if is_render:
        port = int(os.environ.get('PORT', 10000))
        webhook_url = os.environ.get('WEBHOOK_URL', 'https://for-telegram.onrender.com')
        print(f"Running on Render with webhook URL: {webhook_url}")
        app.run_webhook(
            listen='0.0.0.0',
            port=port,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{webhook_url}/{TELEGRAM_BOT_TOKEN}"
        )
    else:
        print("Running locally with polling mode...")
        app.run_polling()

if __name__ == "__main__":
    main()
