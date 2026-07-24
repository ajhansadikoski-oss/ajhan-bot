import logging
import sqlite3
import os
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
    ConversationHandler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константи
ADMIN_MENU, CEKA_BRISI_ID, CEKA_CUSTOM_DAYS, ADMIN_ODOBRI_LICENCA = range(4)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8674559116:AAFuZWJJLVY-qMAHBSr7Z6om686b1zeGxKc")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8694942406"))

# ========== БАЗА ==========
def inicijaliziraj_baza():
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS korisnici (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            istekuvanje TEXT,
            datum_dodeluvanje TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS baranja_za_pari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            iznos TEXT,
            datum TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Базата е иницијализирана")

inicijaliziraj_baza()

# ========== GG СКРИПТИ ==========
def generiraj_gg_skripta(funkcija, user_id):
    if funkcija == "W16":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('2000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('5000', gg.TYPE_DWORD)
gg.alert('✅ W16 Motor отклучен!')"""
    elif funkcija == "PARI":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('999999999', gg.TYPE_DWORD)
gg.alert('💰 Додадени $999,999,999!')"""
    elif funkcija == "UnlockAll":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('1000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('999999999', gg.TYPE_DWORD)
gg.searchNumber('2000', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('5000', gg.TYPE_DWORD)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(1000)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('🌟 СЕ Е ОТКЛУЧЕНО! 🎉')"""
    elif funkcija == "Horns":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(1000)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('✅ Сите хорни отклучени!')"""
    elif funkcija == "NoDmg":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('100', gg.TYPE_FLOAT)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_FLOAT)
gg.alert('🛡️ Штетата е исклучена!')"""
    elif funkcija == "Fuel":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('100', gg.TYPE_FLOAT)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_FLOAT)
gg.alert('⛽ Бесконечно гориво!')"""
    elif funkcija == "Smoke":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('💨 Ефекти на чад отклучени!')"""
    elif funkcija == "Animations":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(500)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('🎭 Сите анимации отклучени!')"""
    elif funkcija == "Wheels":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(200)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('⚙️ Сите тркала отклучени!')"""
    elif funkcija == "Houses":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('0', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('1', gg.TYPE_DWORD)
gg.alert('🏠 Сите куќи отклучени!')"""
    elif funkcija == "Levels":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('1', gg.TYPE_DWORD)
gg.getResults(100)
gg.editAll('999', gg.TYPE_DWORD)
gg.alert('📈 Макс ниво 999!')"""
    elif funkcija == "Rank":
        return f"""gg.setRanges(gg.REGION_C_ALLOC)
gg.searchNumber('1', gg.TYPE_DWORD)
gg.getResults(50)
gg.editAll('999999', gg.TYPE_DWORD)
gg.alert('👑 Макс ранг!')"""
    else:
        return ""

# ========== ПОМОШНА ФУНКЦИЈА ЗА ПРОВЕРКА ==========
def proveri_licenca(user_id):
    """Проверува дали корисникот има валидна лиценца"""
    try:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT status, istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
        rezultat = cursor.fetchone()
        conn.close()
        
        if not rezultat:
            return False, "Нема корисник"
        
        status, istekuvanje = rezultat
        
        if status != 'approved':
            return False, f"Статус: {status}"
        
        if istekuvanje and istekuvanje != "forever":
            try:
                istek_datum = datetime.strptime(istekuvanje, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > istek_datum:
                    return False, "Лиценцата истекна"
            except:
                pass
        
        return True, "Валидна"
        
    except Exception as e:
        logger.error(f"Грешка при проверка: {e}")
        return False, f"Грешка: {e}"

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    first_name = update.message.from_user.first_name or "User"
    
    logger.info(f"📱 START од {user_id} (@{username})")

    # АДМИН
    if user_id == ADMIN_ID:
        await prikazi_admin_panel(update)
        return ADMIN_MENU

    # ПРОВЕРКА ДАЛИ КОРИСНИКОТ ПОСТОИ
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, status, istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()
    
    # АКО НЕ ПОСТОИ - КРЕИРАЈ БАРАЊЕ
    if not rezultat:
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO korisnici (user_id, username, first_name, status, datum_dodeluvanje) 
            VALUES (?, ?, ?, 'pending', ?)
        ''', (user_id, username, first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ **Барањето е испратено!**\n\n"
            f"👤 Корисник: @{username}\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"📌 Почекајте администраторот да ве одобри.",
            parse_mode='Markdown'
        )
        
        # ПОРАКА ДО АДМИН
        tastatura = [
            [
                InlineKeyboardButton("♾️ Forever", callback_data=f"lic_forever_{user_id}"),
                InlineKeyboardButton("📅 30 Days", callback_data=f"lic_30_{user_id}")
            ],
            [
                InlineKeyboardButton("📅 7 Days", callback_data=f"lic_7_{user_id}"),
                InlineKeyboardButton("📝 Custom", callback_data=f"lic_custom_{user_id}")
            ],
            [
                InlineKeyboardButton("❌ Deny", callback_data=f"lic_deny_{user_id}")
            ]
        ]
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **НОВО БАРАЊЕ!**\n\n"
                 f"👤 {first_name}\n"
                 f"🆔 `{user_id}`\n"
                 f"📌 @{username}\n"
                 f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            reply_markup=InlineKeyboardMarkup(tastatura),
            parse_mode='Markdown'
        )
        return
    
    # КОРИСНИКОТ ПОСТОИ
    user_id_db, status, istekuvanje = rezultat
    
    # АКО Е ОДБИЕН
    if status == 'denied':
        await update.message.reply_text(
            "❌ **Вашето барање е одбиено!**",
            parse_mode='Markdown'
        )
        return
    
    # АКО Е PENDING
    if status == 'pending':
        await update.message.reply_text(
            "⏳ **Веќе имате испратено барање!**\n\n"
            "Почекајте администраторот да го одобри.",
            parse_mode='Markdown'
        )
        return
    
    # АКО Е APPROVED
    if status == 'approved':
        # ПРОВЕРИ ДАЛИ ЛИЦЕНЦАТА ИСТЕКНА
        if istekuvanje and istekuvanje != "forever":
            try:
                istek_datum = datetime.strptime(istekuvanje, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > istek_datum:
                    # ИСТЕКНА
                    conn = sqlite3.connect('licenci.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE korisnici SET status = "expired" WHERE user_id = ?', (user_id,))
                    conn.commit()
                    conn.close()
                    
                    await update.message.reply_text(
                        "❌ **Вашата лиценца истекна!**\n\n"
                        "Контактирајте го администраторот.",
                        parse_mode='Markdown'
                    )
                    return
            except Exception as e:
                logger.error(f"Грешка: {e}")
        
        # ✅ ВАЛИДНА ЛИЦЕНЦА - GG МЕНИ
        await prikazi_gg_menu(update, context)
        return
    
    # АКО Е EXPIRED
    if status == 'expired':
        await update.message.reply_text(
            "❌ **Вашата лиценца истекна!**\n\n"
            "Контактирајте го администраторот.",
            parse_mode='Markdown'
        )
        return
    
    # ДЕФАУЛТ
    await update.message.reply_text(
        "❌ **Грешка!**\n\n"
        "Контактирајте го администраторот.",
        parse_mode='Markdown'
    )

# ========== GG МЕНИ ==========
async def prikazi_gg_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = query.from_user.id if query else update.message.from_user.id
    
    # ПРОВЕРКА
    validna, poraka = proveri_licenca(user_id)
    if not validna:
        if query:
            await query.edit_message_text(
                f"❌ **Немате активна лиценца!**\n\n{poraka}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ **Немате активна лиценца!**\n\n{poraka}",
                parse_mode='Markdown'
            )
        return
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    conn.close()
    
    username = rezultat[0] if rezultat else "N/A"
    istek = rezultat[1] if rezultat else "N/A"
    
    if istek != "forever" and istek != "N/A" and istek:
        try:
            istek_datum = datetime.strptime(istek, "%Y-%m-%d %H:%M:%S")
            preostanato = istek_datum - datetime.now()
            if preostanato.days > 0:
                istek = f"{preostanato.days} дена"
            else:
                istek = "🔴 ИСТЕКНА"
        except:
            pass
    
    menu_text = f"""<b>🎮 GAME GUARDIAN - CAR PARKING</b>

👤 <b>Корисник:</b> @{username}
🆔 <b>ID:</b> {user_id}
📅 <b>Лиценца:</b> {istek}

<b>⚡ ИЗБЕРИ ФУНКЦИЈА:</b>"""

    keyboard = [
        [
            InlineKeyboardButton("🔊 W16", callback_data="gg_w16"),
            InlineKeyboardButton("📯 Horns", callback_data="gg_horns")
        ],
        [
            InlineKeyboardButton("🛡️ No Dmg", callback_data="gg_nodmg"),
            InlineKeyboardButton("⛽ Fuel", callback_data="gg_fuel")
        ],
        [
            InlineKeyboardButton("💨 Smoke", callback_data="gg_smoke"),
            InlineKeyboardButton("🎭 Animations", callback_data="gg_animations")
        ],
        [
            InlineKeyboardButton("⚙️ Wheels", callback_data="gg_wheels"),
            InlineKeyboardButton("🏠 Houses", callback_data="gg_houses")
        ],
        [
            InlineKeyboardButton("📈 Levels", callback_data="gg_levels"),
            InlineKeyboardButton("👑 Rank", callback_data="gg_rank")
        ],
        [
            InlineKeyboardButton("🌟 UNLOCK ALL ★", callback_data="gg_unlock_all")
        ],
        [
            InlineKeyboardButton("💵 ДОБИЈ ПАРИ", callback_data="gg_money")
        ]
    ]
    
    if query:
        await query.edit_message_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        await query.answer()
    else:
        await update.message.reply_text(
            menu_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# ========== GG HANDLERS ==========
async def gg_funkcija(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    funkcija = query.data.replace('gg_', '')
    
    # ПРОВЕРКА
    validna, poraka = proveri_licenca(user_id)
    if not validna:
        await query.edit_message_text(
            f"❌ **Немате активна лиценца!**\n\n{poraka}",
            parse_mode='Markdown'
        )
        return
    
    funkcii = {
        'w16': 'W16 Motor', 'horns': 'Хорни', 'nodmg': 'Без Штета',
        'fuel': 'Бесконечно Гориво', 'smoke': 'Чад', 'animations': 'Анимации',
        'wheels': 'Тркала', 'houses': 'Куќи', 'levels': 'Нивоа',
        'rank': 'Ранг', 'unlock_all': 'СЕ ОТКЛУЧУВА', 'money': 'ПАРИ'
    }
    
    ime = funkcii.get(funkcija, funkcija)
    
    if funkcija == 'unlock_all':
        skripta = generiraj_gg_skripta('UnlockAll', user_id)
    elif funkcija == 'money':
        skripta = generiraj_gg_skripta('PARI', user_id)
    else:
        skripta = generiraj_gg_skripta(funkcija.capitalize(), user_id)
    
    await query.edit_message_text(
        f"""<b>🎮 {ime} - GG СКРИПТА</b>

📝 <b>Копирај:</b>

<code>{skripta}</code>

📌 <b>Инструкции:</b>
1. Отвори Game Guardian
2. Избери Car Parking
3. Кликни 📜 за скрипти
4. Paste - Вметни
5. Run - Изврши""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="gg_menu")]
        ]),
        parse_mode='HTML'
    )

