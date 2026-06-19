import os
import threading
import json
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# تنظیمات اصلی
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "5989298023"
DB_FILE = "users_db.json"
WITHDRAW_FILE = "withdraws.json"

# توابع کمکی برای کار با دیتابیس
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# دستور ادمین: /admin add [id] [amount] یا /admin send [text]
async def admin_panel(update, context):
    if str(update.effective_user.id) != ADMIN_ID:
        return
    
    cmd = context.args
    db = load_json(DB_FILE)
    
    if not cmd:
        withdraws = load_json(WITHDRAW_FILE)
        await update.message.reply_text(f"پنل ادمین فعال.\nدرخواست‌های برداشت: {json.dumps(withdraws, ensure_ascii=False)}\n\nراهنما:\n/admin add [ID] [مبلغ]\n/admin send [متن]")
        return

    action = cmd[0]
    
    if action == "add" and len(cmd) >= 3:
        uid, amt = cmd[1], int(cmd[2])
        if uid in db:
            db[uid]["balance"] = db.get(uid, {}).get("balance", 0) + amt
            save_json(DB_FILE, db)
            await update.message.reply_text(f"مبلغ {amt} تومان به موجودی {uid} اضافه شد.")
    
    elif action == "send" and len(cmd) > 1:
        msg = " ".join(cmd[1:])
        for uid in db:
            try: await context.bot.send_message(chat_id=int(uid), text=msg)
            except: continue
        await update.message.reply_text("پیام همگانی ارسال شد.")

# دستور شروع
async def start(update, context):
    db = load_json(DB_FILE)
    uid = str(update.effective_user.id)
    if uid not in db:
        db[uid] = {"balance": 0, "username": update.effective_user.first_name}
        save_json(DB_FILE, db)
    
    kb = ReplyKeyboardMarkup([["💎 شروع کسب درآمد 💎"], ["🏠 حساب کاربری", "💸 برداشت از حساب"]], resize_keyboard=True)
    await update.message.reply_text("به ربات کسب درآمد بمب خوش آمدید 🌹", reply_markup=kb)

# مدیریت پیام‌های متنی
async def handle_message(update, context):
    text = update.message.text
    uid = str(update.effective_user.id)
    
    if "حساب کاربری" in text:
        db = load_json(DB_FILE)
        bal = db.get(uid, {}).get("balance", 0)
        await update.message.reply_text(f"موجودی فعلی شما: {bal} تومان")
        
    elif "برداشت از حساب" in text:
        await update.message.reply_text("لطفاً مبلغ مورد نظر برای برداشت را به عدد وارد کنید:")
        context.user_data['wait_withdraw'] = True
        
    elif context.user_data.get('wait_withdraw'):
        w = load_json(WITHDRAW_FILE)
        w[uid] = {"amount": text, "username": update.effective_user.username or "NoUser"}
        save_json(WITHDRAW_FILE, w)
        context.user_data['wait_withdraw'] = False
        await update.message.reply_text("درخواست برداشت شما با موفقیت ثبت شد و به ادمین ارسال گردید.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)
