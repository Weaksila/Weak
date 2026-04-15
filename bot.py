import asyncio
import os
import logging
import sys
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# Loglarni sozlash
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

try:
    from handlers import router as user_router
    from database import init_db, add_user
    from keyboards import main_menu_keyboard
except Exception as e:
    logger.error(f"IMPORT XATOSI: {e}")
    sys.exit(1)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("BOT_TOKEN topilmadi!")
    sys.exit(1)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- RENDER WEB SERVER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get("/", handle)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 10000))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Web server {port}-portda ishga tushdi.")
    except Exception as e:
        logger.error(f"Web serverda xatolik: {e}")

# --- START HANDLER ---
@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    try:
        # Xatolikni oldini olish uchun await'siz ishlatamiz
        init_db() 
        add_user(message.from_user.id)
        await message.answer(
            f"Salom, {message.from_user.full_name}! Zal botiga xush kelibsiz!",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Start handler xatosi: {e}")

async def main() -> None:
    try:
        # Bazani ishga tushirish (await olib tashlandi)
        init_db()
        logger.info("Ma'lumotlar bazasi tayyor.")
        
        # Portni parallel yurgizish
        asyncio.create_task(start_web_server())
        
        dp.include_router(user_router)
        logger.info("Bot polling boshlanmoqda...")
        
        # Botni ishga tushirishdan oldin eski xabarlarni o'chirib yuboramiz
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Asosiy jarayonda xatolik: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
