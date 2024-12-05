from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes
import os
import json
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token and Webhook URL
TOKEN = "7946706520:AAHxnfqdrH6Km7QP-AnM3xYwEcZzvKaCJN8"
WEBHOOK_URL = f"https://medical-telegram-bot-2.onrender.com/{TOKEN}"

# Conversation states
ASK_NAME, CHOOSE_SPECIALTY = range(2)

# Save user data
def save_user_data(user_id, name, username, specialty):
    try:
        os.makedirs('data', exist_ok=True)
        file_path = 'data/user_data.json'

        # Load existing data or create a new list
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                users = json.load(file)
        else:
            users = []

        # Append new user data
        users.append({
            "user_id": user_id,
            "name": name,
            "username": username,
            "specialty": specialty
        })

        # Save updated data back to the file
        with open(file_path, 'w') as file:
            json.dump(users, file, indent=4)
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🎉 Welcome! Please tell me your name. 😊")
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text
    context.user_data['name'] = user_name

    specialties = ['Internal Medicine', 'Neurology', 'Cardiology', 'Pediatrics']
    reply_keyboard = [specialties[i:i + 2] for i in range(0, len(specialties), 2)]
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

# Initialize the bot application
application = Application.builder().token(TOKEN).build()

# Add conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
        CHOOSE_SPECIALTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_specialty)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
application.add_handler(conv_handler)

# Initialize Flask app
app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        if data:
            update = Update.de_json(data, application.bot)
            application.update_queue.put_nowait(update)
            return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Bot is running"}), 200

# Set the webhook when the Flask app starts
if __name__ == "__main__":
    from telegram import Bot

    try:
        bot = Bot(TOKEN)
        bot.delete_webhook()  # Cleanup old webhooks
        bot.set_webhook(WEBHOOK_URL)  # Set new webhook
        logger.info("Webhook set successfully.")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
