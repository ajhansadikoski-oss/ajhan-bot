import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Заштита на токен
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN") or "8674559116:AAFZfZpBUsHXDowKuC1_UzDeSt6CvdV4"
ADMIN_ID = int(os.getenv("ADMIN_ID", 8694942406))

# Логирање
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- JSON БАЗА ЗА КОРИСНИЦИ ---
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "pending": []}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# --- ФУНКЦИИ ЗА ПРОВЕРКА НА ПРИСТАП ---
def check_access(user_id: int) -> tuple:
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

# --- CPM ФУНКЦИИ (симулација) ---
def cpm_set_coins(amount: int) -> str:
    return f"✅ Coins поставени на {amount}"

def cpm_set_money(amount: int) -> str:
    return f"✅ Money поставен на {amount}"

def cpm_unlock_all() -> str:
    return "✅ Отклучено: W16, Smoke, Horns, No Damage, Unlimited Fuel, Animations, Wheels, Houses"

def cpm_unlock_car(car_id: str) -> str:
    return f"🚗 Отклучен автомобил со ID: {car_id}"

# --- КОМАНДА /START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    has_access, status, expiry = check_access(user_id)
    
    if is_admin(user_id):
        await show_admin_panel(update, context)
        return
    
    if not has_access:
        if status == "banned":
            await update.message.reply_text(
                "🚫 **Вие сте блокирани од користење на овој бот!**\n"
                "Контактирајте го администраторот.",
                parse_mode="Markdown"
            )
            return
        elif status == "expired":
            await update.message.reply_text(
                "⏰ **Вашиот пристап истече!**\n"
                "Побарајте повторно дозвола од администраторот.",
                parse_mode="Markdown"
            )
            await request_access(update, context)
            return
        else:
            await request_access(update, context)
            return
    
    expiry_text = f"⏳ Истекува: {expiry.strftime('%d.%m.%Y %H:%M')}" if expiry else "♾️ Вечен пристап"
    keyboard = [
        [InlineKeyboardButton("💰 Economy", callback_data="economy")],
        [InlineKeyboardButton("🔓 Unlock Menu", callback_data="unlock")],
        [InlineKeyboardButton("✨ Chrome Menu", callback_data="chrome")],
        [InlineKeyboardButton("🚗 Car Unlock", callback_data="car_unlock")],
        [InlineKeyboardButton("🎨 Copy Vinyls", callback_data="copy_vinyls")],
        [InlineKeyboardButton("📋 Copy Cars", callback_data="copy_cars")],
        [InlineKeyboardButton("👤 Clone Account", callback_data="clone_account")],
        [InlineKeyboardButton("⚙️ Account Settings", callback_data="account_settings")],
        [InlineKeyboardButton("📈 Max Account", callback_data="max_account")],
        [InlineKeyboardButton("🚨 Siren Menu", callback_data="siren_menu")],
        [InlineKeyboardButton("🔧 Bumper Menu", callback_data="bumper_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🤖 **CPM Premium Bot**\n"
        f"👤 {user.first_name} (@{username})\n"
        f"{expiry_text}\n\n"
        f"Избери опција:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- ФУНКЦИЈА ЗА БАРАЊЕ ПРИСТАП ---
async def request_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    first_name = user.first_name or "No Name"
    last_name = user.last_name or ""
    
    db = load_db()
    pending = db.get("pending", [])
    
    if any(p["id"] == user_id for p in pending):
        await update.message.reply_text(
            "⏳ **Веќе имате испратено барање за пристап!**\n"
            "Почекајте администраторот да одговори.",
            parse_mode="Markdown"
        )
        return
    
    pending.append({
        "id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "date": datetime.now().isoformat()
    })
    db["pending"] = pending
    save_db(db)
    
    await update.message.reply_text(
        "📨 **Барањето за пристап е испратено!**\n"
        "Администраторот ќе ве одобри наскоро.\n"
        "Ве молиме почекајте.",
        parse_mode="Markdown"
    )
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **Ново барање за пристап!**\n"
             f"👤 Име: {first_name} {last_name}\n"
             f"🆔 ID: `{user_id}`\n"
             f"📛 @{username}\n\n"
             f"Користи:\n"
             f"/approve {user_id} [traenje]\n"
             f"/deny {user_id}\n"
             f"Пример: `/approve {user_id} 30d`\n"
             f"Опции: `forever`, `30d`, `7d`, `custom`",
        parse_mode="Markdown"
    )

# --- АДМИН КОМАНДИ ---
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = load_db()
    pending = db.get("pending", [])
    users = db.get("users", {})
    
    pending_text = f"📥 **Непрочитани барања:** {len(pending)}" if pending else "✅ Нема нови барања"
    total_users = len(users)
    
    keyboard = [
        [InlineKeyboardButton("📥 Прегледај барања", callback_data="admin_pending")],
        [InlineKeyboardButton("👥 Листа на корисници", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 Блокирани", callback_data="admin_banned")],
    ]
    
    await update.message.reply_text(
        f"👑 **Администраторски панел**\n\n"
        f"{pending_text}\n"
        f"👥 Вкупно корисници: {total_users}\n\n"
        f"Избери опција:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Само администратор!")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Користи: `/approve USER_ID DURATION`\n"
            "DURATION: `forever`, `30d`, `7d`, `custom` (на пример `custom 2026-12-31`)",
            parse_mode="Markdown"
        )
        return
    
    user_id = int(args[0])
    duration = args[1].lower()
    
    if duration == "forever":
        expiry = None
    elif duration == "30d":
        expiry = datetime.now() + timedelta(days=30)
    elif duration == "7d":
        expiry = datetime.now() + timedelta(days=7)
    elif duration == "custom" and len(args) >= 3:
        try:
            expiry = datetime.strptime(args[2], "%Y-%m-%d")
        except:
            await update.message.reply_text("❌ Формат за custom: `YYYY-MM-DD` (на пр. 2026-12-31)")
            return
    else:
        await update.message.reply_text("❌ Непознато траење. Користи: forever, 30d, 7d, custom")
        return
    
    db = load_db()
    pending = db.get("pending", [])
    db["pending"] = [p for p in pending if p["id"] != user_id]
    
    user_info = None
    for p in pending:
        if p["id"] == user_id:
            user_info = p
            break
    
    if not user_info:
        if str(user_id) in db["users"]:
            db["users"][str(user_id)]["expiry"] = expiry.isoformat() if expiry else None
            db["users"][str(user_id)]["banned"] = False
            save_db(db)
            await update.message.reply_text(f"✅ Пристапот е обновен за {user_id}!")
            return
        else:
            await update.message.reply_text("❌ Корисникот не е пронајден во барањата.")
            return
    
    db["users"][str(user_id)] = {
        "username": user_info.get("username"),
        "first_name": user_info.get("first_name"),
        "last_name": user_info.get("last_name"),
        "expiry": expiry.isoformat() if expiry else None,
        "banned": False,
        "approved_date": datetime.now().isoformat()
    }
    save_db(db)
    
    expiry_text = "♾️ вечен" if not expiry else f"до {expiry.strftime('%d.%m.%Y %H:%M')}"
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ **Вашето барање е одобрено!**\n"
             f"🕐 Пристап: {expiry_text}\n\n"
             f"Сега можете да го користите ботот. Пратете /start за да започнете.",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(f"✅ Корисникот {user_id} е одобрен! Пристап {expiry_text}")

async def admin_deny(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Само администратор!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Користи: `/deny USER_ID`", parse_mode="Markdown")
        return
    
    user_id = int(args[0])
    
    db = load_db()
    pending = db.get("pending", [])
    db["pending"] = [p for p in pending if p["id"] != user_id]
    
    if str(user_id) in db["users"]:
        db["users"][str(user_id)]["banned"] = True
    save_db(db)
    
    await context.bot.send_message(
        chat_id=user_id,
        text="❌ **Вашето барање е одбиено!**\nКонтактирајте го администраторот.",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(f"❌ Барањето на {user_id} е одбиено.")

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Само администратор!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Користи: `/ban USER_ID`", parse_mode="Markdown")
        return
    
    user_id = int(args[0])
    db = load_db()
    if str(user_id) in db["users"]:
        db["users"][str(user_id)]["banned"] = True
        save_db(db)
        await update.message.reply_text(f"🚫 Корисникот {user_id} е блокиран.")
        await context.bot.send_message(
            chat_id=user_id,
            text="🚫 **Вие сте блокирани од администраторот!**",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Корисникот не е пронајден.")

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Само администратор!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Користи: `/unban USER_ID`", parse_mode="Markdown")
        return
    
    user_id = int(args[0])
    db = load_db()
    if str(user_id) in db["users"]:
        db["users"][str(user_id)]["banned"] = False
        save_db(db)
        await update.message.reply_text(f"✅ Корисникот {user_id} е одблокиран.")
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ **Вие сте одблокирани!** Можете повторно да го користите ботот.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Корисникот не е пронајден.")

# --- BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "admin_pending":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Не сте администратор!")
            return
        db = load_db()
        pending = db.get("pending", [])
        if not pending:
            await query.edit_message_text("✅ Нема нови барања.", parse_mode="Markdown")
            return
        text = "📥 **Непрочитани барања:**\n\n"
        for p in pending[:10]:
            text += f"👤 {p.get('first_name')} {p.get('last_name')}\n"
            text += f"🆔 `{p.get('id')}`\n"
            text += f"📛 @{p.get('username')}\n"
            text += f"📅 {p.get('date')}\n\n"
        await query.edit_message_text(text, parse_mode="Markdown")
        return
    
    elif data == "admin_users":
        if not is_admin(user_id):
            return
        db = load_db()
        users = db.get("users", {})
        if not users:
            await query.edit_message_text("📭 Нема регистрирани корисници.", parse_mode="Markdown")
            return
        text = "👥 **Листа на корисници:**\n\n"
        for uid, u in list(users.items())[:10]:
            expiry = u.get("expiry")
            expiry_text = "♾️" if not expiry else f"до {expiry.split('T')[0]}"
            banned = "🚫" if u.get("banned") else "✅"
            text += f"{banned} `{uid}` - {u.get('first_name')} {expiry_text}\n"
        await query.edit_message_text(text, parse_mode="Markdown")
        return
    
    elif data == "admin_banned":
        if not is_admin(user_id):
            return
        db = load_db()
        users = db.get("users", {})
        banned = [uid for uid, u in users.items() if u.get("banned")]
        if not banned:
            await query.edit_message_text("✅ Нема блокирани корисници.", parse_mode="Markdown")
            return
        text = "🚫 **Блокирани корисници:**\n"
        for uid in banned:
            u = users[uid]
            text += f"`{uid}` - {u.get('first_name')}\n"
        await query.edit_message_text(text, parse_mode="Markdown")
        return
    
    has_access, status, expiry = check_access(user_id)
    if not has_access:
        if status == "banned":
            await query.edit_message_text("🚫 Вие сте блокирани!", parse_mode="Markdown")
        elif status == "expired":
            await query.edit_message_text("⏰ Вашиот пристап истече!", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Немате пристап. Пратете /start за да побарате дозвола.", parse_mode="Markdown")
        return
    
    if data == "economy":
        await query.edit_message_text(
            "💰 **Economy**\n"
            "Испрати:\n"
            "`setcoins 1000` - за Coins\n"
            "`setmoney 5000` - за Money",
            parse_mode="Markdown"
        )
        context.user_data["awaiting"] = "economy"
    
    elif data == "unlock":
        kb = [[InlineKeyboardButton("🔓 Unlock All (1 клик)", callback_data="unlock_all")],
              [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
        await query.edit_message_text("🔓 **Unlock Menu**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    
    elif data == "unlock_all":
        await query.edit_message_text(cpm_unlock_all(), parse_mode="Markdown")
    
    elif data == "chrome":
        kb = [
            [InlineKeyboardButton("🚗 Chrome Car", callback_data="chrome_car")],
            [InlineKeyboardButton("🪟 Chrome Windows", callback_data="chrome_windows")],
            [InlineKeyboardButton("💡 Chrome Headlights", callback_data="chrome_headlights")],
            [InlineKeyboardButton("⚙️ Chrome Wheels", callback_data="chrome_wheels")],
            [InlineKeyboardButton("✨ Full Chrome", callback_data="chrome_full")],
            [InlineKeyboardButton("🔄 Reset Chrome", callback_data="chrome_reset")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
        ]
        await query.edit_message_text("✨ **Chrome Menu**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    
    elif data.startswith("chrome_"):
        part = data.replace("chrome_", "").replace("_", " ").title()
        await query.edit_message_text(f"✅ {part} применет", parse_mode="Markdown")
    
    elif data == "car_unlock":
        await query.edit_message_text(
            "🚗 **Car Unlock**\n"
            "Испрати:\n"
            "`unlockcar 123` - за специфичен автомобил\n"
            "`unlockallcars` - за сите",
            parse_mode="Markdown"
        )
        context.user_data["awaiting"] = "car_unlock"
    
    elif data == "copy_vinyls":
        await query.edit_message_text(
            "🎨 **Copy Vinyls**\n"
            "Испрати:\n"
            "`copyvinyl FROM_CAR TO_CAR1,TO_CAR2`\n"
            "`copyvinylall FROM_CAR` - за сите",
            parse_mode="Markdown"
        )
        context.user_data["awaiting"] = "copy_vinyls"
    
    elif data == "copy_cars":
        await query.edit_message_text(
            "📋 **Copy Cars**\n"
            "Испрати:\n"
            "`copycar FROM_CAR TO_ACCOUNT`\n"
            "`copyallcars TO_ACCOUNT`",
            parse_mode="Markdown"
        )
        context.user_data["awaiting"] = "copy_cars"
    
    elif data == "clone_account":
        await query.edit_message_text(
            "👤 **Clone Account**\n"
            "Испрати:\n"
            "`clone TARGET_ACCOUNT_ID`",
            parse_mode="Markdown"
        )
        context.user_data["awaiting"] = "clone_account"
    
    elif data == "account_settings":
        kb = [
            [InlineKeyboardButton("📛 Change Name", callback_data="acc_name")],
            [InlineKeyboardButton("🆔 Change CPM ID", callback_data="acc_cpmid")],
            [InlineKeyboardButton("📧 Change Email", callback_data="acc_email")],
            [InlineKeyboardButton("🔑 Change Password", callback_data="acc_password")],
            [InlineKeyboardButton("🏁 Set Wins/Losses", callback_data="acc_wins")],
            [InlineKeyboardButton("🔢 Copy Number Plates", callback_data="acc_plates")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
        ]
        await query.edit_message_text("⚙️ **Account Settings**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    
    elif data.startswith("acc_"):
        await query.edit_message_text(f"⚙️ {data.replace('acc_', '').title()} - испрати нова вредност", parse_mode="Markdown")
        context.user_data["awaiting"] = data
    
    elif data == "max_account":
        await query.edit_message_text(
            "📈 **Max Account**\n"
            "✅ Сè отклучено\n"
            "W16, Smoke, Horns, No Damage, Fuel, Animations, Wheels, Houses, Сите автомобили",
            parse_mode="Markdown"
        )
    
    elif data == "siren_menu":
        await query.edit_message_text(
            "🚨 **Siren Menu**\n"
            "Испрати:\n"
            "`siren CAR_ID`\n"
            "`sirenall` - за сите",
            parse_mode="Markdown"
        )
        context.user_data["awaiting"] = "siren"
    
    elif data == "bumper_menu":
        kb = [
            [InlineKeyboardButton("🔧 Remove Front", callback_data="bumper_front")],
            [InlineKeyboardButton("🔧 Remove Rear", callback_data="bumper_rear")],
            [InlineKeyboardButton("🔧 Remove Both", callback_data="bumper_both")],
            [InlineKeyboardButton("🔧 Remove All Cars", callback_data="bumper_all")],
            [InlineKeyboardButton("🔧 Remove Specific Car", callback_data="bumper_specific")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
        ]
        await query.edit_message_text("🔧 **Bumper Menu**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    
    elif data.startswith("bumper_"):
        if data == "bumper_all":
            await query.edit_message_text("🔧 Браници отстранети од сите автомобили", parse_mode="Markdown")
        elif data == "bumper_specific":
            await query.edit_message_text("Испрати ID на автомобил:\n`removebumper 456`", parse_mode="Markdown")
            context.user_data["awaiting"] = "bumper_specific"
        else:
            await query.edit_message_text("🔧 Браници отстранети", parse_mode="Markdown")
    
    elif data == "back_main":
        await start(update, context)

# --- TEXT HANDLER ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.strip()
    
    has_access, status, _ = check_access(user_id)
    if not has_access:
        await update.message.reply_text("❌ Немате пристап до оваа функција. Пратете /start за да побарате дозвола.")
        return
    
    awaiting = context.user_data.get("awaiting", "")
    
    if awaiting == "economy":
        if user_text.startswith("setcoins"):
            try:
                amt = int(user_text.split()[1])
                await update.message.reply_text(cpm_set_coins(amt))
            except:
                await update.message.reply_text("❌ Испрати: `setcoins 1000`", parse_mode="Markdown")
        elif user_text.startswith("setmoney"):
            try:
                amt = int(user_text.split()[1])
                await update.message.reply_text(cpm_set_money(amt))
            except:
                await update.message.reply_text("❌ Испрати: `setmoney 5000`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Користи `setcoins` или `setmoney`", parse_mode="Markdown")
    
    elif awaiting == "car_unlock":
        if user_text.startswith("unlockcar"):
            car_id = user_text.replace("unlockcar", "").strip()
            await update.message.reply_text(cpm_unlock_car(car_id))
        elif user_text.startswith("unlockallcars"):
            await update.message.reply_text("✅ Сите автомобили отклучени")
        else:
            await update.message.reply_text("❌ Користи `unlockcar ID` или `unlockallcars`", parse_mode="Markdown")
    
    elif awaiting == "copy_vinyls":
        if user_text.startswith("copyvinyl"):
            parts = user_text.split()
            if len(parts) >= 3:
                await update.message.reply_text(f"🎨 Винили копирани од {parts[1]} во {parts[2]}")
            else:
                await update.message.reply_text("❌ Формат: `copyvinyl FROM_CAR TO_CAR1,TO_CAR2`", parse_mode="Markdown")
        elif user_text.startswith("copyvinylall"):
            await update.message.reply_text("🎨 Винили копирани на сите автомобили")
    
    elif awaiting == "copy_cars":
        if user_text.startswith("copycar"):
            parts = user_text.split()
            if len(parts) >= 3:
                await update.message.reply_text(f"📋 Автомобил {parts[1]} копиран во {parts[2]}")
            else:
                await update.message.reply_text("❌ Формат: `copycar FROM_CAR TO_ACCOUNT`", parse_mode="Markdown")
        elif user_text.startswith("copyallcars"):
            acc = user_text.replace("copyallcars", "").strip()
            await update.message.reply_text(f"📋 Сите автомобили копирани во {acc}")
    
    elif awaiting == "clone_account":
        if user_text.startswith("clone"):
            target = user_text.replace("clone", "").strip()
            await update.message.reply_text(f"👤 Акаунт клониран во {target}")
    
    elif awaiting == "siren":
        if user_text.startswith("siren"):
            car_id = user_text.replace("siren", "").strip()
            await update.message.reply_text(f"🚨 Сирена поставена на автомобил {car_id}")
        elif user_text.startswith("sirenall"):
            await update.message.reply_text("🚨 Сирени на сите автомобили")
    
    elif awaiting == "bumper_specific":
        if user_text.startswith("removebumper"):
            car_id = user_text.replace("removebumper", "").strip()
            await update.message.reply_text(f"🔧 Браници отстранети од автомобил {car_id}")
    
    elif awaiting.startswith("acc_"):
        await update.message.reply_text(f"✅ {awaiting} променето во: {user_text}")
    
    else:
        await update.message.reply_text("❌ Непозната команда. Користи /start")
    
    context.user_data["awaiting"] = ""

# --- ГЛАВНА ФУНКЦИЈА (ПОПРАВЕНА ЗА RENDER) ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", admin_approve))
    app.add_handler(CommandHandler("deny", admin_deny))
    app.add_handler(CommandHandler("ban", admin_ban))
    app.add_handler(CommandHandler("unban", admin_unban))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    port = int(os.environ.get("PORT", 8443))
    
    # ⭐ КЛУЧНО: Земете го Render URL-то
    render_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if render_url:
        webhook_url = f"https://{render_url}/webhook"
        print(f"✅ Ботот стартува на webhook: {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )
    else:
        print("⚠️ Локален режим (polling)")
        app.run_polling()

if __name__ == "__main__":
    main()
