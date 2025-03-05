from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import openai
import os

# Set your OpenAI API key
openai.api_key = os.getenv("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")

# Set your Telegram bot token
BOT_TOKEN = "7594844957:AAFr3sxpGljzXO2a0f5IDOaKXEjdkOC6nCg"

async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    await update.message.reply_text("Hello! I am an Testo. Ask me anything!")

async def chat(update: Update, context: CallbackContext):
    """Handles messages and sends AI-generated responses."""
    user_message = update.message.text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}]
    )
    bot_reply = response["choices"][0]["message"]["content"]
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
