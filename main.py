import os, json, threading, asyncio
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

TOKEN = os.getenv("BOT_TOKEN")
TITLE, Q_TEXT, Q_OPT, Q_ANS = range(4)
QUIZ_FILE = "quizzes.json"

def load_q():
    if os.path.exists(QUIZ_FILE):
        with open(QUIZ_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}
def save_q(data):
    with open(QUIZ_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

quizzes = load_q()
user_scores = {}
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Quiz Maker LIVE!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ADVANCE QUIZ MAKER\n\n/newquiz - Naya Quiz Banao (aap khud)\n/myquiz - Aapke Quiz\n/quiz - Quiz Khelo\n/leaderboard")

async def newquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Quiz ka Title bhejo:\nEx: Bihar GK")
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_quiz'] = {"title": update.message.text, "questions": [], "owner": update.effective_user.id}
    context.user_data['qid'] = f"{update.effective_user.id}_{len(quizzes)}"
    await update.message.reply_text("Pehla Sawaal bhejo:")
    return Q_TEXT

async def get_q_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['curr_q'] = {"q": update.message.text}
    await update.message.reply_text("Ab 4 Options bhejo alag line me:\nPatna\nGaya\nBhagalpur\nPurnia")
    return Q_OPT

async def get_q_opt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opts = update.message.text.split("\n")
    context.user_data['curr_q']['o'] = opts[:4]
    await update.message.reply_text(f"Sahi jawab ka number bhejo (1-{len(opts)}):")
    return Q_ANS

async def get_q_ans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ans = int(update.message.text)-1
        curr = context.user_data['curr_q']
        curr['a'] = ans
        qid = context.user_data['qid']
        context.user_data['new_quiz']['questions'].append(curr)
        quizzes[qid] = context.user_data['new_quiz']
        save_q(quizzes)
        kb = [[InlineKeyboardButton("➕ Aur Sawaal Add Karo", callback_data="more")],[InlineKeyboardButton("✅ Bas Ho Gaya", callback_data="done")]]
        await update.message.reply_text(f"Add ho gaya! Total {len(quizzes[qid]['questions'])}", reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END
    except:
        await update.message.reply_text("1-4 me number bhejo")
        return Q_ANS

async def more_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "more":
        context.user_data['state'] = Q_TEXT
        await q.edit_message_text("Agla Sawaal bhejo:")
    else:
        await q.edit_message_text(f"✅ Quiz Ready! ID: {context.user_data['qid']}\nGroup me /quiz {context.user_data['qid']} likh ke chalao")

async def add_more_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    if state == Q_TEXT:
        context.user_data['curr_q'] = {"q": update.message.text}
        context.user_data['state'] = Q_OPT
        await update.message.reply_text("Options bhejo line me:")
    elif state == Q_OPT:
        context.user_data['curr_q']['o'] = update.message.text.split("\n")[:4]
        context.user_data['state'] = Q_ANS
        await update.message.reply_text("Sahi ka number bhejo:")
    elif state == Q_ANS:
        try:
            ans = int(update.message.text)-1
            context.user_data['curr_q']['a'] = ans
            qid = context.user_data['qid']
            quizzes[qid]['questions'].append(context.user_data['curr_q'])
            save_q(quizzes)
            kb = [[InlineKeyboardButton("➕ Aur Sawaal", callback_data="more")],[InlineKeyboardButton("✅ Bas Ho Gaya", callback_data="done")]]
            await update.message.reply_text(f"Add ho gaya! Total {len(quizzes[qid]['questions'])}", reply_markup=InlineKeyboardMarkup(kb))
            context.user_data['state'] = None
        except:
            await update.message.reply_text("Number galat")

async def myquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my = {k:v for k,v in quizzes.items() if str(v.get('owner')) == str(update.effective_user.id)}
    if not my:
        await update.message.reply_text("Aapne koi quiz nahi banaya")
        return
    txt = "Aapke Quiz:\n\n"
    for k,v in my.items(): txt += f"ID: {k}\nTitle: {v['title']} ({len(v['questions'])} Q)\n/quiz {k}\n\n"
    await update.message.reply_text(txt)

async def send_q(chat_id, context, quiz_id, q_idx):
    q = quizzes[quiz_id]['questions'][q_idx]
    btns = [[InlineKeyboardButton(f"{o}", callback_data=f"play_{quiz_id}_{q_idx}_{i}")] for i, o in enumerate(q['o'])]
    await context.bot.send_message(chat_id, f"Q{q_idx+1}: {q['q']}", reply_markup=InlineKeyboardMarkup(btns))

async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not quizzes:
        await update.message.reply_text("Pehle /newquiz se banao")
        return
    qid = context.args[0] if context.args else list(quizzes.keys())[-1]
    if qid not in quizzes:
        await update.message.reply_text("/myquiz se ID dekho")
        return
    await send_q(update.effective_chat.id, context, qid, 0)

async def play_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, quiz_id, q_idx, opt_idx = q.data.split("_")
    q_idx, opt_idx = int(q_idx), int(opt_idx)
    correct = quizzes[quiz_id]['questions'][q_idx]['a']
    uid = q.from_user.id
    if uid not in user_scores: user_scores[uid] = {"name": q.from_user.first_name, "pts": 0}
    if opt_idx == correct:
        user_scores[uid]['pts'] += 1
        res = "✅ Sahi!"
    else:
        res = f"❌ Galat! Sahi: {quizzes[quiz_id]['questions'][q_idx]['o'][correct]}"
    await q.edit_message_text(f"Q{q_idx+1}: {quizzes[quiz_id]['questions'][q_idx]['q']}\n\n{res}")
    await asyncio.sleep(1.5)
    nxt = q_idx+1
    if nxt < len(quizzes[quiz_id]['questions']):
        await send_q(q.message.chat_id, context, quiz_id, nxt)
    else:
        await context.bot.send_message(q.message.chat_id, "🎉 Khatam! /leaderboard")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_scores:
        await update.message.reply_text("Koi score nahi")
        return
    top = sorted(user_scores.values(), key=lambda x: x['pts'], reverse=True)[:10]
    txt = "🏆 Leaderboard\n\n" + "\n".join([f"{i+1}. {s['name']} - {s['pts']}" for i, s in enumerate(top)])
    await update.message.reply_text(txt)

def run_bot():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(entry_points=[CommandHandler("newquiz", newquiz)], states={TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)], Q_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_q_text)], Q_OPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_q_opt)], Q_ANS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_q_ans)]}, fallbacks=[])
    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myquiz", myquiz))
    app.add_handler(CommandHandler("quiz", quiz_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(more_handler, pattern="^(more|done)$"))
    app.add_handler(CallbackQueryHandler(play_handler, pattern="^play_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_more_text))
    app.run_polling()

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))