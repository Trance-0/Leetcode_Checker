# Create your tasks here

import os
from member.googlesheet_parser import update_member_data, update_benchmark

from celery import shared_task

import os
from celery import shared_task
from member.googlesheet_scraper import GoogleSheetScraper
from member.googlesheet_parser import update_member_data
from main.celery import app  # Import the Celery app

@shared_task
def update_member_data_task():
    update_member_data(GoogleSheetScraper(os.getenv("GOOGLE_SHEET_ID"), os.getenv("GOOGLE_API_KEY")))

# Register the task to run every 10 minutes (600 seconds)
app.conf.beat_schedule = app.conf.get('beat_schedule', {})
app.conf.beat_schedule['update_member_data_task'] = {
    'task': 'member.tasks.update_member_data_task',
    'schedule': 600.0,
}