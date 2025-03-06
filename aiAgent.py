import os
import traceback
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from openai import OpenAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
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
    
    # Function to convert messages and call Deepseek API
    def deepseek_chat(messages):
        message_dicts = []
        
        # Debug info
        print(f"Processing {len(messages)} messages")
        
        # Convert LangChain messages to Deepseek format
        for message in messages:
            # Handle tuple messages (sometimes messages come as (role, content) tuple)
            if isinstance(message, tuple) and len(message) == 2:
                role, content = message
                print(f"Converting tuple message: role={role}, content={content[:30]}...")
                if role == "human":
                    message_dicts.append({"role": "user", "content": content})
                elif role == "ai":
                    message_dicts.append({"role": "assistant", "content": content})
                elif role == "system":
                    message_dicts.append({"role": "system", "content": content})
            # Handle standard LangChain message objects
            elif isinstance(message, HumanMessage):
                message_dicts.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                message_dicts.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                message_dicts.append({"role": "system", "content": message.content})
            else:
                print(f"⚠️ Unexpected message type: {type(message)}, content: {str(message)[:100]}")
        
        # Ensure we have at least one message
        if not message_dicts:
            print("WARNING: No valid messages to send to Deepseek API, adding default message")
            message_dicts = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"}
            ]
        
        print(f"Sending {len(message_dicts)} messages to Deepseek API")
        
        # Call Deepseek API
        response = openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=message_dicts,
            stream=False
        )
        
        # Return the AI's response as an AIMessage
        return AIMessage(content=response.choices[0].message.content)
    
    # Create conversation prompt template with proper input variables
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="You are a helpful assistant that provides clear, accurate, and friendly responses."),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessage(content="{question}")
    ])
    
    # Create the conversation chain
    conversation_chain = prompt | deepseek_chat
    
    # Set up conversation memory (per user)
    user_message_histories = {}
    
    # Configure the chain with message history
    conversation_with_history = RunnableWithMessageHistory(
        conversation_chain,
        lambda session_id: user_message_histories.get(session_id, ChatMessageHistory()),
        input_messages_key="question",
        history_messages_key="chat_history"
    )
    
except Exception as e:
    print(f"ERROR initializing Deepseek client: {str(e)}")
    print("Please check your Deepseek API key and network connection.")
    traceback.print_exc()
    raise

# Define a function for the /start command
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in user_message_histories:
        user_message_histories[user_id] = ChatMessageHistory()
    await update.message.reply_text("Hello! I am Testo powered by Deepseek AI with LangChain integration. Ask me anything!")

# Define the function to handle incoming user messages
async def chat(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        user_message = update.message.text
        print(f"Received message from user {user_id}: {user_message}")
        
        if user_id not in user_message_histories:
            user_message_histories[user_id] = ChatMessageHistory()
        
        print("Sending request to Deepseek API via LangChain...")
        response = conversation_with_history.invoke(
            {"question": user_message},
            config={"configurable": {"session_id": str(user_id)}}
        )
        
        ai_content = response.content
        print(f"Received response via LangChain: {ai_content[:30]}...")
        await update.message.reply_text(ai_content)
        
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        print(f"ERROR: {error_msg}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        await update.message.reply_text(f"Sorry, I encountered an error processing your message.\nError details: {str(e)}")

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
