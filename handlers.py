import logging
import datetime
import os
import io
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Render-da matplotlib xatosi bermasligi uchun 'Agg' backendini tanlaymiz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from keyboards import main_menu_keyboard
from database import (
    add_workout, get_workouts, add_nutrition, get_nutrition, 
    add_weight, get_weight_history, get_user_id, add_user, 
    update_user_height, get_user_height, add_reminder, 
    get_reminders, add_water_intake, get_daily_water_intake, 
    add_ai_message, get_ai_chat_history
)

# Groq importini try-except ichiga olamiz
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)
router = Router()

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_AVAILABLE and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None
    logger.warning("GROQ_API_KEY topilmadi yoki kutubxona yo'q. AI funksiyalari o'chirildi.")

# FSM States
class Form(StatesGroup):
    waiting_for_day = State()
    waiting_for_weight_input = State()
    waiting_for_height_input = State()
    waiting_for_food_input = State()
    waiting_for_reminder_time = State()
    waiting_for_reminder_message = State()
    waiting_for_ai_question = State()
    waiting_for_water_amount = State()

# Mashqlar rejasi (qisqartirilgan holatda saqlaymiz)
WORKOUT_PLAN = {
    "dushanba": {"text": "Ko'krak va Triceps...", "videos": {}},
    "seshanba": {"text": "Orqa va Biceps...", "videos": {}},
    "chorshanba": {"text": "Dam olish kuni", "videos": {}},
    "payshanba": {"text": "Yelka va Oyoq...", "videos": {}},
    "juma": {"text": "Full Body...", "videos": {}},
    "shanba": {"text": "Kardio...", "videos": {}},
    "yakshanba": {"text": "Dam olish kuni", "videos": {}}
}

async def generate_weight_chart(user_id):
    try:
        history = get_weight_history(user_id)
        if not history: return None
        dates = [datetime.datetime.strptime(item[0], "%Y-%m-%d") for item in history]
        weights = [item[1] for item in history]
        plt.figure(figsize=(8, 5))
        plt.plot(dates, weights, marker='o')
        plt.title('Vazn Tarixi')
        plt.grid(True)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        logger.error(f"Grafik xatosi: {e}")
        return None

@router.message(F.text == "Mashqlar Rejasi")
async def workout_plan(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_day)
    await message.answer("Kunni kiriting (Dushanba...):")

@router.message(Form.waiting_for_day)
async def show_day(message: types.Message, state: FSMContext):
    day = message.text.lower()
    await message.answer(WORKOUT_PLAN.get(day, {"text": "Kun topilmadi"})["text"])
    await state.clear()

@router.message(F.text == "Natijalarim")
async def results(message: types.Message):
    user_id = get_user_id(message.from_user.id)
    chart = await generate_weight_chart(user_id)
    if chart:
        await message.answer_photo(types.BufferedInputFile(chart.getvalue(), filename='chart.png'))
    else:
        await message.answer("Ma'lumot yo'q.")

@router.message(F.text == "Kkal Hisoblagich")
async def kkal(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_food_input)
    await message.answer("Ovqatni kiriting:")

@router.message(Command("vazn"))
async def weight_cmd(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_weight_input)
    await message.answer("Vazningizni kiriting:")

@router.message(Form.waiting_for_weight_input)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        w = float(message.text)
        add_weight(get_user_id(message.from_user.id), datetime.date.today().strftime("%Y-%m-%d"), w)
        await message.answer(f"Saqlandi: {w} kg")
    except: await message.answer("Xato son.")
    finally: await state.clear()

@router.message(F.text == "BMI Hisoblash")
@router.message(Command("bmi"))
async def bmi(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_height_input)
    await message.answer("Bo'yingizni kiriting (sm):")

@router.message(Form.waiting_for_height_input)
async def process_height(message: types.Message, state: FSMContext):
    try:
        h = float(message.text)
        update_user_height(message.from_user.id, h)
        await message.answer(f"Bo'y {h} sm saqlandi.")
    except: await message.answer("Xato son.")
    finally: await state.clear()

@router.message(F.text == "Suv Balansi")
@router.message(Command("water"))
async def water(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_water_amount)
    await message.answer("Suv miqdori (ml):")

@router.message(Form.waiting_for_water_amount)
async def process_water(message: types.Message, state: FSMContext):
    try:
        ml = int(message.text)
        add_water_intake(get_user_id(message.from_user.id), datetime.date.today().strftime("%Y-%m-%d"), ml)
        await message.answer(f"Qabul qilindi: {ml} ml")
    except: await message.answer("Xato son.")
    finally: await state.clear()

@router.message(F.text == "AI Yordamchi")
@router.message(Command("ai"))
async def ai_cmd(message: types.Message, state: FSMContext):
    if not groq_client:
        await message.answer("AI o'chirilgan.")
        return
    await state.set_state(Form.waiting_for_ai_question)
    await message.answer("Savolingizni bering:")

@router.message(Form.waiting_for_ai_question)
async def process_ai(message: types.Message, state: FSMContext):
    try:
        q = message.text
        res = groq_client.chat.completions.create(messages=[{"role": "user", "content": q}], model="llama3-8b-8192")
        await message.answer(res.choices[0].message.content)
    except Exception as e: await message.answer(f"AI xatosi: {e}")
    finally: await state.clear()

@router.message(F.text == "Yordam")
@router.message(Command("help"))
async def help_h(message: types.Message):
    await message.answer("Zalga Bot yordami. Tugmalardan foydalaning.")
