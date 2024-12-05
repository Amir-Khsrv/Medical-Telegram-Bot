from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from fastapi import FastAPI
import os
import json

# Conversation states
ASK_NAME, CHOOSE_SPECIALTY = range(2)

# Define the FastAPI app
app = FastAPI()

# Telegram Bot Token
TOKEN = "7946706520:AAHxnfqdrH6Km7QP-AnM3xYwEcZzvKaCJN8"
WEBHOOK_URL = f"https://medical-telegram-bot-2.onrender.com/webhook/{TOKEN}"

# Initialize the bot application
application = Application.builder().token(TOKEN).build()

# Save user data
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

# Add handlers to the application
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
        CHOOSE_SPECIALTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_specialty)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
application.add_handler(conv_handler)

# FastAPI routes
@app.on_event("startup")
async def on_startup():
    # Set the webhook
    await application.bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    # Remove the webhook
    await application.bot.delete_webhook()

@app.get("/")
async def home():
    return {"message": "Bot is running"}

@app.post(f"/webhook/{TOKEN}")
async def telegram_webhook(update: dict):
    # Process the incoming update
    await application.update_queue.put(Update.de_json(update, application.bot))
    return {"ok": True}

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
