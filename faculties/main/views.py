from django.shortcuts import render
from django.http import HttpResponse
def index(request):
    return render(request, 'main/index.html')

def test_views(request):
    return render(request, 'main/test.html')

def test_result(request):
    return render(request, 'main/test_result.html')

