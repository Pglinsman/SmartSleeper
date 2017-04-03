from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr
from django.shortcuts import render

# Create your views here.
def parse_time(time):
  time = time.replace("T", " ")
  time = time.replace("Z", "")
  time = time[0:len(time)-4]
  # time = time[11:]
  # time = "2012-02-24"
  return time

def home(request):
  context = {}
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')

  table = dynamodb.Table('SensorData')

  response = table.query(
      KeyConditionExpression=Key('SensorId').eq("Temperature")
  )

  timeStamps = []
  values = []
  pair = []

  for i in response['Items']:
    timeStamps.append(parse_time(i['Timestamp']))
    values.append(i['Value'])
    #print(parse_time(i['Timestamp']), ":", i['Value'])

  print(timeStamps)
  pair = zip(timeStamps, values)
  context['pair'] = pair

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