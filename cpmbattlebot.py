import asyncio
import logging
import os
import random
import threading
from datetime import datetime, timezone
from html import escape

from flask import Flask
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery, ChatJoinRequest
)

# ==========================================
# KONFIGURATSIYA (RENDER VA ENVIRONMENT)
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8734592942:AAFeKV1VP5F6hCxM4cIuQZUOYvD3298yOPI")
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://cpmcpmbattle_db_user:lKQN2ePocUCIM9zi@cluster0.brsfu0p.mongodb.net/?appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "konkurs_bot_db")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6968399046"))
PORT = int(os.getenv("PORT", 8080))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("contest-bot")

# ==========================================
# FLASK SERVER (Render Web Service Uptime uchun)
# ==========================================
app = Flask(__name__)

@app.get("/")
def health_check():
    return "Bot is running 24/7!", 200

def run_web():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)

# ==========================================
# MONGODB VA AIOGRAM INIT
# ==========================================
mongo = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=10000)
db = mongo[DB_NAME]
users_col = db.users
contests_col = db.contests
channels_col = db.channels
join_requests_col = db.join_requests
prizes_col = db.prizes

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==========================================
# MATNLAR (UZ, RU, EN)
# ==========================================
TEXTS = {
    "uz": {
        "choose": "Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺",
        "welcome": "Xush kelibsiz! Kerakli bo'limni tanlang:",
        "prizes_btn": "| MEN YUTGAN SOVRINLAR 🛒|",
        "lang_btn": "| TIL ALMASHTIRISH 🌐 |",
        "create_btn": "| KONKURS YARATISH 🛒 |",
        "stats_btn": "| BOT STATISTIKASI📊 |",
        "subs_btn": "| MAJBURIY OBUNA ULASH 📣 |",
        "select_type": "Qaysi turdagi konkurs qilasiz tanlang 🌟",
        "account": "👉🏻 AKKAUNTLI",
        "other": "👉🏻 BOSHQA",
        "ask_prizes": "Nechta akkaunt qoʻyamiz?\nYozing📦\n(Faqat son koʻrinishida)",
        "ask_accounts": "Akkauntlarni quyidagi formatda yuboring🔖:\n\n<code>01 | email | parol | OK</code>\n<code>02 | email | parol | OK</code>",
        "ask_custom": "Konkursga nima yutuqlar qoʻyiladi yozing🎁\n(Masalan:\n1🥇- 30K COIN\n2🥈- 500K COIN\n3🥉- CHANGE ID)",
        "ask_winners": "Nechta odam gʻolib boʻladi yozing ⚡\n(Faqat son koʻrinishida)",
        "ask_limit": "Nechta odam qatnasha oladi yozing 🌟\n(Faqat son koʻrinishida)",
        "pick_channel": "Konkurs qilinadigan kanalni tanlang:",
        "started": "Konkurs boshlandi 📣\n\nYutuqlar🎁:\n{prizes}\nTugashi: {current}/{limit}\n\nQatnashish uchun pastdagi tugmani bosing!",
        "started_en": "The contest has started 📣\n\nPrizes 🎁:\n{prizes}\nEnds: {current}/{limit}\n\nClick the button GOO 👇",
        "goo": "GOO 🎁",
        "subscribe": "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
        "check": "✅ Tekshirish",
        "joined": "Siz muvaffaqiyatli qatnashdingiz✅",
        "already": "Siz allaqachon ushbu konkursda qatnashmoqdasiz!",
        "finished_uz": "🏁 <b>KOʻNKURS YAKUNLANDI</b>\n\n{winners}",
        "finished_en": "🏁 <b>CONTEST FINISHED</b>\n\n{winners}",
        "won_notify": "🎉 Tabriklaymiz! Siz yutdingiz:\n{prize}\n\n✨Yutuqni olish uchun \n@cpm_java ga yozing 🎁",
        "no_prizes": "Sizda hali yutib olingan sovrinlar yo'q 🛒",
        "my_prizes": "🛒 Siz yutgan sovrinlar:\n\n",
        "channels_menu": "Majburiy obuna boshqaruvi bo'limi:",
        "add": "➕ Kanal/Guruh qo'shish",
        "remove": "➖ Majburiy obunani olib tashlash",
        "choose_sub": "Qaysi turdagi kanal/guruh qo'shmoqchisiz?",
        "channel": "ODDIY KANAL📣",
        "group": "CHAT GURUH ✉️",
        "request": "ZAYAFKA KANAL📦",
        "ask_channel": "Kanal username yoki havolasini yuboring (Masalan: @kanal yoki https://t.me/kanal):\n<i>Bot kanalga admin bo'lishi shart!</i>",
        "ask_group": "Guruh username yoki havolasini yuboring:\n<i>Bot guruhda admin bo'lishi shart!</i>",
        "ask_request": "Zayafka (Join Request) kanal username yoki havolasini yuboring:\n<i>Bot ushbu kanalda admin bo'lishi shart!</i>",
        "added": "✅ Muvaffaqiyatli qo'shildi!",
        "removed": "🗑 Majburiy obuna olib tashlandi!",
        "none": "Hali hech qanday majburiy obuna qo'shilmagan.",
        "bad_number": "Xatolik! Iltimos, faqat musbat son kiriting.",
        "count_mismatch": "Akkauntlar soni kam. Kamida {n} ta akkaunt yuboring:",
        "stats": "📊 <b>Bot Statistikasi:</b>\n\n👤 Jami foydalanuvchilar: {users}\n🛒 O'tkazilgan konkurslar: {contests}"
    },
    "ru": {
        "choose": "Выберите язык 🇺🇿 / 🇺🇸 / 🇷🇺",
        "welcome": "Добро пожаловать! Выберите нужный раздел:",
        "prizes_btn": "| МОИ ПРИЗЫ 🛒|",
        "lang_btn": "| СМЕНА ЯЗЫКА 🌐 |",
        "create_btn": "| СОЗДАТЬ КОНКУРС 🛒 |",
        "stats_btn": "| СТАТИСТИКА БОТА 📊 |",
        "subs_btn": "| ОБЯЗАТЕЛЬНАЯ ПОДПИСКА 📣 |",
        "select_type": "Выберите тип конкурса 🌟",
        "account": "👉🏻 АККАУНТЫ",
        "other": "👉🏻 ДРУГОЕ",
        "ask_prizes": "Сколько аккаунтов разыгрываем?\n(Только число)",
        "ask_accounts": "Отправьте аккаунты в формате🔖:\n\n<code>01 | email | пароль | OK</code>\n<code>02 | email | пароль | OK</code>",
        "ask_custom": "Напишите призы конкурса 🎁:",
        "ask_winners": "Сколько человек выиграет ⚡:\n(Только число)",
        "ask_limit": "Сколько человек может участвовать 🌟:\n(Только число)",
        "pick_channel": "Выберите канал для конкурса:",
        "started": "Конкурс начался 📣\n\nПризы🎁:\n{prizes}\nЗавершение: {current}/{limit}\n\nНажмите кнопку ниже для участия!",
        "started_en": "The contest has started 📣\n\nPrizes 🎁:\n{prizes}\nEnds: {current}/{limit}\n\nClick the button GOO 👇",
        "goo": "GOO 🎁",
        "subscribe": "Для использования бота подпишитесь на каналы:",
        "check": "✅ Проверить",
        "joined": "Вы успешно участвовали✅",
        "already": "Вы уже участвуете в этом конкурсе!",
        "finished_uz": "🏁 <b>KOʻNKURS YAKUNLANDI</b>\n\n{winners}",
        "finished_en": "🏁 <b>CONTEST FINISHED</b>\n\n{winners}",
        "won_notify": "🎉 Поздравляем! Ваш выигрыш:\n{prize}\n\n✨Для получения приза\nнапишите @cpm_java 🎁",
        "no_prizes": "У вас пока нет выигранных призов 🛒",
        "my_prizes": "🛒 Ваши выигранные призы:\n\n",
        "channels_menu": "Управление обязательной подпиской:",
        "add": "➕ Добавить канал/группу",
        "remove": "➖ Удалить обязательную подписку",
        "choose_sub": "Какой тип подписки добавить?",
        "channel": "ОБЫЧНЫЙ КАНАЛ📣",
        "group": "ЧАТ ГРУППА ✉️",
        "request": "ЗАЯВКА КАНАЛ📦",
        "ask_channel": "Отправьте username или ссылку на канал:",
        "ask_group": "Отправьте username или ссылку на группу:",
        "ask_request": "Отправьте ссылку на Join Request канал:",
        "added": "✅ Успешно добавлено!",
        "removed": "🗑 Обязательная подписка удалена!",
        "none": "Список обязательных подписок пуст.",
        "bad_number": "Ошибка! Введите только положительное число.",
        "count_mismatch": "Количество аккаунтов меньше указанного ({n} шт.).",
        "stats": "📊 <b>Статистика бота:</b>\n\n👤 Пользователей: {users}\n🛒 Конкурсов: {contests}"
    },
    "en": {
        "choose": "Choose a language 🇺🇿 / 🇺🇸 / 🇷🇺",
        "welcome": "Welcome! Select an option below:",
        "prizes_btn": "| MY PRIZES 🛒|",
        "lang_btn": "| CHANGE LANGUAGE 🌐 |",
        "create_btn": "| CREATE CONTEST 🛒 |",
        "stats_btn": "| BOT STATS 📊 |",
        "subs_btn": "| MANDATORY SUBS 📣 |",
        "select_type": "Select contest type 🌟",
        "account": "👉🏻 ACCOUNTS",
        "other": "👉🏻 OTHER",
        "ask_prizes": "How many accounts to giveaway?\n(Numbers only)",
        "ask_accounts": "Send accounts in format🔖:\n\n<code>01 | email | password | OK</code>\n<code>02 | email | password | OK</code>",
        "ask_custom": "Write custom prizes 🎁:",
        "ask_winners": "How many winners ⚡:\n(Numbers only)",
        "ask_limit": "How many participants can join 🌟:\n(Numbers only)",
        "pick_channel": "Select contest channel:",
        "started": "Contest started 📣\n\nPrizes 🎁:\n{prizes}\nEnds: {current}/{limit}\n\nClick the button below to join!",
        "started_en": "The contest has started 📣\n\nPrizes 🎁:\n{prizes}\nEnds: {current}/{limit}\n\nClick the button GOO 👇",
        "goo": "GOO 🎁",
        "subscribe": "Subscribe to channels to use the bot:",
        "check": "✅ Check",
        "joined": "You joined successfully✅",
        "already": "You are already participating!",
        "finished_uz": "🏁 <b>KOʻNKURS YAKUNLANDI</b>\n\n{winners}",
        "finished_en": "🏁 <b>CONTEST FINISHED</b>\n\n{winners}",
        "won_notify": "🎉 Congratulations! Your prize:\n{prize}\n\n✨To claim your prize,\nmessage @cpm_java 🎁",
        "no_prizes": "You haven't won any prizes yet 🛒",
        "my_prizes": "🛒 Your prizes:\n\n",
        "channels_menu": "Mandatory Subscription Management:",
        "add": "➕ Add Channel/Group",
        "remove": "➖ Remove Subscription",
        "choose_sub": "Select subscription type:",
        "channel": "REGULAR CHANNEL📣",
        "group": "CHAT GROUP ✉️",
        "request": "REQUEST CHANNEL📦",
        "ask_channel": "Send channel username or link:",
        "ask_group": "Send group username or link:",
        "ask_request": "Send join request channel username or link:",
        "added": "✅ Successfully added!",
        "removed": "🗑 Subscription removed!",
        "none": "No mandatory subscriptions added yet.",
        "bad_number": "Error! Please enter a positive number.",
        "count_mismatch": "Number of accounts doesn't match ({n}).",
        "stats": "📊 <b>Bot Stats:</b>\n\n👤 Total Users: {users}\n🛒 Contests: {contests}"
    }
}

