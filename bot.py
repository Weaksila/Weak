import asyncio
import os
import logging
import sys
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# Loglarni eng yuqori darajada yoqamiz (Render loglarida ko'rinishi uchun)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

try:
    # O'zingizning fayllaringizdan importlar
    from handlers import router as user_router
    from database import init_db, add_user
    from keyboards import main_menu_keyboard
except Exception as e:
    logger.error(f"IMPORT XATOSI: {e}")
    sys.exit(1)

# Muhit o'zgaruvchilarini yuklash
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("BOT_TOKEN muhit o'zgaruvchisi topilmadi!")
    # Render-da status 1 bilan chiqish, lekin loglarda xatoni ko'rsatish
    sys.exit(1)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- RENDER UCHUN PORTNI BOG'LASH (WEB SERVER) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get("/", handle)
        runner = web.AppRunner(app)
        await runner.setup()
        
        # Render bergan PORTni ishlatamiz, agar bo'lmasa 10000
        port = int(os.environ.get("PORT", 10000))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Web server {port}-portda muvaffaqiyatli ishga tushdi.")
    except Exception as e:
        logger.error(f"Web server ishga tushishida xatolik: {e}")

# --- HANDLERLAR ---
@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    try:
        await init_db() 
        add_user(message.from_user.id)
        await message.answer(
            f"Salom, {message.from_user.full_name}! Zal botiga xush kelibsiz!",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Start handlerda xatolik: {e}")

async def main() -> None:
    try:
        # Ma'lumotlar bazasini ishga tushirish
        await init_db()
        logger.info("Ma'lumotlar bazasi tayyor.")
        
        # Web serverni polling bilan parallel ishlashini ta'minlaymiz
        asyncio.create_task(start_web_server())
        
        # Routerni qo'shish
        dp.include_router(user_router)
        
        # Botni ishga tushirish
        logger.info("Bot pollingni boshlamoqda...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Asosiy jarayonda xatolik: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
        sys.exit(1)
