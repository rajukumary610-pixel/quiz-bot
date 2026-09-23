import os, threading
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
def home(): return "Bot is Live!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! 🙏 /quiz likho")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['score']=0
    context.user_data['q_index']=0
    await send_q(update, context)

async def send_q(update, context):
    i=context.user_data.get('q_index',0)
    if i>=len(QUESTIONS):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Quiz Khatam! Score: {context.user_data.get('score',0)}/{len(QUESTIONS)}")
        return
    q=QUESTIONS[i]
    kb=[[InlineKeyboardButton(opt, callback_data=str(idx))] for idx,opt in enumerate(q['options'])]
    txt=f"Q{i+1}: {q['q']}"
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=txt, reply_markup=InlineKeyboardMarkup(kb))

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    idx=context.user_data.get('q_index',0)
    if idx>=len(QUESTIONS): return
    data=QUESTIONS[idx]
    ans=int(q.data)
    if ans==data['ans']:
        context.user_data['score']=context.user_data.get('score',0)+1
        res="✅ Sahi Jawab!"
    else:
        res=f"❌ Galat! Sahi hai: {data['options'][data['ans']]}"
    await q.edit_message_text(f"{res}")
    context.user_data['q_index']=idx+1
    import asyncio
    await asyncio.sleep(1)
    await send_q(update, context)

def run_bot():
    TOKEN=os.getenv("BOT_TOKEN")
    print(f"TOKEN exists: {bool(TOKEN)}")
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port=int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
