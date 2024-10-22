from django.shortcuts import render
from django.views.decorators.http import require_POST, require_GET

from check.googlesheet_member_parser import update_member_data
# Create your views here.

@require_GET
def load_benchmark(request):
    update_member_data()
    update_problem_data()
    context={'last_update_time': '10:30 AM'}
    # test data
    daily_users = [
        {'name': 'User A', 'submission_time': '10:00 AM'},
        {'name': 'User B', 'submission_time': '10:05 AM'}
    ]
    weekly_users = [
        {'name': 'User C', 'submission_time': '10:00 AM'},
        {'name': 'User D', 'submission_time': '10:05 AM'}
    ]
    all_time_users = [
        {'name': 'User E', 'submission_time': '10:00 AM'},
        {'name': 'User F', 'submission_time': '10:05 AM'}
    ]
    context['daily_benchmark'] = daily_users
    context['weekly_benchmark'] = weekly_users
    context['all_time_benchmark'] = all_time_users
    return render(request,'benchmark.html',context)