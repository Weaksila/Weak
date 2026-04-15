import asyncio
import os
import logging
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# O'zingizning fayllaringizdan importlar
from handlers import router as user_router
from database import init_db, add_user
from keyboards import main_menu_keyboard

# Loglarni yoqish (xatoliklarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# Muhit o'zgaruvchilarini yuklash
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("XATO: BOT_TOKEN topilmadi!")
    # Render-da status 1 bilan chiqmaslik uchun, lekin xatoni bildirish uchun
    TOKEN = "YOUR_TOKEN_HERE" 

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- RENDER UCHUN PORTNI BOG'LASH (MUHIM) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render bergan PORTni ishlatamiz, agar bo'lmasa 10000 (Render default)
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server {port}-portda ishga tushdi.")

# --- HANDLERLAR ---
@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    await init_db() 
    add_user(message.from_user.id)
    await message.answer(
        f"Salom, {message.from_user.full_name}! Zal botiga xush kelibsiz!\n\nMen sizga mashg'ulotlaringizni rejalashtirish, natijalaringizni kuzatish va ovqatlanishingizni nazorat qilishda yordam beraman.",
        reply_markup=main_menu_keyboard()
    )

async def main() -> None:
    # Ma'lumotlar bazasini ishga tushirish
    await init_db()
    
    # Web serverni ishga tushirish (Render "No open ports detected" xatosi bermasligi uchun)
    # Bu qismni polling bilan parallel ishlashini ta'minlaymiz
    asyncio.create_task(start_web_server())
    
    # Routerni qo'shish
    dp.include_router(user_router)
    
    # Botni ishga tushirish
    logging.info("Bot pollingni boshladi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
    except Exception as e:
        logging.error(f"Kutilmagan xatolik: {e}")
