from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key! Set it as an environment variable.")

# Initialize OpenAI client with API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing Telegram Bot Token! Set it as an environment variable.")

# Define a function for the /start command
async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    await update.message.reply_text("Hello! I am Testo. Ask me anything!")

# Define the function to handle incoming user messages
async def chat(update: Update, context: CallbackContext):
    """Handles messages and sends AI-generated responses."""
    user_message = update.message.text

    # Get response from OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}]
    )

    # Extract the bot's reply
    bot_reply = response.choices[0].message.content
    await update.message.reply_text(bot_reply)

# Main function to start the bot with webhook
def main():
    """Start the bot with webhook."""
    
    # Create the Application object
    app = Application.builder().token(BOT_TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Define the webhook URL (adjust it to your deployed server URL)
    webhook_url = 'https://your-app-url.com/'  # Replace with your actual URL

    # Setup the webhook
    app.run_webhook(
        listen='0.0.0.0',    # Listen on all IPs
        port=80,             # Standard HTTP port (you might need to use 443 for HTTPS)
        url_path=BOT_TOKEN,  # Your bot token used to create the webhook URL
        webhook_url=f"{webhook_url}/{BOT_TOKEN}"  # Full webhook URL with bot token
    )

if __name__ == "__main__":
    main()
