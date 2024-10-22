from django.shortcuts import render
from django.views.decorators.http import require_POST, require_GET
# Create your views here.

@require_GET
def load_benchmark(request):
    context={'last_update_time': '10:30 AM'}
    # test data
    users = [
        {'name': 'User A', 'submission_time': '10:00 AM'},
        {'name': 'User B', 'submission_time': '10:05 AM'}
    ]
    context['users'] = users
    return render(request,'benchmark.html',context)