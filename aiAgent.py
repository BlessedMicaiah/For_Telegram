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

# Custom LangChain Deepseek Integration
class DeepseekChatModel(BaseModel):
    """Custom LangChain integration for Deepseek Chat API."""
    
    client: Any = Field(..., description="OpenAI Client")
    model_name: str = Field(default="deepseek-chat", description="Model name")
    system_message: str = Field(default="You are a helpful assistant.", description="System message")
    
    def __init__(self, client, model_name="deepseek-chat", system_message="You are a helpful assistant."):
        super().__init__(client=client, model_name=model_name, system_message=system_message)
    
    def invoke(self, messages, **kwargs):
        message_dicts = []
        
        # Add system message if not present
        if not messages or messages[0].type != "system":
            message_dicts.append({"role": "system", "content": self.system_message})
        
        # Convert LangChain messages to Deepseek format
        for message in messages:
            if message.type == "human":
                message_dicts.append({"role": "user", "content": message.content})
            elif message.type == "ai":
                message_dicts.append({"role": "assistant", "content": message.content})
            elif message.type == "system":
                message_dicts.append({"role": "system", "content": message.content})
        
        # Call Deepseek API
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=message_dicts,
            stream=False,
            **kwargs
        )
        
        # Extract and return the response
        return AIMessage(content=response.choices[0].message.content)

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
    
    # Initialize LangChain with custom Deepseek integration
    llm = DeepseekChatModel(client=openai_client)
    
    # Create conversation prompt template with proper input variables
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="You are a helpful assistant that provides clear, accurate, and friendly responses."),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessage(content="{question}")
    ])
    
    # Create the conversation chain using the new pipe operator pattern
    conversation_chain = prompt | llm
    
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
    raise

# Define a function for the /start command
async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    user_id = update.effective_user.id
    # Initialize message history for new users
    if user_id not in user_message_histories:
        user_message_histories[user_id] = ChatMessageHistory()
    
    await update.message.reply_text("Hello! I am Testo powered by Deepseek AI with LangChain integration. Ask me anything!")

# Define the function to handle incoming user messages
async def chat(update: Update, context: CallbackContext):
    """Handles messages and sends AI-generated responses using LangChain."""
    try:
        user_id = update.effective_user.id
        user_message = update.message.text
        print(f"Received message from user {user_id}: {user_message}")
        
        # Get or create message history for this user
        if user_id not in user_message_histories:
            user_message_histories[user_id] = ChatMessageHistory()
        
        # Generate response using the new pattern
        print(f"Sending request to Deepseek API via LangChain...")
        response = conversation_with_history.invoke(
            {"question": user_message},
            config={"configurable": {"session_id": str(user_id)}}
        )
        
        # Extract the bot's reply
        print(f"Received response via LangChain: {response.content[:30]}...")
        await update.message.reply_text(response.content)
        
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
