import os
import json
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not set!")

ADMIN_ID = int(os.environ.get("ADMIN_ID", 8694942406))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "pending": []}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def check_access(user_id: int):
    db = load_db()
    user_id_str = str(user_id)
    
    if user_id == ADMIN_ID:
        return True, "admin", None
    
    if user_id_str in db["users"]:
        user_data = db["users"][user_id_str]
        if user_data.get("banned", False):
            return False, "banned", None
        
        expiry = user_data.get("expiry")
        if expiry:
            expiry_date = datetime.fromisoformat(expiry)
            if datetime.now() > expiry_date:
                return False, "expired", expiry_date
        
        return True, "active", expiry
    
    return False, "no_access", None

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def cpm_set_coins(amount: int) -> str:
    return f"Coins set to {amount}"

def cpm_set_money(amount: int) -> str:
    return f"Money set to {amount}"

def cpm_unlock_all() -> str:
    return "Unlocked: W16, Smoke, Horns, No Damage, Unlimited Fuel, Animations, Wheels, Houses"

def cpm_unlock_car(car_id: str) -> str:
    return f"Car {car_id} unlocked"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    
    has_access, status, expiry = check_access(user_id)
    
    if is_admin(user_id):
        await show_admin_panel(update, context)
        return
    
    if not has_access:
        if status == "banned":
            await update.message.reply_text("You are banned!")
            return
        elif status == "expired":
            await update.message.reply_text("Your access expired! Request again.")
            await request_access(update, context)
            return
        else:
            await request_access(update, context)
            return
    
    keyboard = [
        [InlineKeyboardButton("Economy", callback_data="economy")],
        [InlineKeyboardButton("Unlock Menu", callback_data="unlock")],
        [InlineKeyboardButton("Chrome Menu", callback_data="chrome")],
        [InlineKeyboardButton("Car Unlock", callback_data="car_unlock")],
        [InlineKeyboardButton("Copy Vinyls", callback_data="copy_vinyls")],
        [InlineKeyboardButton("Copy Cars", callback_data="copy_cars")],
        [InlineKeyboardButton("Clone Account", callback_data="clone_account")],
        [InlineKeyboardButton("Account Settings", callback_data="account_settings")],
        [InlineKeyboardButton("Max Account", callback_data="max_account")],
        [InlineKeyboardButton("Siren Menu", callback_data="siren_menu")],
        [InlineKeyboardButton("Bumper Menu", callback_data="bumper_menu")],
    ]
    
    await update.message.reply_text(
        "CPM Premium Bot\nChoose option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def request_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    
    db = load_db()
    pending = db.get("pending", [])
    
    if any(p["id"] == user_id for p in pending):
        await update.message.reply_text("You already have a pending request!")
        return
    
    pending.append({
        "id": user_id,
        "username": user.username or user.first_name,
        "first_name": user.first_name or "No Name",
        "last_name": user.last_name or "",
        "date": datetime.now().isoformat()
    })
    db["pending"] = pending
    save_db(db)
    
    await update.message.reply_text("Access request sent! Wait for admin approval.")
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"New access request!\nID: {user_id}\nUser: {user.first_name}\n\nUse: /approve {user_id} forever"
    )

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = load_db()
    pending = db.get("pending", [])
    users = db.get("users", {})
    
    keyboard = [
        [InlineKeyboardButton("View Pending", callback_data="admin_pending")],
        [InlineKeyboardButton("List Users", callback_data="admin_users")],
        [InlineKeyboardButton("Banned Users", callback_data="admin_banned")],
    ]
    
    await update.message.reply_text(
        f"Admin Panel\nPending: {len(pending)}\nUsers: {len(users)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Use: /approve USER_ID")
        return
    
    user_id = int(args[0])
    
    db = load_db()
    pending = db.get("pending", [])
    db["pending"] = [p for p in pending if p["id"] != user_id]
    
    user_info = None
    for p in pending:
        if p["id"] == user_id:
            user_info = p
            break
    
    if not user_info:
        await update.message.reply_text("User not found!")
        return
    
    db["users"][str(user_id)] = {
        "username": user_info.get("username"),
        "first_name": user_info.get("first_name"),
        "last_name": user_info.get("last_name"),
        "expiry": None,
        "banned": False,
        "approved_date": datetime.now().isoformat()
    }
    save_db(db)
    
    await context.bot.send_message(
        chat_id=user_id,
        text="Access granted! Send /start to use the bot."
    )
    
    await update.message.reply_text(f"User {user_id} approved!")

