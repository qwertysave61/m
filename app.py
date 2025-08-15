from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import os
from datetime import datetime, timedelta

from config import settings
from database import get_session, create_tables
from models import User, Bot, BotTemplate, Payment, SystemSettings
from services.bot_factory import BotFactory
from services.payment_service import PaymentService
from services.monitoring_service import MonitoringService
from services.notification_service import NotificationService
from celery_app import celery_app
from loguru import logger

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("RiseBuilder API starting up...")
    
    # Create database tables
    await create_tables()
    
    # Create necessary directories
    os.makedirs(settings.BOT_STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
    os.makedirs(settings.LOG_PATH, exist_ok=True)
    
    logger.info("RiseBuilder API started successfully")
    
    yield
    
    # Shutdown
    logger.info("RiseBuilder API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="RiseBuilder API",
    description="Telegram Bot Factory Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize services
bot_factory = BotFactory()
payment_service = PaymentService()
monitoring_service = MonitoringService()
notification_service = NotificationService()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        async with get_session() as session:
            await session.execute(select(1))
        
        # Check Redis connection
        result = celery_app.control.ping(timeout=1)
        redis_ok = bool(result)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "ok",
            "redis": "ok" if redis_ok else "error",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Dashboard endpoint
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    """Main dashboard"""
    try:
        # Get statistics
        total_users = await session.scalar(select(func.count(User.id)))
        total_bots = await session.scalar(select(func.count(Bot.id)).where(Bot.status != "deleted"))
        running_bots = await session.scalar(select(func.count(Bot.id)).where(Bot.status == "running"))
        
        # Today's statistics
        today = datetime.now().date()
        new_users_today = await session.scalar(
            select(func.count(User.id)).where(func.date(User.created_at) == today)
        )
        new_bots_today = await session.scalar(
            select(func.count(Bot.id)).where(func.date(Bot.created_at) == today)
        )
        
        # Revenue statistics
        total_revenue = await session.scalar(
            select(func.sum(Payment.amount)).where(Payment.status == "completed")
        ) or 0
        
        today_revenue = await session.scalar(
            select(func.sum(Payment.amount)).where(
                and_(
                    Payment.status == "completed",
                    func.date(Payment.completed_at) == today
                )
            )
        ) or 0
        
        # System health
        system_health = await monitoring_service.get_system_health()
        
        stats = {
            "total_users": total_users or 0,
            "total_bots": total_bots or 0,
            "running_bots": running_bots or 0,
            "new_users_today": new_users_today or 0,
            "new_bots_today": new_bots_today or 0,
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
            "system_health": system_health
        }
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

# API Routes

# Bot management
@app.get("/api/bots")
async def get_bots(session: AsyncSession = Depends(get_session)):
    """Get all bots"""
    try:
        result = await session.execute(
            select(Bot, User, BotTemplate)
            .join(User, Bot.user_id == User.id)
            .join(BotTemplate, Bot.template_id == BotTemplate.id)
            .where(Bot.status != "deleted")
            .order_by(Bot.created_at.desc())
        )
        
        bots = []
        for bot, user, template in result.all():
            bots.append({
                "id": bot.id,
                "name": bot.name,
                "username": bot.username,
                "status": bot.status,
                "template_name": template.name,
                "owner_name": user.first_name,
                "created_at": bot.created_at.isoformat(),
                "last_payment_date": bot.last_payment_date.isoformat() if bot.last_payment_date else None
            })
        
        return {"bots": bots}
        
    except Exception as e:
        logger.error(f"Get bots error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/start")
async def start_bot(bot_id: int, background_tasks: BackgroundTasks):
    """Start a bot"""
    try:
        # Use Celery for async bot starting
        task = celery_app.send_task(
            'tasks.bot_monitor.start_bot', 
            args=[bot_id]
        )
        
        return {
            "message": "Bot start initiated",
            "task_id": task.id
        }
        
    except Exception as e:
        logger.error(f"Start bot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/stop")
async def stop_bot(bot_id: int):
    """Stop a bot"""
    try:
        success = await bot_factory.stop_bot(bot_id)
        
        if success:
            return {"message": "Bot stopped successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop bot")
            
    except Exception as e:
        logger.error(f"Stop bot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/restart")
async def restart_bot(bot_id: int, background_tasks: BackgroundTasks):
    """Restart a bot"""
    try:
        # Use Celery for async bot restarting
        task = celery_app.send_task(
            'emergency_restart_bot',
            args=[bot_id],
            priority=10
        )
        
        return {
            "message": "Bot restart initiated",
            "task_id": task.id
        }
        
    except Exception as e:
        logger.error(f"Restart bot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bots/{bot_id}")
async def delete_bot(bot_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a bot"""
    try:
        # Get bot
        result = await session.execute(select(Bot).where(Bot.id == bot_id))
        bot = result.scalar_one_or_none()
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Delete bot using factory
        success = await bot_factory.delete_bot(bot_id)
        
        if success:
            # Update database
            bot.status = "deleted"
            bot.will_be_deleted_at = datetime.now()
            await session.commit()
            
            return {"message": "Bot deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete bot")
            
    except Exception as e:
        logger.error(f"Delete bot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bot analytics
@app.get("/api/bots/{bot_id}/analytics")
async def get_bot_analytics(bot_id: int, days: int = 7):
    """Get bot analytics"""
    try:
        analytics = await monitoring_service.get_bot_analytics(bot_id, days)
        return {"analytics": analytics}
        
    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Templates management
@app.get("/api/templates")
async def get_templates(session: AsyncSession = Depends(get_session)):
    """Get all bot templates"""
    try:
        result = await session.execute(
            select(BotTemplate).where(BotTemplate.is_active == True)
            .order_by(BotTemplate.category, BotTemplate.name)
        )
        
        templates = []
        for template in result.scalars().all():
            templates.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "creation_fee": template.creation_fee,
                "daily_fee": template.daily_fee,
                "complexity_level": template.complexity_level,
                "features": template.features
            })
        
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"Get templates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User management
@app.get("/api/users")
async def get_users(session: AsyncSession = Depends(get_session)):
    """Get all users"""
    try:
        result = await session.execute(
            select(User, func.count(Bot.id).label('bot_count'))
            .outerjoin(Bot, User.id == Bot.user_id)
            .group_by(User.id)
            .order_by(User.created_at.desc())
        )
        
        users = []
        for user, bot_count in result.all():
            users.append({
                "id": user.id,
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "balance": user.balance,
                "total_spent": user.total_spent,
                "bot_count": bot_count,
                "is_admin": user.is_admin,
                "is_banned": user.is_banned,
                "created_at": user.created_at.isoformat()
            })
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Payment management
@app.get("/api/payments")
async def get_payments(session: AsyncSession = Depends(get_session)):
    """Get all payments"""
    try:
        result = await session.execute(
            select(Payment, User, Bot)
            .join(User, Payment.user_id == User.id)
            .outerjoin(Bot, Payment.bot_id == Bot.id)
            .order_by(Payment.created_at.desc())
            .limit(100)
        )
        
        payments = []
        for payment, user, bot in result.all():
            payments.append({
                "id": payment.id,
                "amount": payment.amount,
                "payment_type": payment.payment_type,
                "status": payment.status,
                "user_name": user.first_name,
                "bot_name": bot.name if bot else None,
                "created_at": payment.created_at.isoformat(),
                "completed_at": payment.completed_at.isoformat() if payment.completed_at else None
            })
        
        return {"payments": payments}
        
    except Exception as e:
        logger.error(f"Get payments error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System monitoring
@app.get("/api/system/health")
async def get_system_health():
    """Get system health information"""
    try:
        health = await monitoring_service.get_system_health()
        return {"health": health}
        
    except Exception as e:
        logger.error(f"Get system health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/stats")
async def get_system_stats(session: AsyncSession = Depends(get_session)):
    """Get system statistics"""
    try:
        # Get comprehensive statistics
        stats = {}
        
        # User statistics
        stats["users"] = {
            "total": await session.scalar(select(func.count(User.id))),
            "active": await session.scalar(
                select(func.count(func.distinct(Bot.user_id)))
                .where(Bot.status == "running")
            ),
            "new_today": await session.scalar(
                select(func.count(User.id))
                .where(func.date(User.created_at) == datetime.now().date())
            )
        }
        
        # Bot statistics
        stats["bots"] = {
            "total": await session.scalar(
                select(func.count(Bot.id)).where(Bot.status != "deleted")
            ),
            "running": await session.scalar(
                select(func.count(Bot.id)).where(Bot.status == "running")
            ),
            "stopped": await session.scalar(
                select(func.count(Bot.id)).where(Bot.status == "stopped")
            ),
            "suspended": await session.scalar(
                select(func.count(Bot.id)).where(Bot.status == "suspended")
            )
        }
        
        # Payment statistics
        payment_stats = await payment_service.get_payment_statistics()
        stats["payments"] = payment_stats
        
        return {"stats": stats}
        
    except Exception as e:
        logger.error(f"Get system stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Task management
@app.get("/api/tasks")
async def get_active_tasks():
    """Get active Celery tasks"""
    try:
        inspect = celery_app.control.inspect()
        
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        return {
            "active": active_tasks,
            "scheduled": scheduled_tasks,
            "reserved": reserved_tasks
        }
        
    except Exception as e:
        logger.error(f"Get tasks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/cleanup")
async def trigger_cleanup():
    """Trigger emergency cleanup"""
    try:
        task = celery_app.send_task('emergency_cleanup', priority=10)
        return {"message": "Cleanup initiated", "task_id": task.id}
        
    except Exception as e:
        logger.error(f"Trigger cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 error handler"""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error": "Page not found",
            "status_code": 404
        },
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """500 error handler"""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error": "Internal server error",
            "status_code": 500
        },
        status_code=500
    )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        access_log=True
    )
