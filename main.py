import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 10 Quiz Questions
QUESTIONS = [
    {"q": "Bharat ki rajdhani kya hai?", "options": ["Mumbai", "Delhi", "Kolkata"], "ans": 1},
    {"q": "2 + 2 kitna hota hai?", "options": ["3", "4", "5"], "ans": 1},
    {"q": "Taj Mahal kahan hai?", "options": ["Delhi", "Agra", "Jaipur"], "ans": 1},
    {"q": "Computer ka dimag kise kehte hai?", "options": ["Mouse", "CPU", "Keyboard"], "ans": 1},
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! 🙏\nQuiz start karne ke liye /quiz likho")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['score'] = 0
    context.user_data['q_index'] = 0
    await send_question(update, context)

async def send_question(update, context):
    q_index = context.user_data['q_index']
    if q_index >= len(QUESTIONS):
        score = context.user_data['score']
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Quiz Khatam! 🎉\nAapka Score: {score}/{len(QUESTIONS)}")
        return

    q_data = QUESTIONS[q_index]
    keyboard = []
    for i, opt in enumerate(q_data['options']):
        keyboard.append([InlineKeyboardButton(opt, callback_data=str(i))])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Q{q_index+1}: {q_data['q']}"
    
    # Agar /quiz command se aaya hai to naya message, warna purane ko edit karo
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    q_index = context.user_data['q_index']
    q_data = QUESTIONS[q_index]
    user_ans = int(query.data)
    
    if user_ans == q_data['ans']:
        context.user_data['score'] += 1
        result = "✅ Sahi Jawab!"
    else:
        result = f"❌ Galat! Sahi jawab hai: {q_data['options'][q_data['ans']]}"
    
    await query.edit_message_text(text=f"{result}\n\nAgle sawal ka intezaar karo...")
    
    context.user_data['q_index'] += 1
    # Thoda wait karke agla sawal
    import asyncio
    await asyncio.sleep(1)
    await send_question(update, context)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()

if __name__ == "__main__":
    main()