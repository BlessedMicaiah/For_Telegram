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
    try:
        user_message = update.message.text
        print(f"Received message: {user_message}")

        # Get response from OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )

        # Extract the bot's reply
        bot_reply = response.choices[0].message.content
        print(f"Sending reply: {bot_reply[:30]}...")
        await update.message.reply_text(bot_reply)
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        await update.message.reply_text("Sorry, I encountered an error processing your message.")

# Main function to start the bot
def main():
    """Start the bot."""
    
    print("Starting bot...")
    
    # Create the Application object
    app = Application.builder().token(BOT_TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot using polling (for local development)
    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()
    
    # If you want to use webhook for production, uncomment the following:
    # webhook_url = 'https://for-telegram.onrender.com' 
    # app.run_webhook(
    #     listen='0.0.0.0',
    #     port=8080,             # Using a higher port number
    #     url_path=BOT_TOKEN,
    #     webhook_url=f"{webhook_url}/{BOT_TOKEN}"
    # )

if __name__ == "__main__":
    main()