async def admin_deny(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Use: /deny USER_ID")
        return
    
    user_id = int(args[0])
    
    db = load_db()
    pending = db.get("pending", [])
    db["pending"] = [p for p in pending if p["id"] != user_id]
    save_db(db)
    
    await context.bot.send_message(
        chat_id=user_id,
        text="Access denied!"
    )
    
    await update.message.reply_text(f"User {user_id} denied!")

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Use: /ban USER_ID")
        return
    
    user_id = int(args[0])
    db = load_db()
    if str(user_id) in db["users"]:
        db["users"][str(user_id)]["banned"] = True
        save_db(db)
        await update.message.reply_text(f"User {user_id} banned!")

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Use: /unban USER_ID")
        return
    
    user_id = int(args[0])
    db = load_db()
    if str(user_id) in db["users"]:
        db["users"][str(user_id)]["banned"] = False
        save_db(db)
        await update.message.reply_text(f"User {user_id} unbanned!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "admin_pending":
        if not is_admin(user_id):
            await query.edit_message_text("Admin only!")
            return
        db = load_db()
        pending = db.get("pending", [])
        if not pending:
            await query.edit_message_text("No pending requests.")
            return
        text = "Pending requests:\n"
        for p in pending:
            text += f"{p.get('first_name')} - ID: {p.get('id')}\n"
        await query.edit_message_text(text)
        return
    
    elif data == "admin_users":
        if not is_admin(user_id):
            return
        db = load_db()
        users = db.get("users", {})
        if not users:
            await query.edit_message_text("No users.")
            return
        text = "Users:\n"
        for uid, u in list(users.items())[:10]:
            text += f"{uid} - {u.get('first_name')}\n"
        await query.edit_message_text(text)
        return
    
    elif data == "admin_banned":
        if not is_admin(user_id):
            return
        db = load_db()
        users = db.get("users", {})
        banned = [uid for uid, u in users.items() if u.get("banned")]
        if not banned:
            await query.edit_message_text("No banned users.")
            return
        text = "Banned users:\n"
        for uid in banned:
            text += f"{uid}\n"
        await query.edit_message_text(text)
        return
    
    has_access, status, _ = check_access(user_id)
    if not has_access:
        await query.edit_message_text("No access!")
        return
    
    if data == "economy":
        await query.edit_message_text("Economy: Use /setcoins or /setmoney")
        context.user_data["awaiting"] = "economy"
    
    elif data == "unlock":
        await query.edit_message_text("Unlock Menu")
    
    elif data == "chrome":
        await query.edit_message_text("Chrome Menu")
    
    elif data == "car_unlock":
        await query.edit_message_text("Car Unlock")
    
    elif data == "copy_vinyls":
        await query.edit_message_text("Copy Vinyls")
    
    elif data == "copy_cars":
        await query.edit_message_text("Copy Cars")
    
    elif data == "clone_account":
        await query.edit_message_text("Clone Account")
    
    elif data == "account_settings":
        await query.edit_message_text("Account Settings")
    
    elif data == "max_account":
        await query.edit_message_text("Max Account")
    
    elif data == "siren_menu":
        await query.edit_message_text("Siren Menu")
    
    elif data == "bumper_menu":
        await query.edit_message_text("Bumper Menu")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.strip()
    
    has_access, status, _ = check_access(user_id)
    if not has_access:
        await update.message.reply_text("No access!")
        return
    
    awaiting = context.user_data.get("awaiting", "")
    
    if awaiting == "economy":
        if user_text.startswith("setcoins"):
            try:
                amt = int(user_text.split()[1])
                await update.message.reply_text(cpm_set_coins(amt))
            except:
                await update.message.reply_text("Use: setcoins 1000")
        elif user_text.startswith("setmoney"):
            try:
                amt = int(user_text.split()[1])
                await update.message.reply_text(cpm_set_money(amt))
            except:
                await update.message.reply_text("Use: setmoney 5000")
        else:
            await update.message.reply_text("Use setcoins or setmoney")
    
    context.user_data["awaiting"] = ""

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", admin_approve))
    app.add_handler(CommandHandler("deny", admin_deny))
    app.add_handler(CommandHandler("ban", admin_ban))
    app.add_handler(CommandHandler("unban", admin_unban))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
