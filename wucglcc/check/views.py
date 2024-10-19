from django.shortcuts import render
from django.views.decorators.http import require_POST, require_GET
# Create your views here.

@require_GET
def load_benchmark(request):
    context={}
    return render(request,'benchmark.html',context)