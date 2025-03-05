import os
import traceback
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Get API keys from .env file
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# Validate API Keys
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing Telegram Bot Token! Set TELEGRAM_BOT_TOKEN in your environment variables.")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key! Set OPENAI_API_KEY in your environment variables.")
if not LANGCHAIN_API_KEY:
    raise ValueError("Missing LangChain API Key! Set LANGCHAIN_API_KEY in your environment variables.")

# Initialize LangChain OpenAI client
try:
    print("Initializing LangChain OpenAI client...")
    llm = ChatOpenAI(
        api_key=LANGCHAIN_API_KEY,  # Using LangChain API
        model="gpt-3.5-turbo",  # You can change this to another model like "gpt-4" if you have access
        temperature=0.7
    )
    # Test connection
    test_response = llm.invoke("Say OK")
    print("LangChain OpenAI client initialized successfully!")
except Exception as e:
    print(f"ERROR initializing LangChain OpenAI client: {str(e)}")
    print("Please check your LangChain API key and network connection.")
    raise

# Define a function for the /start command
async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    await update.message.reply_text("Hello! I am Testo powered by LangChain and OpenAI. Ask me anything!")

# Define the function to handle incoming user messages
async def chat(update: Update, context: CallbackContext):
    """Handles messages and sends AI-generated responses."""
    try:
        user_message = update.message.text
        print(f"Received message: {user_message}")

        # Get AI response
        print("Sending request to LangChain API...")
        response = llm.invoke(user_message)

        # Extract the bot's reply
        bot_reply = response.content
        print(f"Received response from LangChain API: {bot_reply[:30]}...")
        await update.message.reply_text(bot_reply)
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        print(f"ERROR: {error_msg}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        await update.message.reply_text(f"Sorry, I encountered an error processing your message.\nError details: {str(e)}")

# Main function to start the bot
def main():
    """Start the bot using webhooks or polling."""
    print("Starting bot...")

    # Create the Application object
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Check if running on Render or locally
    is_render = os.environ.get('RENDER') == 'true'
    
    if is_render:
        # Use webhook on Render
        port = int(os.environ.get('PORT', 10000))
        webhook_url = os.environ.get('WEBHOOK_URL', 'https://for-telegram.onrender.com')
        print(f"Running on Render with webhook URL: {webhook_url}")

        # Run with webhook
        app.run_webhook(
            listen='0.0.0.0',
            port=port,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{webhook_url}/{TELEGRAM_BOT_TOKEN}"
        )
    else:
        # Use polling for local development
        print("Running locally with polling mode...")
        app.run_polling()

if __name__ == "__main__":
    main()
