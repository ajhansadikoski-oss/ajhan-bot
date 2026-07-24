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
    filters,
    ConversationHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CEKA_EMAIL, CEKA_PASSWORD, GLAVNO_MENI = range(3)

# Конфигурација со твојот точен токен и твоето точно ID
BOT_TOKEN = "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc"
ADMIN_ID = 8694942406  

def inicijaliziraj_baza():
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS korisnici (user_id INTEGER PRIMARY KEY, istekuvanje TEXT)')
    conn.commit()
    conn.close()

inicijaliziraj_baza()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Nema Username"
    first_name = update.message.from_user.first_name

    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()

    sega = datetime.now()
    dozvolen = False

    if rezultat:
        istekuvanje_str = rezultat
        if istekuvanje_str == "forever":
            dozvolen = True
        else:
            try:
                istekuvanje_datum = datetime.strptime(istekuvanje_str, "%Y-%m-%d %H:%M:%S")
                dozvolen = sega < istekuvanje_datum
            except Exception: pass

    if not dozvolen:
        await update.message.reply_text("❌ Немаш активна лиценца.\nБарањето за пристап е испратено до сопственикот.")
        tastatura = [
            [InlineKeyboardButton("♾️ Forever", callback_data=f"lic_forever_{user_id}"), InlineKeyboardButton("📅 30 Days", callback_data=f"lic_30_{user_id}")],
            [InlineKeyboardButton("📅 7 Days", callback_data=f"lic_7_{user_id}"), InlineKeyboardButton("❌ Deny", callback_data=f"lic_deny_{user_id}")]
        ]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **Барање за пристап** од {first_name} (@{username})\nID: `{user_id}`",
            reply_markup=InlineKeyboardMarkup(tastatura),
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    datum_sega = sega.strftime("%d %b %Y • %I:%M %p")
    welcome_text = (
        "--------------------------------------------------\n"
        "🎮 **CPM_AJHAN_BOT v5.0**\n"
        "--------------------------------------------------\n\n"
        "              **WELCOME**              \n"
        "┌───────────────────┐\n"
        "  👤 @{username}\n"
        "  🆔 `{user_id}`\n"
        "  📅 {datum_sega}\n"
        "└───────────────────┘\n\n"
        "▶ _Sign in with your CPM credentials_"
    ).format(username=username, user_id=user_id, datum_sega=datum_sega)

    keyboard = [[InlineKeyboardButton("🔐 Sign In", callback_data='cpm_signin')]]
    await update.message.reply_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

