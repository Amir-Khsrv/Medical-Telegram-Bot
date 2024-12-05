import json
import os
from fastapi import FastAPI , Request
from pydantic import BaseModel
from daphne.server import Server
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import asyncio
# Define states for the conversation
ASK_NAME, CHOOSE_SPECIALTY = range(2)

# Function to save user data
def save_user_data(user_id, name, username, specialty):
    os.makedirs('data', exist_ok=True)
    file_path = 'data/user_data.json'

    try:
        with open(file_path, 'r') as file:
            users = json.load(file)
    except FileNotFoundError:
        users = []

    users.append({
        "user_id": user_id,
        "name": name,
        "username": username,
        "specialty": specialty
    })

    with open(file_path, 'w') as file:
        json.dump(users, file, indent=4)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🎉 Welcome! Please tell me your name. 😊",
    )
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text
    context.user_data['name'] = user_name

    specialty_list = [
        'Internal Medicine', 'Neurology', 'Cardiology', 'Pediatrics',
    ]
    reply_keyboard = [specialty_list[i:i + 2] for i in range(0, len(specialty_list), 2)]
    await update.message.reply_text(
        f"Hi {user_name}! Choose a specialty: 👇",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSE_SPECIALTY

async def choose_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    specialty = update.message.text
    name = context.user_data.get('name', 'User')
    save_user_data(
        user_id=update.message.from_user.id,
        name=name,
        username=update.message.from_user.username,
        specialty=specialty
    )
    await update.message.reply_text(f"Thank you, {name}! You chose {specialty}. 🎉")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Goodbye!")
    return ConversationHandler.END

# Flask app and Telegram bot application
app = FastAPI()
TOKEN = "7946706520:AAHxnfqdrH6Km7QP-AnM3xYwEcZzvKaCJN8"
WEBHOOK_URL = f"https://medical-telegram-bot-2.onrender.com/webhook/{TOKEN}"

application = (
    Application.builder()
    .token(TOKEN)
    .build()
)
class UpdateData(BaseModel):
    update_id: int
    message: dict
# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
        CHOOSE_SPECIALTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_specialty)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
application.add_handler(conv_handler)

@app.route('/')
def home():
    return "Bot is running!"

@app.route(f"/webhook/{TOKEN}", methods=['POST'])
async def webhook(token: str, request: Request):
    try:
        data = await request.json()  # Get JSON data
        print("Incoming update:", data)  # Log incoming data for debugging
        if data:
            update = Update.de_json(data, application.bot)  # Deserialize data
            await application.process_update(update)    # Fixing the warning
        return "OK", 200  # Return a successful HTTP status code
    except Exception as e:
        print("Error in webhook:", e)  # Log the error
        return "Internal Server Error", 500  # Return error HTTP status code

# Initialize the bot
def initialize_bot():
    application.bot.set_webhook(WEBHOOK_URL)
    print("Webhook set successfully.")

# Initialize bot before running Flask app
initialize_bot()

# Start Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
