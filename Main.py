import json
import os
import asyncio
from flask import Flask, request
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

# Function to save user data to a custom folder (e.g., data/)
def save_user_data(user_id, name, username, specialty):
    os.makedirs('data', exist_ok=True)
    file_path = 'data/user_data.json'

    data = {
        "user_id": user_id,
        "name": name,
        "username": username,
        "specialty": specialty
    }

    try:
        with open(file_path, 'r') as file:
            users = json.load(file)
    except FileNotFoundError:
        users = []

    users.append(data)

    with open(file_path, 'w') as file:
        json.dump(users, file, indent=4)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    welcome_message = """
    🎉 Welcome to **TalleyBot**! 🎉

    I'm your personal assistant 🤖, here to help you explore medical specialties! 🩺

    Please tell me your name so we can get started. 😊
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    return ASK_NAME

# Name input handler
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text
    context.user_data['name'] = user_name

    specialty_list = [
        'Internal Medicine', 'Neurology', 'Cardiology', 'Pediatrics', 'Orthopedics', 
        'Dermatology', 'Psychiatry', 'General Surgery', 'Obstetrics and Gynecology',
        'Radiology', 'Pathology', 'Emergency Medicine', 'Anesthesia', 'Physical Examination'
    ]

    reply_keyboard = [specialty_list[i:i + 3] for i in range(0, len(specialty_list), 3)]
    await update.message.reply_text(
        f"Hi {user_name}! Please choose a specialty from the list below: 👇",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSE_SPECIALTY

# Specialty selection handler
async def choose_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    specialty = update.message.text
    user_name = context.user_data.get('name', 'User')
    username = update.message.from_user.username
    context.user_data['specialty'] = specialty

    save_user_data(update.message.from_user.id, user_name, username, specialty)

    await update.message.reply_text(f"Thank you, {user_name}! 🎉 You chose **{specialty}** as your specialty! 🩺")
    return ConversationHandler.END

# Cancel command handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Goodbye! 👋 Stay healthy! 🩺")
    return ConversationHandler.END

# Flask app for webhook
app = Flask(__name__)
TOKEN = "7946706520:AAHxnfqdrH6Km7QP-AnM3xYwEcZzvKaCJN8"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
application = Application.builder().token(TOKEN).build()

@app.route('/')
def home():
    return "Bot is running!"

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    data = request.get_json()
    if data:
        update = Update.de_json(data, application.bot)
        application.process_update(update)
    return "OK"

# Main function
async def main():
    # Set the webhook URL (replace '<your-render-url>' with your actual URL)
    webhook_url = f"https://medical-telegram-bot-2.onrender.com/webhook/{TOKEN}"
    await application.bot.set_webhook(url=webhook_url)

if __name__ == '__main__':
    # Run the bot in the background
    loop = asyncio.get_event_loop()
    loop.create_task(main())

    # Start Flask app (runs on port 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
