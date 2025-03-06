import os
import traceback
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from openai import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.chat_models.base import BaseChatModel
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Any, Dict, List, Optional

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
class DeepseekChatModel(BaseChatModel):
    """Custom LangChain integration for Deepseek Chat API."""
    
    client: Any  # OpenAI Client
    model_name: str = "deepseek-chat"
    system_message: str = "You are a helpful assistant."
    
    def __init__(self, client, model_name="deepseek-chat", system_message="You are a helpful assistant."):
        super().__init__()
        self.client = client
        self.model_name = model_name
        self.system_message = system_message
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
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
        ai_message = AIMessage(content=response.choices[0].message.content)
        return {"generations": [[ai_message]], "llm_output": None}
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        # For async support - implement if needed
        return self._generate(messages, stop, run_manager, **kwargs)
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"

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
    
    # Create conversation prompt template
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="You are a helpful assistant that provides clear, accurate, and friendly responses."),
        MessagesPlaceholder(variable_name="history"),
        HumanMessage(content="{input}")
    ])
    
    # Set up conversation memory (per user)
    user_memories = {}
    
except Exception as e:
    print(f"ERROR initializing Deepseek client: {str(e)}")
    print("Please check your Deepseek API key and network connection.")
    raise

# Define a function for the /start command
async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    user_id = update.effective_user.id
    # Initialize memory for new users
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferMemory(return_messages=True)
    
    await update.message.reply_text("Hello! I am Testo powered by Deepseek AI with LangChain integration. Ask me anything!")

# Define the function to handle incoming user messages
async def chat(update: Update, context: CallbackContext):
    """Handles messages and sends AI-generated responses using LangChain."""
    try:
        user_id = update.effective_user.id
        user_message = update.message.text
        print(f"Received message from user {user_id}: {user_message}")
        
        # Get or create memory for this user
        if user_id not in user_memories:
            user_memories[user_id] = ConversationBufferMemory(return_messages=True, memory_key="history")
        
        memory = user_memories[user_id]
        
        # Create the conversation chain
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            prompt=prompt,
            verbose=True
        )
        
        # Generate response
        print(f"Sending request to Deepseek API via LangChain...")
        response = conversation.predict(input=user_message)
        
        # Extract the bot's reply
        print(f"Received response via LangChain: {response[:30]}...")
        await update.message.reply_text(response)
        
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
