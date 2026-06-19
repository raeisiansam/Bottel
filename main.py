import os
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# خواندن متغیرها از تنظیمات Railway (بخش Variables)
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
BOT_USERNAME = "bombdaramadbot"

DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class RailwayHealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Active!")
    def log_message(self, format, *args):
        return  

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RailwayHealthCheck)
    server.serve_forever()

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        ["💎 شروع کسب درآمد 💎"],
        ["🏠 حساب کاربری", "🌟 برترین کاربران"],
        ["💸 برداشت از حساب", "📊 تاریخچه برداشت"],
        ["📜 قوانین", "📞 پشتیبانی", "📚 راهنما"]
    ], resize_keyboard=True)

async def start_command(update, context):
    user = update.effective_user
    user_id = str(user.id)
    db = load_db()

    if user_id not in db:
        db[user_id] = {"balance": 0, "invited_by": None, "invites_count": 0, "username": user.first_name, "step": "none"}
        if context.args:
            inviter_id = context.args[0]
            if inviter_id in db and inviter_id != user_id:
                db[user_id]["invited_by"] = inviter_id
                db[inviter_id]["balance"] += 120000
                db[inviter_id]["invites_count"] += 1
                try: await context.bot.send_message(chat_id=int(inviter_id), text="🎉 یک کاربر جدید دعوت کردی!")
                except: pass
        save_db(db)
    
    await update.message.reply_text("به ربات بمب خوش آمدید 🌹", reply_markup=get_main_keyboard())

async def handle_message(update, context):
    text = update.message.text
    if "شروع کسب درآمد" in text:
        user_id = update.effective_user.id
        await update.message.reply_text(f"👇 با هر دعوت ۱۲۰,۰۰۰ تومان میده 👇\nhttps://t.me/{BOT_USERNAME}?start={user_id}")
    elif "حساب کاربری" in text:
        db = load_db()
        bal = db.get(str(update.effective_user.id), {}).get("balance", 0)
        await update.message.reply_text(f"موجودی شما: {bal:,} تومان")
    else:
        await update.message.reply_text("در حال حاضر در دست توسعه...")

if __name__ == "__main__":
    threading.Thread(target=start_health_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()
