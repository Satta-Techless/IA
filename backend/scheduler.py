from apscheduler.schedulers.background import BackgroundScheduler
from .pipeline import run_daily_pipeline, run_weekly_deep_dive
from .cleanup import cleanup_old_files

scheduler = BackgroundScheduler()
scheduler.add_job(run_daily_pipeline, 'cron', hour=6, minute=0, id='daily')
scheduler.add_job(run_weekly_deep_dive, 'cron', day_of_week='mon', hour=7, minute=0, id='weekly')
scheduler.add_job(cleanup_old_files, 'cron', day_of_week='sun', hour=8, minute=0, id='cleanup')

def start_scheduler():
    scheduler.start()
    print("⏰ Scheduler started.")