import os
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "5989298023" # آیدی ادمین شما
BOT_USERNAME = "bombdaramadbot"
DB_FILE = "users_db.json"
WITHDRAW_FILE = "withdraws.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class RailwayHealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Active!")
    def log_message(self, format, *args): return

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    HTTPServer(("0.0.0.0", port), RailwayHealthCheck).serve_forever()

async def start(update, context):
    user = update.effective_user
    db = load_json(DB_FILE)
    if str(user.id) not in db:
        db[str(user.id)] = {"balance": 0, "invites": 0, "username": user.first_name}
        save_json(DB_FILE, db)
    
    kb = ReplyKeyboardMarkup([["💎 شروع کسب درآمد 💎"], ["🏠 حساب کاربری", "💸 برداشت از حساب"]], resize_keyboard=True)
    await update.message.reply_text("به ربات خوش آمدید!", reply_markup=kb)

async def admin_panel(update, context):
    if str(update.effective_user.id) != ADMIN_ID: return
    withdraws = load_json(WITHDRAW_FILE)
    if not withdraws:
        await update.message.reply_text("هیچ درخواست برداشتی وجود ندارد.")
        return
    msg = "لیست درخواست‌های برداشت:\n\n"
    for uid, info in withdraws.items():
        msg += f"👤 کاربر: {uid} | 💰 مبلغ: {info['amount']} تومان\n"
    await update.message.reply_text(msg)

async def handle_message(update, context):
    text = update.message.text
    user_id = str(update.effective_user.id)
    
    if "شروع کسب درآمد" in text:
        await update.message.reply_text(f"لینک دعوت:\nhttps://t.me/{BOT_USERNAME}?start={user_id}")
    elif "حساب کاربری" in text:
        db = load_json(DB_FILE)
        bal = db.get(user_id, {}).get("balance", 0)
        await update.message.reply_text(f"موجودی: {bal} تومان")
    elif "برداشت از حساب" in text:
        await update.message.reply_text("لطفا مبلغ برداشت را به صورت عددی بفرستید:")
        context.user_data['waiting_withdraw'] = True
    elif context.user_data.get('waiting_withdraw'):
        amount = text
        withdraws = load_json(WITHDRAW_FILE)
        withdraws[user_id] = {"amount": amount}
        save_json(WITHDRAW_FILE, withdraws)
        context.user_data['waiting_withdraw'] = False
        await update.message.reply_text("درخواست شما ثبت شد.")

if __name__ == "__main__":
    threading.Thread(target=start_health_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)