# ========== АДМИН ПАНЕЛ ==========
async def prikazi_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM korisnici')
    vkupno = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "approved"')
    aktivni = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status = "pending"')
    baranja = cursor.fetchone()[0]
    
    conn.close()
    
    admin_text = f"""<b>👑 АДМИН ПАНЕЛ</b>

📊 <b>Статистика:</b>
• Вкупно: {vkupno}
• Активни: {aktivni}
• Барања: {baranja}

📌 <b>Опции:</b>"""

    keyboard = [
        [InlineKeyboardButton("📋 Корисници", callback_data="admin_users")],
        [InlineKeyboardButton("❌ Бриши Корисник", callback_data="admin_remove")],
        [InlineKeyboardButton("💵 Барања за Пари", callback_data="admin_money_requests")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🔧 Поправи Корисник", callback_data="admin_fix_user")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# ========== АДМИН - ПОПРАВИ КОРИСНИК ==========
async def admin_fix_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поправа корисник кој има проблем со лиценцата"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔧 **ПОПРАВИ КОРИСНИК**\n\n"
        "Внесете го ID на корисникот што сакате да го поправите:\n\n"
        "Пример: `8793457956`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
    )
    return ADMIN_ODOBRI_LICENCA

async def primi_fix_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Внесете валиден ID!")
        return ADMIN_ODOBRI_LICENCA
    
    # ПРОВЕРИ ДАЛИ КОРИСНИКОТ ПОСТОИ
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status, istekuvanje FROM korisnici WHERE user_id = ?', (user_id,))
    rezultat = cursor.fetchone()
    
    if not rezultat:
        await update.message.reply_text(f"❌ Корисникот {user_id} не постои!")
        conn.close()
        return ADMIN_ODOBRI_LICENCA
    
    status, istekuvanje = rezultat
    
    # ПОПРАВИ - СТАВИ APPROVED
    if istekuvanje and istekuvanje != "forever":
        try:
            istek_datum = datetime.strptime(istekuvanje, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > istek_datum:
                # ДОДАЈ 7 ДЕНА
                novo_istekuvanje = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    UPDATE korisnici 
                    SET status = 'approved', istekuvanje = ? 
                    WHERE user_id = ?
                ''', (novo_istekuvanje, user_id))
                conn.commit()
                conn.close()
                
                await update.message.reply_text(
                    f"✅ **Корисникот {user_id} е поправен!**\n"
                    f"📅 Нова лиценца: 7 дена"
                )
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ **Вашата лиценца е обновена!** 🎉\n\n"
                         "📅 Времетраење: 7 дена\n"
                         "🔑 Напишете /start за да почнете.",
                    parse_mode='Markdown'
                )
                await prikazi_admin_panel(update)
                return ADMIN_MENU
        except:
            pass
    
    # АКО НЕМА ЛИЦЕНЦА - ДОДЕЛИ
    novo_istekuvanje = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        UPDATE korisnici 
        SET status = 'approved', istekuvanje = ? 
        WHERE user_id = ?
    ''', (novo_istekuvanje, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ **Корисникот {user_id} е поправен!**\n"
        f"📅 Доделена лиценца: 7 дена"
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text="✅ **ДОБИВТЕ ПРИСТАП!** 🎉\n\n"
             "📅 Времетраење: 7 дена\n"
             "🔑 Напишете /start за да почнете.",
        parse_mode='Markdown'
    )
    
    await prikazi_admin_panel(update)
    return ADMIN_MENU

# ========== АДМИН - КОРИСНИЦИ ==========
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, first_name, status, istekuvanje FROM korisnici ORDER BY user_id')
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await query.edit_message_text(
            "📋 Нема корисници.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
            ])
        )
        return
    
    tekst = "<b>📋 КОРИСНИЦИ:</b>\n\n"
    for user in users[:20]:
        status_emoji = "✅" if user[3] == "approved" else "⏳" if user[3] == "pending" else "❌"
        istek = user[4] if user[4] else "Нема"
        if istek != "forever" and istek != "Нема":
            try:
                istek_datum = datetime.strptime(istek, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > istek_datum:
                    istek = "🔴 ИСТЕКНА"
                else:
                    preostanato = istek_datum - datetime.now()
                    istek = f"{preostanato.days} дена"
            except:
                pass
        tekst += f"{status_emoji} 🆔 {user[0]} | @{user[1] or 'N/A'}\n"
        tekst += f"   Статус: {user[3]} | {istek}\n\n"
    
    await query.edit_message_text(
        tekst,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
    )

# ========== АДМИН - БРИШИ ==========
async def admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ **БРИШИ КОРИСНИК**\n\n"
        "Внесете го ID:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
    )
    return CEKA_BRISI_ID

