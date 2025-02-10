from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Q
from django.views.decorators.http import require_POST, require_GET

# import scraper
from member.googlesheet_scraper import GoogleSheetScraper
from member.googlesheet_parser import update_member_data, update_benchmark

# import models
from check.models import Problem, ProblemStatusChoices, Schedule
from member.models import Member, ServerOperations

# import logger
import logging
logger = logging.getLogger(__name__)

# load env variables
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR,'.env'))

# utils functions:

def last_submission_time(member_id):
    # get all schedule id of this member
    schedule_ids = Schedule.objects.filter(member_id=member_id).values_list('id', flat=True)
    if schedule_ids.count() == 0:
        return member_id.date_joined
    # get all problem of this schedule id
    problems = Problem.objects.filter(Q(schedule_id__in=schedule_ids) & Q(status=ProblemStatusChoices.AC)).order_by('-done_date').first()
    if problems is None:
        return member_id.date_joined
    return problems.done_date


# Create your views here.

@require_GET
def get_ac_data(request):
    update_benchmark()
    return JsonResponse({'message': 'AC data correctly updated'})

@require_GET
def get_schedule_data(request):
    update_member_data(GoogleSheetScraper(os.getenv("GOOGLE_SHEET_ID"), os.getenv("GOOGLE_API_KEY")))
    return JsonResponse({'message': 'Schedule data correctly updated'})


@require_GET
def get_benchmark(request):
    # update_member_data(GoogleSheetScraper(os.getenv("GOOGLE_SHEET_ID"), os.getenv("GOOGLE_API_KEY")))
    # update_benchmark()
    context={'last_update_time': 'N/A'}
    # test data
    daily_submissions = Problem.objects.filter(
        Q(schedule_id__member_id__user_id__is_staff=False)&
        Q(status=ProblemStatusChoices.AC)&
        Q(done_date__date__gte=timezone.now().date()-timedelta(days=1))
        )
    daily_users = daily_submissions.values('schedule_id__member_id').distinct()
    daily_ranking = sorted([{
        "user": Member.objects.get(id=problem['schedule_id__member_id']), 
        "AC_count": daily_submissions.filter(schedule_id__member_id=problem['schedule_id__member_id']).count(), 
        "last_submission_time": last_submission_time(problem['schedule_id__member_id'])
        } for problem in daily_users], key=lambda x: x['AC_count'], reverse=True)
    
    logger.info(f"Daily ranking: {daily_ranking}, extracting from: {daily_users}, recent submission: {daily_submissions}")

    weekly_submissions = Problem.objects.filter(
        Q(schedule_id__member_id__user_id__is_staff=False)&
        Q(status=ProblemStatusChoices.AC)&
        Q(done_date__date__gte=timezone.now().date()-timedelta(days=7))
        )
    weekly_users = weekly_submissions.values('schedule_id__member_id').distinct()
    weekly_ranking = sorted([{
        "user": Member.objects.get(id=problem['schedule_id__member_id']), 
        "AC_count": weekly_submissions.filter(schedule_id__member_id=problem['schedule_id__member_id']).count(), 
        "last_submission_time": last_submission_time(problem['schedule_id__member_id'])
        } for problem in weekly_users], key=lambda x: x['AC_count'], reverse=True)
    logger.info(f"Weekly ranking: {weekly_ranking}, extracting from: {weekly_users}, recent submission: {weekly_submissions}")

    all_time_submissions = Problem.objects.filter(
        Q(schedule_id__member_id__user_id__is_staff=False)&
        Q(status=ProblemStatusChoices.AC)
        )
    all_time_users = all_time_submissions.values('schedule_id__member_id').distinct()
    all_time_ranking = sorted([{
        "user": Member.objects.get(id=problem['schedule_id__member_id']), 
        "AC_count": all_time_submissions.filter(schedule_id__member_id=problem['schedule_id__member_id']).count(), 
        "last_submission_time": last_submission_time(problem['schedule_id__member_id'])
        } for problem in all_time_users], key=lambda x: x['AC_count'], reverse=True)
    logger.info(f"All time ranking: {all_time_ranking}, extracting from: {all_time_users}, recent submission: {all_time_submissions}")

    context['daily_benchmark'] = daily_ranking
    context['weekly_benchmark'] = weekly_ranking
    context['all_time_benchmark'] = all_time_ranking
    context['logs'] = ServerOperations.objects.all().order_by('-timestamp')[:10]
    return render(request,'benchmark_display.html',context)