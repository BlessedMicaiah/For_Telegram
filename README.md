# Telegram OpenAI Bot

A Telegram bot that uses OpenAI's GPT models to respond to user messages.

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv openai-env
   ```
3. Activate the virtual environment:
   ```
   # Windows
   .\openai-env\Scripts\activate
   
   # Linux/macOS
   source openai-env/bin/activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ```

## Running Locally with Webhooks

To run the bot locally with webhooks:

1. Install ngrok: https://ngrok.com/download
2. Start ngrok to expose your local server:
   ```
   ngrok http 8443
   ```
3. Copy the HTTPS URL provided by ngrok (e.g., https://a1b2c3d4.ngrok.io)
4. Set the WEBHOOK_URL environment variable:
   ```
   # Windows
   set WEBHOOK_URL=https://your-ngrok-url
   
   # Linux/macOS
   export WEBHOOK_URL=https://your-ngrok-url
   ```
5. Run the bot:
   ```
   python aiAgent.py
   ```

## Running on Render

This bot is configured to run on Render with webhooks:

1. Connect your GitHub repository to Render
2. Render will automatically use the `render.yaml` configuration
3. Set the following environment variables in Render:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `WEBHOOK_URL` (your Render domain, e.g., https://for-telegram.onrender.com)

## Commands

- `/start` - Start the bot and receive a welcome message
- Send any text message to receive an AI-generated response

## Note

Make sure only one instance of your bot is running at any time to avoid conflicts with Telegram's API.