# ==========================================
# FSM STATES
# ==========================================
class ContestFlow(StatesGroup):
    kind = State()
    custom_prizes = State()
    winners = State()
    account_count = State()
    limit = State()
    accounts = State()
    channel = State()

class SubFlow(StatesGroup):
    link = State()

LANG_BUTTONS = [t["lang_btn"] for t in TEXTS.values()]
PRIZE_BUTTONS = [t["prizes_btn"] for t in TEXTS.values()]
CREATE_BUTTONS = [t["create_btn"] for t in TEXTS.values()]
STAT_BUTTONS = [t["stats_btn"] for t in TEXTS.values()]
SUB_BUTTONS = [t["subs_btn"] for t in TEXTS.values()]

# ==========================================
# YORDAMCHI FUNKSIYALAR
# ==========================================
async def get_lang(uid: int):
    try:
        doc = await users_col.find_one({"user_id": uid})
        if doc and doc.get("lang") in TEXTS:
            return doc["lang"]
    except Exception:
        pass
    return None

def main_keyboard(uid: int, lang: str):
    t = TEXTS[lang]
    rows = [
        [KeyboardButton(text=t["prizes_btn"])],
        [KeyboardButton(text=t["lang_btn"])]
    ]
    if uid == ADMIN_ID:
        rows.append([KeyboardButton(text=t["create_btn"])])
        rows.append([KeyboardButton(text=t["stats_btn"]), KeyboardButton(text=t["subs_btn"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
    ]])

def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "https://t.me"
    if value.startswith(("https://", "http://")):
        return value
    if value.startswith("@"):
        return "https://t.me/" + value[1:]
    if value.startswith("t.me/"):
        return "https://" + value
    return "https://t.me/" + value

async def subscription_keyboard(lang: str, contest_id: str = None):
    docs = await channels_col.find().to_list(100)
    rows = []
    for ch in docs:
        if ch.get("url"):
            rows.append([InlineKeyboardButton(text="📣 " + ch.get("title", "Kanal"), url=normalize_url(ch["url"]))])
    cb = "checksub:" + (contest_id or "home")
    rows.append([InlineKeyboardButton(text=TEXTS[lang]["check"], callback_data=cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def check_subscriptions(uid: int) -> bool:
    try:
        channels_list = await channels_col.find().to_list(200)
        if not channels_list:
            return True
        for ch in channels_list:
            kind = ch.get("type", "channel")
            chat_id = ch.get("chat_id")
            if kind in ("channel", "group") and chat_id:
                try:
                    member = await bot.get_chat_member(int(chat_id), uid)
                    if member.status in ("left", "kicked"):
                        return False
                except Exception:
                    pass
            elif kind == "request":
                if chat_id:
                    req = await join_requests_col.find_one({"user_id": uid, "chat_id": int(chat_id)})
                    if not req:
                        return False
                else:
                    req = await join_requests_col.find_one({"user_id": uid})
                    if not req:
                        return False
        return True
    except Exception as e:
        log.error(f"Subscription check error: {e}")
        return True

async def send_home(message: types.Message, uid: int, lang: str):
    await message.answer(TEXTS[lang]["welcome"], reply_markup=main_keyboard(uid, lang))

# ==========================================
# /START VA TIL TANLASH
# ==========================================
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    uid = message.from_user.id
    args = (message.text or "").split(maxsplit=1)
    contest_id = args[1][8:] if len(args) > 1 and args[1].startswith("contest_") else None

    await users_col.update_one(
        {"user_id": uid},
        {"$set": {
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )

    lang = await get_lang(uid)
    if not lang:
        if contest_id:
            await users_col.update_one({"user_id": uid}, {"$set": {"pending_contest_id": contest_id}})
        await message.answer(TEXTS["uz"]["choose"], reply_markup=language_keyboard())
        return

    if not await check_subscriptions(uid):
        await message.answer(TEXTS[lang]["subscribe"], reply_markup=await subscription_keyboard(lang, contest_id))
        return

    if contest_id:
        await join_contest(uid, contest_id, message)
    else:
        await send_home(message, uid, lang)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language_callback(call: CallbackQuery):
    lang = call.data[5:]
    if lang not in TEXTS:
        await call.answer("Error", show_alert=True)
        return

    uid = call.from_user.id
    old = await users_col.find_one({"user_id": uid})
    pending = old.get("pending_contest_id") if old else None

    await users_col.update_one(
        {"user_id": uid},
        {"$set": {"lang": lang, "updated_at": datetime.now(timezone.utc)}, "$unset": {"pending_contest_id": ""}},
        upsert=True
    )

    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass

    if not await check_subscriptions(uid):
        await call.message.answer(TEXTS[lang]["subscribe"], reply_markup=await subscription_keyboard(lang, pending))
    elif pending:
        await join_contest(uid, pending, call.message)
    else:
        await send_home(call.message, uid, lang)

@dp.callback_query(F.data.startswith("checksub:"))
async def check_sub_callback(call: CallbackQuery):
    uid = call.from_user.id
    lang = await get_lang(uid) or "uz"

    if not await check_subscriptions(uid):
        err_txt = "Barcha kanallarga a'zo bo'ling! ❌" if lang == "uz" else ("Подпишитесь на все каналы! ❌" if lang == "ru" else "Subscribe to all channels! ❌")
        await call.answer(err_txt, show_alert=True)
        return

    payload = call.data.split(":", 1)[1]
    try:
        await call.message.delete()
    except Exception:
        pass

    if payload != "home":
        await join_contest(uid, payload, call.message)
    else:
        await send_home(call.message, uid, lang)

@dp.message(F.text.in_(LANG_BUTTONS))
async def change_language_menu(message: types.Message):
    await message.answer("Tilni tanlang 🇺🇿 / 🇺🇸 / 🇷🇺", reply_markup=language_keyboard())

# ==========================================
# SOVRINLAR MENYUSI
# ==========================================
@dp.message(F.text.in_(PRIZE_BUTTONS))
async def show_prizes_menu(message: types.Message):
    lang = await get_lang(message.from_user.id) or "uz"
    docs = await prizes_col.find({"user_id": message.from_user.id}).to_list(100)
    if not docs:
        await message.answer(TEXTS[lang]["no_prizes"])
        return
    text = TEXTS[lang]["my_prizes"] + "\n".join(f"{i}. <code>{escape(p.get('account', 'Sovrin'))}</code>" for i, p in enumerate(docs, 1))
    await message.answer(text, parse_mode="HTML")

# ==========================================
# ADMIN: KONKURS YARATISH
# ==========================================
@dp.message(F.text.in_(CREATE_BUTTONS))
async def create_contest_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    lang = await get_lang(message.from_user.id) or "uz"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=TEXTS[lang]["account"], callback_data="kind:account"),
        InlineKeyboardButton(text=TEXTS[lang]["other"], callback_data="kind:other")
    ]])
    await message.answer(TEXTS[lang]["select_type"], reply_markup=kb)
    await state.set_state(ContestFlow.kind)

@dp.callback_query(F.data.startswith("kind:"), ContestFlow.kind)
async def choose_kind(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":", 1)[1]
    admin_lang = await get_lang(call.from_user.id) or "uz"
    await state.update_data(kind=kind, admin_lang=admin_lang)
    t = TEXTS[admin_lang]

    if kind == "account":
        await call.message.edit_text(t["ask_prizes"])
        await state.set_state(ContestFlow.account_count)
    else:
        await call.message.edit_text(t["ask_custom"])
        await state.set_state(ContestFlow.custom_prizes)
    await call.answer()

@dp.message(ContestFlow.custom_prizes)
async def custom_prizes_step(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Yutuq matnini yuboring.")
        return
    prize_lines = [line.strip() for line in text.splitlines() if line.strip()]
    await state.update_data(custom_prizes=text, prize_lines=prize_lines)
    t = TEXTS[await get_lang(message.from_user.id) or "uz"]
    await message.answer(t["ask_winners"])
    await state.set_state(ContestFlow.winners)

@dp.message(ContestFlow.winners)
async def winners_count_step(message: types.Message, state: FSMContext):
    lang = await get_lang(message.from_user.id) or "uz"
    if not (message.text or "").isdigit() or int(message.text) < 1:
        await message.answer(TEXTS[lang]["bad_number"])
        return
    await state.update_data(winners_count=int(message.text), prize_count=int(message.text))
    await message.answer(TEXTS[lang]["ask_limit"])
    await state.set_state(ContestFlow.limit)

@dp.message(ContestFlow.account_count)
async def account_count_step(message: types.Message, state: FSMContext):
    lang = await get_lang(message.from_user.id) or "uz"
    if not (message.text or "").isdigit() or int(message.text) < 1:
        await message.answer(TEXTS[lang]["bad_number"])
        return
    await state.update_data(prize_count=int(message.text), winners_count=int(message.text))
    await message.answer(TEXTS[lang]["ask_limit"])
    await state.set_state(ContestFlow.limit)

@dp.message(ContestFlow.limit)
async def limit_step(message: types.Message, state: FSMContext):
    lang = await get_lang(message.from_user.id) or "uz"
    if not (message.text or "").isdigit() or int(message.text) < 1:
        await message.answer(TEXTS[lang]["bad_number"])
        return
    await state.update_data(max_users=int(message.text))
    data = await state.get_data()

    if data["kind"] == "account":
        await message.answer(TEXTS[lang]["ask_accounts"], parse_mode="HTML")
        await state.set_state(ContestFlow.accounts)
    else:
        await choose_publish_channel(message, state)

@dp.message(ContestFlow.accounts)
async def accounts_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lines = [line.strip() for line in (message.text or "").splitlines() if line.strip()]
    if len(lines) < data["prize_count"]:
        t = TEXTS[await get_lang(message.from_user.id) or "uz"]
        await message.answer(t["count_mismatch"].format(n=data["prize_count"]))
        return
    await state.update_data(accounts=lines, prize_lines=lines)
    await choose_publish_channel(message, state)

async def choose_publish_channel(message: types.Message, state: FSMContext):
    docs = await channels_col.find({"type": "channel"}).to_list(100)
    valid_channels = [d for d in docs if d.get("chat_id")]
    if not valid_channels:
        await message.answer("⚠️ Avval 'MAJBURIY OBUNA ULASH' bo'limidan 'ODDIY KANAL' qo'shing va botni kanalga admin qiling.")
        await state.clear()
        return
    rows = []
    for d in valid_channels:
        cid = d["chat_id"]
        rows.append([InlineKeyboardButton(text=d.get("title", "Kanal")[:50], callback_data=f"pub:{cid}")])
    t = TEXTS[await get_lang(message.from_user.id) or "uz"]
    await message.answer(t["pick_channel"], reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await state.set_state(ContestFlow.channel)

@dp.callback_query(F.data.startswith("pub:"), ContestFlow.channel)
async def publish_contest(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Faqat admin uchun", show_alert=True)
        return
    data = await state.get_data()
    try:
        chat_id = int(call.data.split(":", 1)[1])
    except Exception:
        await call.answer("Xato kanal", show_alert=True)
        return

    kind = data["kind"]
    if kind == "account":
        prize_lines = data["accounts"]
        prize_text = f"{data['prize_count']}ta akkaunt"
    else:
        prize_lines = data["prize_lines"]
        prize_text = data["custom_prizes"]

    doc = {
        "kind": kind,
        "prize_count": data["prize_count"],
        "prize_lines": prize_lines,
        "prize_text": prize_text,
        "max_users": data["max_users"],
        "current": 0,
        "participants": [],
        "status": "active",
        "chat_id": chat_id,
        "created_at": datetime.now(timezone.utc)
    }
    result = await contests_col.insert_one(doc)
    cid = str(result.inserted_id)
    me = await bot.get_me()

    markup = contest_markup(me.username, cid)
    body = contest_post(doc, 0)

    try:
        sent = await bot.send_message(chat_id, body, parse_mode="HTML", reply_markup=markup)
        await contests_col.update_one({"_id": result.inserted_id}, {"$set": {"message_id": sent.message_id}})
        await call.message.edit_text("✅ Konkurs kanalga muvaffaqiyatli joylandi!")
    except Exception as exc:
        await contests_col.delete_one({"_id": result.inserted_id})
        await call.message.edit_text(f"❌ Postni yuborib bo'lmadi: {escape(str(exc))}")

    await call.answer()
    await state.clear()

def contest_markup(username: str, cid: str):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="GOO 🎁", url=f"https://t.me/{username}?start=contest_{cid}")
    ]])

def contest_post(c: dict, current: int) -> str:
    prize = escape(c.get("prize_text", ""))
    uz = TEXTS["uz"]["started"].format(prizes=prize, current=current, limit=c["max_users"])
    en = TEXTS["en"]["started_en"].format(prizes=prize, current=current, limit=c["max_users"])
    return f"{uz}\n\n<blockquote><i>{en}</i></blockquote>"

# ==========================================
# KONKURSGA QATNASHISH VA YAKUNLASH
# ==========================================
async def join_contest(uid: int, cid_text: str, message: types.Message):
    lang = await get_lang(uid) or "uz"
    try:
        oid = ObjectId(cid_text)
    except Exception:
        await message.answer("⚠️ Noto'g'ri konkurs havolasi.", reply_markup=main_keyboard(uid, lang))
        return

    if not await check_subscriptions(uid):
        await message.answer(TEXTS[lang]["subscribe"], reply_markup=await subscription_keyboard(lang, cid_text))
        return

    res = await contests_col.update_one(
        {"_id": oid, "status": "active", "participants": {"$ne": uid}, "$expr": {"$lt": ["$current", "$max_users"]}},
        {"$addToSet": {"participants": uid}, "$inc": {"current": 1}}
    )

    if res.modified_count == 0:
        c = await contests_col.find_one({"_id": oid})
        if not c or c.get("status") != "active":
            await message.answer("⚠️ Bu konkurs yakunlangan yoki mavjud emas.", reply_markup=main_keyboard(uid, lang))
            return
        if uid in c.get("participants", []):
            await message.answer(TEXTS[lang]["already"], reply_markup=main_keyboard(uid, lang))
            return
        await message.answer("⚠️ Konkursda qatnashchilar soni to'lgan.", reply_markup=main_keyboard(uid, lang))
        return

    c = await contests_col.find_one({"_id": oid})
    await message.answer(TEXTS[lang]["joined"], reply_markup=main_keyboard(uid, lang))

    # Kanal postini yangilash
    try:
        me = await bot.get_me()
        await bot.edit_message_text(
            chat_id=c["chat_id"],
            message_id=c["message_id"],
            text=contest_post(c, c["current"]),
            parse_mode="HTML",
            reply_markup=contest_markup(me.username, cid_text)
        )
    except Exception:
        pass

    if c["current"] >= c["max_users"]:
        await finish_contest(oid)

async def finish_contest(oid: ObjectId):
    claim = await contests_col.update_one(
        {"_id": oid, "status": "active"},
        {"$set": {"status": "drawing"}}
    )
    if claim.modified_count == 0:
        return

    c = await contests_col.find_one({"_id": oid})
    participants = c.get("participants", [])
    prize_lines = c.get("prize_lines", [])
    prize_count = c.get("prize_count", len(prize_lines))

    count = min(len(participants), prize_count)
    winners = random.sample(participants, count) if count else []

    rows = []
    medals = ["1️⃣ OʻRIN🥇", "2️⃣ OʻRIN🥈", "3️⃣ OʻRIN🥉", "4️⃣ OʻRIN🏆", "5️⃣ OʻRIN🏆", "6️⃣ OʻRIN🏆", "7️⃣ OʻRIN🏆", "8️⃣ OʻRIN🏆", "9️⃣ OʻRIN🏆", "🔟 OʻRIN🏆"]

    for index, uid in enumerate(winners):
        user = await users_col.find_one({"user_id": uid}) or {}
        uname = user.get("username")
        fname = user.get("first_name")
        display = f"@{uname}" if uname else escape(fname or f"ID: {uid}")

        label = medals[index] if index < len(medals) else f"{index+1}-OʻRIN🏆"
        rows.append(f"{label} - {display}")

        prize_item = prize_lines[index] if index < len(prize_lines) else f"Sovrin #{index+1}"

        if c.get("kind") == "account":
            await prizes_col.insert_one({
                "user_id": uid,
                "contest_id": str(oid),
                "account": prize_item,
                "created_at": datetime.now(timezone.utc)
            })

        u_lang = await get_lang(uid) or "uz"
        t = TEXTS[u_lang]
        msg_text = t["won_notify"].format(prize=escape(prize_item))

        try:
            await bot.send_message(uid, msg_text, parse_mode="HTML")
        except Exception:
            pass

    winners_list_str = "\n".join(rows) if rows else "Gʻolib aniqlanmadi."
    uz_final = TEXTS["uz"]["finished_uz"].format(winners=winners_list_str)
    en_final = TEXTS["en"]["finished_en"].format(winners=winners_list_str)
    final_post = f"{uz_final}\n\n<blockquote><i>{en_final}</i></blockquote>"

    try:
        await bot.edit_message_text(
            chat_id=c["chat_id"],
            message_id=c["message_id"],
            text=final_post,
            parse_mode="HTML",
            reply_markup=None
        )
    except Exception:
        pass

    await contests_col.update_one({"_id": oid}, {"$set": {"status": "finished", "winners": winners}})

# ==========================================
# ADMIN: MAJBURIY OBUNA VA STATISTIKA
# ==========================================
@dp.message(F.text.in_(STAT_BUTTONS))
async def stats_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = await get_lang(message.from_user.id) or "uz"
    u_count = await users_col.count_documents({})
    c_count = await contests_col.count_documents({})
    await message.answer(TEXTS[lang]["stats"].format(users=u_count, contests=c_count), parse_mode="HTML")

@dp.message(F.text.in_(SUB_BUTTONS))
async def sub_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = await get_lang(message.from_user.id) or "uz"
    t = TEXTS[lang]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["add"], callback_data="sub:add")],
        [InlineKeyboardButton(text=t["remove"], callback_data="sub:remove")]
    ])
    await message.answer(t["channels_menu"], reply_markup=kb)

