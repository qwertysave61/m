from celery import Celery
from config import settings
import os

# Create Celery app
celery_app = Celery(
    "risebuilder",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "tasks.payment_checker",
        "tasks.bot_monitor", 
        "tasks.cleanup_task"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tashkent',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'tasks.payment_checker.*': {'queue': 'payments'},
        'tasks.bot_monitor.*': {'queue': 'monitoring'},
        'tasks.cleanup_task.*': {'queue': 'cleanup'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Payment checker - every hour
        'check-payments': {
            'task': 'tasks.payment_checker.check_daily_payments',
            'schedule': 3600.0,  # 1 hour
            'options': {'queue': 'payments'}
        },
        
        # Bot health check - every 5 minutes
        'check-bot-health': {
            'task': 'tasks.bot_monitor.check_bot_health',
            'schedule': 300.0,  # 5 minutes
            'options': {'queue': 'monitoring'}
        },
        
        # Performance monitoring - every 15 minutes
        'monitor-performance': {
            'task': 'tasks.bot_monitor.monitor_performance',
            'schedule': 900.0,  # 15 minutes
            'options': {'queue': 'monitoring'}
        },
        
        # Analytics collection - every 30 minutes
        'collect-analytics': {
            'task': 'tasks.bot_monitor.collect_analytics',
            'schedule': 1800.0,  # 30 minutes
            'options': {'queue': 'monitoring'}
        },
        
        # File cleanup - every 6 hours
        'cleanup-files': {
            'task': 'tasks.cleanup_task.cleanup_files',
            'schedule': 21600.0,  # 6 hours
            'options': {'queue': 'cleanup'}
        },
        
        # Full cleanup - daily at 2 AM
        'daily-cleanup': {
            'task': 'tasks.cleanup_task.daily_cleanup',
            'schedule': {
                'hour': 2,
                'minute': 0
            },
            'options': {'queue': 'cleanup'}
        },
        
        # Daily report - every day at 9 AM
        'daily-report': {
            'task': 'tasks.payment_checker.generate_daily_report',
            'schedule': {
                'hour': 9,
                'minute': 0
            },
            'options': {'queue': 'payments'}
        },
        
        # System health check - every 10 minutes
        'system-health': {
            'task': 'tasks.bot_monitor.check_system_health',
            'schedule': 600.0,  # 10 minutes
            'options': {'queue': 'monitoring'}
        },
        
        # Cleanup old data - weekly on Sunday at 3 AM
        'weekly-cleanup': {
            'task': 'tasks.cleanup_task.weekly_cleanup',
            'schedule': {
                'hour': 3,
                'minute': 0,
                'day_of_week': 0  # Sunday
            },
            'options': {'queue': 'cleanup'}
        },
    },
    
    # Worker settings
    worker_concurrency=4,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=4,
    
    # Task settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    
    # Redis settings
    redis_max_connections=20,
    redis_retry_on_timeout=True,
    
    # Result backend settings
    result_expires=86400,  # 1 day
    result_persistent=True,
)

# Task definitions
@celery_app.task(bind=True)
def check_daily_payments(self):
    """Check and process daily payments"""
    import asyncio
    from tasks.payment_checker import PaymentChecker
    
    async def run_check():
        checker = PaymentChecker()
        return await checker.check_daily_payments()
    
    return asyncio.run(run_check())

@celery_app.task(bind=True)
def check_bot_health(self):
    """Check bot health and restart failed bots"""
    import asyncio
    from tasks.bot_monitor import BotMonitor
    
    async def run_check():
        monitor = BotMonitor()
        return await monitor.check_bot_health()
    
    return asyncio.run(run_check())

@celery_app.task(bind=True)
def monitor_performance(self):
    """Monitor bot performance"""
    import asyncio
    from tasks.bot_monitor import BotMonitor
    
    async def run_monitor():
        monitor = BotMonitor()
        return await monitor.monitor_bot_performance()
    
    return asyncio.run(run_monitor())

