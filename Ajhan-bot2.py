import logging
import sqlite3
import asyncio
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Твојот токен и твоето точно ADMIN ID
BOT_TOKEN = "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc" 
ADMIN_ID = 8694942406  

def inicijaliziraj_baza():
    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS licenci (id TEXT PRIMARY KEY, data TEXT)')
    conn.commit()
    conn.close()

inicijaliziraj_baza()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user if update.message else update.callback_query.from_user
    username = user.username if user.username else "User"

    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM licenci WHERE id = ?', (user.id,))
    rezultat = cursor.fetchone()
    conn.close()

    sega = datetime.now()
    dozvolen = False

    if rezultat:
        istekuvanje_str = rezultat[0]
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
        poraka_lic = "❌ Немате активна лиценца. Барањето е испратено до админот."
        if update.message:
            await update.message.reply_text(poraka_lic)
        elif update.callback_query:
            await update.callback_query.message.reply_text(poraka_lic)
            
        tastatura = [
            [
                InlineKeyboardButton("✅ Засекогаш", callback_data=f"lic:forever:{user.id}"),
                InlineKeyboardButton("📅 30 Дена", callback_data=f"lic:30:{user.id}")
            ],
            [InlineKeyboardButton("❌ Одбиј", callback_data=f"lic:deny:{user.id}")]
        ]
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Барање за лиценца од @{username} (`{user.id}`)\nИзберете опција:",
                reply_markup=InlineKeyboardMarkup(tastatura),
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Грешка при праќање до админ: {e}")
        return

    datum_sega = sega.strftime("%d %B %Y")
    welcome_text = (
        "...\n"
        "   **CPM AJHAN BOT v5.0**\n"
        "-------------------------------\n"
        "          **WELCOME**\n"
        "👤 @{username}\n"
        "🆔 `{user_id}`\n"
        "📅 {datum_sega}\n"
        "-------------------------------\n"
        "🗝️ Успешно сте најавени во CPM ботот!"
    ).format(username=username, user_id=user.id, datum_sega=datum_sega)

    keyboard = [[InlineKeyboardButton("📱 Отвори мени", callback_data="open_menu")]]
    
    if update.message:
        await update.message.reply_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def main_menu_display(query):
    dashboard_text = (
        "...\n"
        "   **DASHBOARD**\n"
        "-------------------------------\n"
        "       **ACCOUNT**\n"
        "📢 Изберете опција подолу или одете на најава:"
    )
    keyboard = [
        [InlineKeyboardButton("🔑 Најави се во CPM", callback_data="cpm_signin")],
        [InlineKeyboardButton("💰 Money", callback_data="menu_money"), InlineKeyboardButton("🪙 Coins", callback_data="menu_coins")],
        [InlineKeyboardButton("⚡ Features", callback_data="menu_features"), InlineKeyboardButton("🚗 Cars", callback_data="menu_cars")]
    ]
    await query.edit_message_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def obraboti_klikovi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("lic:"):
        delovi = data.split(":")
        # ПОПРАВЕНО: Додадени се точните пајтон индекси [1] и [2]
        akcija = delovi[1]
        target_user_id = int(delovi[2])
        
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        
        if akcija == "deny":
            cursor.execute('DELETE FROM licenci WHERE id = ?', (target_user_id,))
            poraka = "❌ Вашето барање за лиценца е одбиено."
            admin_odgovor = f"❌ Го одбивте корисникот {target_user_id}"
        else:
            if akcija == "forever":
                vrednost = "forever"
            elif akcija == "30":
                vrednost = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data) VALUES (?, ?)', (target_user_id, vrednost))
            poraka = "✅ Администраторот ја одобри вашата лиценца! Напишете /start за пристап."
            admin_odgovor = f"✅ Одобрена лиценца ({akcija}) за {target_user_id}"
        
        conn.commit()
        conn.close()
        try:
            await context.bot.send_message(chat_id=target_user_id, text=poraka)
            await query.edit_message_text(text=admin_odgovor)
        except Exception:
            pass
        return

    if data == "cpm_signin":
        await query.edit_message_text("📝 Внесете го вашиот CPM Email:")
        context.user_data['sostojba'] = 'CEKA_EMAIL'
        return

    if data in ["open_menu", "main_menu", "vnes_uspesen"]:
        await main_menu_display(query)
        return

    if data == "menu_money":
        money_text = "...\n   **MONEY**\n-------------------------------\n💵 Max: $50,000,000"
        keyboard = [
            [InlineKeyboardButton("$10M", callback_data="add_10m"), InlineKeyboardButton("$20M", callback_data="add_20m")],
            [InlineKeyboardButton("$50M (MAX)", callback_data="add_50m")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        await query.edit_message_text(text=money_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == "menu_coins":
        coins_text = "...\n   **COINS**\n-------------------------------\n🪙 Max: 500,000"
        keyboard = [
            [InlineKeyboardButton("10k", callback_data="add_10k"), InlineKeyboardButton("50k", callback_data="add_50k")],
            [InlineKeyboardButton("500k (MAX)", callback_data="add_500k")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        await query.edit_message_text(text=coins_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == "menu_features":
        features_text = "...\n   **FEATURES**\n-------------------------------\nИзберете опција:"
        keyboard = [
            [InlineKeyboardButton("🏎️ King Engine", callback_data="add_king")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        await query.edit_message_text(text=features_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == "menu_cars":
        cars_text = "...\n   **CARS**\n-------------------------------\nИзберете возило:"
        keyboard = [
            [InlineKeyboardButton("🚗 Отклучи ги сите коли", callback_data="add_all_cars")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        await query.edit_message_text(text=cars_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data.startswith("add_"):
        await query.edit_message_text(text="🔄 Процесирање на барањето...")
        await asyncio.sleep(1.5)
        
        uspesno_text = f"✅ Успешно активирано/додадено: **{data.replace('add_', '')}**"
        keyboard = [[InlineKeyboardButton("👤 Назад во мени", callback_data="main_menu")]]
        await query.message.reply_text(text=uspesno_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

async def obraboti_tekst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sostojba = context.user_data.get('sostojba')
    vnesen_tekst = update.message.text

    if sostojba == 'CEKA_EMAIL':
        context.user_data['email'] = vnesen_tekst
        await update.message.reply_text("🔒 Сега внесете ја вашата лозинка:")
        context.user_data['sostojba'] = 'CEKA_PASSWORD'
        return

    elif sostojba == 'CEKA_PASSWORD':
        context.user_data['password'] = vnesen_tekst
        context.user_data['sostojba'] = None
        
        email = context.user_data.get('email')
        
        dashboard_text = (
            "...\n"
            "   **DASHBOARD**\n"
            "-------------------------------\n"
            "       **ACCOUNT**\n"
            "📧 Email: `{}`\n"
            "🔑 Лозинка: Скриена\n"
            "📢 Изберете опција од менито:"
        ).format(email)

        keyboard = [
            [InlineKeyboardButton("💰 Money", callback_data="menu_money"), InlineKeyboardButton("🪙 Coins", callback_data="menu_coins")],
            [InlineKeyboardButton("⚡ Features", callback_data="menu_features"), InlineKeyboardButton("🚗 Cars", callback_data="menu_cars")]
        ]
        await update.message.reply_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

if __name__ == '__main__':