async def primi_id_za_brisenje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Внесете валиден ID!")
        return CEKA_BRISI_ID
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM korisnici WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        await update.message.reply_text(f"❌ Корисникот {user_id} не постои!")
        conn.close()
        return CEKA_BRISI_ID
    
    cursor.execute('DELETE FROM korisnici WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM baranja_za_pari WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Корисникот {user_id} е избришан!")
    await prikazi_admin_panel(update)
    return ADMIN_MENU

# ========== АДМИН - СТАТИСТИКА ==========
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM korisnici')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status="approved"')
    active = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM korisnici WHERE status="pending"')
    pending = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM baranja_za_pari WHERE status="pending"')
    money = cursor.fetchone()[0]
    conn.close()
    
    await query.edit_message_text(
        f"""<b>📊 СТАТИСТИКА</b>

👥 Вкупно: {total}
✅ Активни: {active}
⏳ Чекаат: {pending}
💵 Барања за пари: {money}
📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}""",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
    )

# ========== АДМИН - БАРАЊА ЗА ПАРИ ==========
async def admin_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, username, iznos, datum FROM baranja_za_pari WHERE status="pending" ORDER BY id DESC')
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        await query.edit_message_text(
            "💵 Нема барања.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
            ])
        )
        return
    
    tekst = "<b>💵 БАРАЊА ЗА ПАРИ</b>\n\n"
    for req in requests[:10]:
        tekst += f"🆔 {req[1]} | @{req[2] or 'N/A'}\n"
        tekst += f"💰 {req[3]} | 📅 {req[4]}\n\n"
    
    await query.edit_message_text(
        tekst,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Освежи", callback_data="admin_money_requests")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
    )

