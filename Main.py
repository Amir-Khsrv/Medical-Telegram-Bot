import json
import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# Define states for the conversation
ASK_NAME, CHOOSE_SPECIALTY = range(2)
TOKEN = "7946706520:AAHxnfqdrH6Km7QP-AnM3xYwEcZzvKaCJN8"

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

# FastAPI app and webhook handling
app = FastAPI()

WEBHOOK_URL = f"https://medical-telegram-bot-2.onrender.com/webhook/{TOKEN}"

# Initialize the Application object and set the webhook
application = Application.builder().token(TOKEN).build()

# Setting webhook inside the initialization function
application.bot.set_webhook(WEBHOOK_URL)

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

@app.get('/')
async def home(request: Request):
    return {"message": "Bot Is Running"}

@app.post(f"/webhook/{TOKEN}")
async def webhook(request: Request):
    try:
        data = await request.json()  # Get JSON data
        print("Incoming update:", data)  # Log incoming data for debugging

        if data:
            update = Update.de_json(data, application.bot)  # Deserialize data
            await application.process_update(update)  # Process the update using the application context

        return {"status": "ok"}, 200  # Return a successful HTTP status code
    except Exception as e:
        print("Error in webhook:", e)  # Log the error
        return {"error": "Internal Server Error"}, 500  # Return error HTTP status code


