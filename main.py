import os, threading, asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

QUESTIONS = [
    {"q": "Bharat ki rajdhani kya hai?", "options": ["Mumbai", "Delhi", "Kolkata"], "ans": 1},
    {"q": "2+2 kitna hota hai?", "options": ["3", "4", "5"], "ans": 1},
    {"q": "Taj Mahal kahan hai?", "options": ["Delhi", "Agra", "Jaipur"], "ans": 1},
]

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot Live Hai!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! 🙏 /quiz likho")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['score']=0
    context.user_data['q_index']=0
    await send_q(update, context)

async def send_q(update, context):
    i=context.user_data['q_index']
    if i>=len(QUESTIONS):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Quiz Khatam! Score: {context.user_data['score']}/{len(QUESTIONS)}")
        return
    q=QUESTIONS[i]
    kb=[[InlineKeyboardButton(opt, callback_data=str(idx))] for idx,opt in enumerate(q['options'])]
    txt=f"Q{i+1}: {q['q']}"
    if update.callback_query:
        await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    idx=context.user_data['q_index']
    data=QUESTIONS[idx]
    ans=int(q.data)
    if ans==data['ans']:
        context.user_data['score']+=1
        res="✅ Sahi!"
    else:
        res=f"❌ Galat! Sahi: {data['options'][data['ans']]}"
    await q.edit_message_text(f"{res}")
    context.user_data['q_index']+=1
    await asyncio.sleep(1)
    await send_q(update, context)

async def run_bot():
    TOKEN=os.getenv("BOT_TOKEN")
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(btn))
    # ye conflict fix karega
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

def start_bot_thread():
    asyncio.run(run_bot())

if __name__=="__main__":
    threading.Thread(target=start_bot_thread, daemon=True).start()
    port=int(os.environ.get("PORT", 10000))
    print(f"Starting flask on port {port}")
    app_flask.run(host="0.0.0.0", port=port)