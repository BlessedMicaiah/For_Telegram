from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import openai
import os

# OpenAI API Key
OPENAI_API_KEY = os.getenv("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")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key! Set it as an environment variable.")

# Initialize OpenAI client with API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing Telegram Bot Token! Set it as an environment variable.")

async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    await update.message.reply_text("Hello! I am Testo. Ask me anything!")

async def chat(update: Update, context: CallbackContext):
    """Handles messages and sends AI-generated responses."""
    user_message = update.message.text

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}]
    )

    bot_reply = response.choices[0].message.content
    await update.message.reply_text(bot_reply)

def main():
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
