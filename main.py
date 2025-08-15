import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from config import settings
from database import create_tables, close_database
from handlers import user_handlers, admin_handlers, payment_handlers, bot_management
from loguru import logger
import redis.asyncio as redis
import sys

# Setup logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    f"{settings.LOG_PATH}/main.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

async def main():
    """Main bot function"""
    # Create directories if they don't exist
    os.makedirs(settings.BOT_STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
    os.makedirs(settings.LOG_PATH, exist_ok=True)
    
    # Create database tables
    await create_tables()
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    
    # Setup Redis storage for FSM
    redis_client = redis.from_url(settings.REDIS_URL)
    storage = RedisStorage(redis_client)
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(payment_handlers.router)
    dp.include_router(bot_management.router)
    
    logger.info("Bot Factory Platform started successfully!")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.session.close()
        await close_database()
        await redis_client.close()
        logger.info("Bot Factory Platform stopped")

if __name__ == "__main__":
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)
