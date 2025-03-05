from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import traceback

# Load environment variables from .env file
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key! Set it as an environment variable.")

# Initialize ChatOpenAI client with API key
try:
    print("Initializing LangChain OpenAI client...")
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-3.5-turbo",  # You can change this to another model like "gpt-4" if you have access
        temperature=0.7
    )
    # Test the connection with a simple completion
    test_response = llm.invoke("Say OK")
    print("LangChain OpenAI client initialized successfully!")
except Exception as e:
    print(f"ERROR initializing LangChain OpenAI client: {str(e)}")
    print("Please check your OpenAI API key and network connection.")
    raise

# Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing Telegram Bot Token! Set it as an environment variable.")

# Define a function for the /start command
async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    await update.message.reply_text("Hello! I am Testo powered by GPT. Ask me anything!")

# Define the function to handle incoming user messages
async def chat(update: Update, context: CallbackContext):
    """Handles messages and sends OpenAI-generated responses."""
    try:
        user_message = update.message.text
        print(f"Received message: {user_message}")

        # Get response from OpenAI via LangChain
        print("Sending request to OpenAI API...")
        response = llm.invoke(user_message)

        # Extract the bot's reply
        bot_reply = response.content
        print(f"Received response from OpenAI API: {bot_reply[:30]}...")
        await update.message.reply_text(bot_reply)
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        print(f"ERROR: {error_msg}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        await update.message.reply_text(f"Sorry, I encountered an error processing your message.\nError details: {str(e)}")

# Main function to start the bot
def main():
    """Start the bot using webhooks."""
    
    print("Starting bot with webhook...")
    
    # Create the Application object
    app = Application.builder().token(BOT_TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Check if running on Render or locally
    is_render = os.environ.get('RENDER') == 'true'
    
    # Configure webhook parameters
    if is_render:
        # Production environment on Render
        port = int(os.environ.get('PORT', 10000))
        webhook_url = os.environ.get('WEBHOOK_URL', 'https://for-telegram.onrender.com')
        print(f"Running on Render. Using webhook URL: {webhook_url}")
    else:
        # Local development - requires ngrok or similar tool
        # To use locally:
        # 1. Install ngrok: https://ngrok.com/download
        # 2. Run: ngrok http 8443
        # 3. Copy the HTTPS URL from ngrok and use it below
        port = 8443
        webhook_url = os.environ.get('WEBHOOK_URL')
        if not webhook_url:
            print("WARNING: No WEBHOOK_URL environment variable found!")
            print("To test locally with webhooks, you need to:")
            print("1. Install ngrok: https://ngrok.com/download")
            print("2. Run: ngrok http 8443")
            print("3. Set the WEBHOOK_URL environment variable to your ngrok HTTPS URL")
            print("Example: set WEBHOOK_URL=https://a1b2c3d4.ngrok.io")
            return
        print(f"Running locally. Using webhook URL: {webhook_url}")
    
    # Run the bot with webhook
    app.run_webhook(
        listen='0.0.0.0',
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"{webhook_url}/{BOT_TOKEN}"
    )
    
if __name__ == "__main__":
    main()