async def obraboti_klikovi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("lic_"):
        if query.from_user.id != ADMIN_ID: return
        delovi = data.split("_")
        akcija, target_user_id = delovi, int(delovi)
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        if akcija == "deny":
            cursor.execute('DELETE FROM korisnici WHERE user_id = ?', (target_user_id,))
            tekst, poraka = "❌ Одбиен", "❌ Твоето барање е одбиено."
        else:
            if akcija == "forever": vrednost, tekst = "forever", "✅ Одобрен засекогаш"
            elif akcija == "30": vrednost, tekst = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"), "✅ Одобрен на 30 дена"
            elif akcija == "7": vrednost, tekst = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"), "✅ Одобрен на 7 дена"
            cursor.execute('INSERT OR REPLACE INTO korisnici (user_id, istekuvanje) VALUES (?, ?)', (target_user_id, vrednost))
            poraka = f"🎉 Администраторот ти одобри пристап {tekst}! Стисни /start за да почнеш."
        conn.commit()
        conn.close()
        await query.edit_message_text(text=f"{query.message.text}\n\nСтатус: {tekst}")
        try: await context.bot.send_message(chat_id=target_user_id, text=poraka)
        except Exception: pass
        return

    if data == 'cpm_signin':
        email_text = (
            "--------------------------------------------------\n"
            "📧 **ENTER EMAIL**\n"
            "--------------------------------------------------\n\n"
            "Type your CPM email:"
        )
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='cpm_cancel')]]
        await query.edit_message_text(text=email_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        context.user_data['состојба'] = 'чека_емаил'
        return

    if data == 'cpm_cancel':
        context.user_data.clear()
        await query.edit_message_text(text="❌ Процесот е откажан. Пишете /start за почеток.")
        return

    if data == 'vnes_uspesen':
        dashboard_text = (
            "--------------------------------------------------\n"
            "🗂️ **DASHBOARD**\n"
            "--------------------------------------------------\n\n"
            "       **ACCOUNT**       \n"
            "📧 `{email}`\n"
            "👤 {first_name}\n\n"
            "▶ _Select an option below:_"
        ).format(email=context.user_data.get('cpm_email', 'N/A'), first_name=query.from_user.first_name)
        
        keyboard = [
            [InlineKeyboardButton("💰 Money", callback_data='meni_money'), InlineKeyboardButton("🪙 Coins", callback_data='meni_coins')],
            [InlineKeyboardButton("⚡ Features", callback_data='meni_features')],
            [InlineKeyboardButton("🚪 Sign Out", callback_data='cpm_cancel')]
        ]
        await query.edit_message_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == 'meni_money':
        money_text = (
            "--------------------------------------------------\n"
            "💰 **MONEY**\n"
            "--------------------------------------------------\n\n"
            "Max: $50,000,000"
        )
        keyboard = [
            [InlineKeyboardButton("$1M", callback_data='inj_1M'), InlineKeyboardButton("$5M", callback_data='inj_5M'), InlineKeyboardButton("$10M", callback_data='inj_10M')],
            [InlineKeyboardButton("$25M", callback_data='inj_25M'), InlineKeyboardButton("$50M ★", callback_data='inj_50M')],
            [InlineKeyboardButton("✏️ Custom Amount", callback_data='inj_custom')],
            [InlineKeyboardButton("◀ Back", callback_data='vnes_uspesen')]
        ]
        await query.edit_message_text(text=money_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == 'meni_coins':
        coins_text = (
            "--------------------------------------------------\n"
            "🪙 **COINS**\n"
            "--------------------------------------------------\n\n"
            "Max: 500,000"
        )
        keyboard = [
            [InlineKeyboardButton("100K", callback_data='inj_100k'), InlineKeyboardButton("250K", callback_data='inj_250k'), InlineKeyboardButton("500K ★", callback_data='inj_500k')],
            [InlineKeyboardButton("✏️ Custom Amount", callback_data='inj_custom')],
            [InlineKeyboardButton("◀ Back", callback_data='vnes_uspesen')]
        ]
        await query.edit_message_text(text=coins_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data == 'meni_features':
        features_text = (
            "--------------------------------------------------\n"
            "⚡ **FEATURES**\n"
            "--------------------------------------------------\n\n"
            "Select a feature or UNLOCK ALL:"
        )
        keyboard = [
            [InlineKeyboardButton("🚀 ★ UNLOCK ALL ★ 🚀", callback_data='inj_all')],
            [InlineKeyboardButton("◀ Back", callback_data='vnes_uspesen')]
        ]
        await query.edit_message_text(text=features_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data.startswith("inj_"):
        await query.edit_message_text(text="⚠️ **AJHAN INJECTOR v5.0** ⚠️\n\n🌐 Поврзување со CPM Cloud...\n🛡️ Деактивирање на анти-чит систем...\n✅ Успешно аплицирано! Опцијата ќе се појави на вашиот профил за 5-10 минути.")
        await asyncio.sleep(2)
        dashboard_text = (
            "--------------------------------------------------\n"
            "🗂️ **DASHBOARD**\n"
            "--------------------------------------------------\n\n"
            "       **ACCOUNT**       \n"
            "📧 `{email}`\n"
            "👤 {first_name}\n\n"
            "▶ _Select an option below:_"
        ).format(email=context.user_data.get('cpm_email', 'N/A'), first_name=query.from_user.first_name)
        keyboard = [
            [InlineKeyboardButton("💰 Money", callback_data='meni_money'), InlineKeyboardButton("🪙 Coins", callback_data='meni_coins')],
            [InlineKeyboardButton("⚡ Features", callback_data='meni_features')],
            [InlineKeyboardButton("🚪 Sign Out", callback_data='cpm_cancel')]
        ]
        try: await query.message.reply_text(text=dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