# ========== LICENCA HANDLER ==========
async def licenca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    akcija = data[1]
    user_id = int(data[2])
    
    logger.info(f"📝 Лиценца: {akcija} за {user_id}")
    
    if akcija == "custom":
        context.user_data['custom_user_id'] = user_id
        await query.edit_message_text(
            f"📝 **Внесете број на денови (1-30)**\n\n"
            f"Корисник ID: `{user_id}`",
            parse_mode='Markdown'
        )
        return CEKA_CUSTOM_DAYS
    
    if akcija == "deny":
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE korisnici SET status = "denied" WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"❌ Корисникот {user_id} е одбиен.")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ **Вашето барање е одбиено!**",
            parse_mode='Markdown'
        )
        return
    
    # ОДОБРИ
    if akcija == "forever":
        istekuvanje = "forever"
        opis = "Forever ♾️"
    else:
        istekuvanje = (datetime.now() + timedelta(days=int(akcija))).strftime("%Y-%m-%d %H:%M:%S")
        opis = f"{akcija} дена"
    
    conn = sqlite3.connect('licenci.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE korisnici 
        SET istekuvanje = ?, status = "approved", datum_dodeluvanje = ? 
        WHERE user_id = ?
    ''', (istekuvanje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(f"✅ **Одобрен!**\n📅 {opis}")
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ **ДОБИВТЕ ПРИСТАП!** 🎉\n\n"
                 f"📅 Времетраење: {opis}\n"
                 f"📆 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                 f"🔑 Напишете /start",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Грешка: {e}")

async def primi_custom_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text.strip())
        if days < 1 or days > 30:
            await update.message.reply_text("❌ 1-30.")
            return CEKA_CUSTOM_DAYS
        
        user_id = context.user_data.get('custom_user_id')
        if not user_id:
            await update.message.reply_text("❌ Грешка!")
            return
        
        istekuvanje = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect('licenci.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE korisn