@celery_app.task(bind=True)
def collect_analytics(self):
    """Collect bot analytics"""
    import asyncio
    from tasks.bot_monitor import BotMonitor
    
    async def run_collection():
        monitor = BotMonitor()
        return await monitor.collect_bot_analytics()
    
    return asyncio.run(run_collection())

@celery_app.task(bind=True)
def cleanup_files(self):
    """Clean up temporary and old files"""
    import asyncio
    from tasks.cleanup_task import CleanupTask
    
    async def run_cleanup():
        cleanup = CleanupTask()
        return await cleanup.run_file_cleanup()
    
    return asyncio.run(run_cleanup())

@celery_app.task(bind=True)
def daily_cleanup(self):
    """Run daily cleanup tasks"""
    import asyncio
    from tasks.cleanup_task import CleanupTask
    
    async def run_cleanup():
        cleanup = CleanupTask()
        return await cleanup.run_daily_cleanup()
    
    return asyncio.run(run_cleanup())

@celery_app.task(bind=True)
def generate_daily_report(self):
    """Generate and send daily report"""
    import asyncio
    from tasks.payment_checker import PaymentChecker
    
    async def run_report():
        checker = PaymentChecker()
        return await checker.generate_daily_report()
    
    return asyncio.run(run_report())

@celery_app.task(bind=True)
def check_system_health(self):
    """Check system health"""
    import asyncio
    from tasks.bot_monitor import BotMonitor
    
    async def run_check():
        monitor = BotMonitor()
        return await monitor.monitor_system_resources()
    
    return asyncio.run(run_check())

@celery_app.task(bind=True)
def weekly_cleanup(self):
    """Run weekly cleanup tasks"""
    import asyncio
    from tasks.cleanup_task import CleanupTask
    
    async def run_cleanup():
        cleanup = CleanupTask()
        stats = await cleanup.cleanup_service.run_full_cleanup()
        await cleanup.cleanup_old_database_records()
        return stats
    
    return asyncio.run(run_cleanup())

# Emergency tasks
@celery_app.task(bind=True, priority=10)
def emergency_restart_bot(self, bot_id: int):
    """Emergency bot restart"""
    import asyncio
    from services.bot_factory import BotFactory
    
    async def restart_bot():
        factory = BotFactory()
        return await factory.restart_bot(bot_id)
    
    return asyncio.run(restart_bot())

@celery_app.task(bind=True, priority=10)
def emergency_cleanup(self):
    """Emergency system cleanup"""
    import asyncio
    from tasks.cleanup_task import CleanupTask
    
    async def run_emergency():
        cleanup = CleanupTask()
        return await cleanup.emergency_cleanup()
    
    return asyncio.run(run_emergency())

# Custom task for bot creation
@celery_app.task(bind=True)
def create_bot_async(self, user_id: int, template_id: int, bot_name: str, 
                    bot_token: str, config: dict = None):
    """Asynchronously create a bot"""
    import asyncio
    from services.bot_factory import BotFactory
    
    async def create_bot():
        factory = BotFactory()
        return await factory.create_bot(user_id, template_id, bot_name, bot_token, config)
    
    return asyncio.run(create_bot())

# Task for processing payments
@celery_app.task(bind=True)
def process_payment_async(self, payment_id: int):
    """Asynchronously process a payment"""
    import asyncio
    from services.payment_service import PaymentService
    
    async def process_payment():
        service = PaymentService()
        return await service.approve_payment(payment_id)
    
    return asyncio.run(process_payment())

# Monitoring task for specific bot
@celery_app.task(bind=True)
def monitor_bot_health(self, bot_id: int):
    """Monitor specific bot health"""
    import asyncio
    from services.monitoring_service import MonitoringService
    
    async def monitor_bot():
        service = MonitoringService()
        return await service.get_bot_analytics(bot_id)
    
    return asyncio.run(monitor_bot())

if __name__ == "__main__":
    celery_app.start()
