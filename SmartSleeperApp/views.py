from django.shortcuts import render

# Create your views here.
def home(request):
  context = {}
  return render(request, 'SmartSleeperApp/home.html', context)

def alarm(request):
  context = {}
  return render(request, 'SmartSleeperApp/alarm.html', context)

def analytics(request):
  context = {}
  return render(request, 'SmartSleeperApp/analytics.html', context)

def settings(request):
  context = {}
  return render(request, 'SmartSleeperApp/settings.html', context)