@dp.callback_query(F.data == "sub:add")
async def sub_add_options(call: CallbackQuery):
    lang = await get_lang(call.from_user.id) or "uz"
    t = TEXTS[lang]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["channel"], callback_data="subtype:channel")],
        [InlineKeyboardButton(text=t["group"], callback_data="subtype:group")],
        [InlineKeyboardButton(text=t["request"], callback_data="subtype:request")]
    ])
    await call.message.edit_text(t["choose_sub"], reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("subtype:"))
async def sub_type_choice(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Admin only", show_alert=True)
        return
    kind = call.data.split(":")[1]
    lang = await get_lang(call.from_user.id) or "uz"
    prompt_map = {"channel": "ask_channel", "group": "ask_group", "request": "ask_request"}
    await state.update_data(sub_type=kind)
    await state.set_state(SubFlow.link)
    await call.message.edit_text(TEXTS[lang][prompt_map[kind]], parse_mode="HTML")
    await call.answer()

@dp.message(SubFlow.link)
async def save_sub_link(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    kind = data["sub_type"]
    raw = (message.text or "").strip()
    lang = await get_lang(message.from_user.id) or "uz"

    try:
        if kind in ("channel", "group"):
            chat_identifier = raw.replace("https://t.me/", "@") if "t.me/" in raw and "+" not in raw else raw
            chat = await bot.get_chat(chat_identifier)
            chat_id = chat.id
            title = chat.title or raw
            url = normalize_url(f"https://t.me/{chat.username}" if chat.username else raw)
        else:
            if "t.me/" in raw and "+" not in raw:
                try:
                    c = await bot.get_chat(raw.replace("https://t.me/", "@"))
                    chat_id = c.id
                    title = c.title
                except Exception:
                    chat_id = None
                    title = f"Zayafka ({raw})"
            else:
                chat_id = None
                title = f"Zayafka ({raw})"
            url = normalize_url(raw)

        await channels_col.insert_one({
            "type": kind,
            "chat_id": chat_id,
            "title": title,
            "url": url,
            "created_at": datetime.now(timezone.utc)
        })
        await message.answer(TEXTS[lang]["added"])
    except Exception as exc:
        await message.answer(f"❌ Xatolik: {exc}\nBot kanal/guruhda admin ekanligini tekshiring!")

    await state.clear()

@dp.callback_query(F.data == "sub:remove")
async def sub_remove_list(call: CallbackQuery):
    docs = await channels_col.find().to_list(100)
    lang = await get_lang(call.from_user.id) or "uz"
    if not docs:
        await call.message.edit_text(TEXTS[lang]["none"])
        await call.answer()
        return
    rows = [[InlineKeyboardButton(text="🗑 " + d.get("title", "Kanal")[:40], callback_data=f"rm:{d['_id']}")] for d in docs]
    await call.message.edit_text("Olib tashlamoqchi bo'lganingizni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()

@dp.callback_query(F.data.startswith("rm:"))
async def remove_sub(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Admin only", show_alert=True)
        return
    oid = ObjectId(call.data.split(":", 1)[1])
    await channels_col.delete_one({"_id": oid})
    lang = await get_lang(call.from_user.id) or "uz"
    await call.message.edit_text(TEXTS[lang]["removed"])
    await call.answer()

@dp.chat_join_request()
async def join_request_listener(update: ChatJoinRequest):
    await join_requests_col.update_one(
        {"user_id": update.from_user.id, "chat_id": update.chat.id},
        {"$set": {"user_id": update.from_user.id, "chat_id": update.chat.id, "created_at": datetime.now(timezone.utc)}},
        upsert=True
    )

# ==========================================
# BOTNI ISHGA TUSHIRISH (MAIN)
# ==========================================
async def main():
    threading.Thread(target=run_web, daemon=True).start()
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Bot Render uchun barcha funksiyalar bilan ishga tushmoqda...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
