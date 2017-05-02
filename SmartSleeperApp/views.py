from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from django.views.decorators.csrf import csrf_exempt
from boto3.dynamodb.conditions import Key, Attr
from django.shortcuts import render
from datetime import datetime
import time
from dateutil import parser
# Imports the Alarm class
from SmartSleeperApp.models import *

#ML STUFF
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import numpy as np
##
import os

PATH = "C:\\" + "Users\Patrick\Desktop\18549\SmartSleeperWebPage\SmartSleeper\SmartSleeperApp"

epoch = datetime.utcfromtimestamp(0)
timeOffset = 0 #14400

def unix_time(dt):
    return (dt - epoch).total_seconds()

# Create your views here.
def parse_time(time):
  time = time.replace("T", " ")
  time = time.replace("Z", "")
  time = time[0:len(time)-4]
  return time

#Home Page
def home(request):
  context = {}
  timeStamps = []
  values = []
  pair = []
  pairCycle = []

  #Table stuff
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
  table = dynamodb.Table('SensorData')
  response = table.query(
      KeyConditionExpression=Key('SensorId').eq("Heartrate")
  )


  #Gets dates
  now = datetime.now()
  month = int(now.month)
  day = int(now.day)

  #Some awful logic to show today and yesterday - wont work at end of a month
  for i in reversed(response['Items']):
    if(i['Value'] == -1):
      break;

    timestampMonth = int(i['Timestamp'][6:7])
    timestampDay = int(i['Timestamp'][8:10])
    if(timestampDay != 24):
      # if(month == timestampMonth and (day == timestampDay or (day-1) == timestampDay)):
      timeStamps.append(parse_time(i['Timestamp']))
      values.append(i['Value'])


  #A way to return data
  results = machine_learning(timeStamps, values)

  if(len(timeStamps) > 0):
    pair = zip(timeStamps, values)
    pairCycle = zip(timeStamps, results)

  context['pair'] = pair
  context['pairCycle'] = pairCycle

  return render(request, 'SmartSleeperApp/home.html', context)

#Alarm Page
def alarm(request):
  context = {}
  errors = []
  alarms = []
  ids = []
  for alarm in Alarm.objects.all():
    alarms.append(datetime.fromtimestamp(float(alarm.text)))
    ids.append(alarm.id)
    print(alarm.id)

  alarmpair = zip(alarms, ids)
  sleep = getSleepTime()
  wakeup = "7:33 am"
  context = {'alarms':alarmpair, 'errors':errors, 'wakeup':wakeup, 'sleep':sleep}
  return render(request, 'SmartSleeperApp/alarm.html', context)


def getSleepTime():
  #Table stuff
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
  table = dynamodb.Table('SensorData')
  response = table.query(
      KeyConditionExpression=Key('SensorId').eq("Heartrate")
  )

  events = []



  for i in reversed(response['Items']):

    timestamp = i['Timestamp']

    if(i['Value'] == -1):
      hour = int(timestamp[11:13]) * 60
      minute = int(timestamp[14:16])
      events.append(hour+minute)

  average = sum(events)/len(events)

  hour = average/60
  minute = average%60
  amOrPm = "am"
  addZeroMinute = ""
  if(hour>12):
    hour -= 12
    amOrPm = "pm"

  if(hour == 0):
    hour = 12

  if(minute<10):
    addZeroMinute = "0"

  if(minute == 0):
    addZeroMinute = "00"

  sleepTime = str(hour) + ":" + str(minute) + addZeroMinute + " " + amOrPm

  return(sleepTime)







#Analytics Page
def analytics(request):
  context = {}
  timeStamps = []
  values = []
  pair = []
  pairCycle = []
  now = datetime.now()
  year = int(now.year)
  month = int(now.month)
  day = int(now.day)


  if not 'day' in request.POST or not request.POST['day']:
    print("")
  else:
    #Fix this nonsense at some point
    year = int(request.POST['year'])
    day = int(request.POST['day']) 
    if(request.POST['month'] == "Apr"):
      month = 4
    elif(request.POST['month'] == "May"):
      month = 5
    else:
      month = 6

  #####

  #Table stuff
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
  table = dynamodb.Table('SensorData')
  response = table.query(
      KeyConditionExpression=Key('SensorId').eq("Heartrate")
  )

  events = []

  for i in reversed(response['Items']):

    date = parse_time(i['Timestamp'])
    newDate = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    eastTime = datetime.fromtimestamp(newDate.total_seconds() - 14400) #4 hours



    timestampYear = int(eastTime.year)

    timestampMonth = int(eastTime.month)

    timestampDay = int(eastTime.day)


    if((month == timestampMonth) and (day == timestampDay or (day-1) == timestampDay) and (year == timestampYear)):
      if(i['Value'] == -1):
        events.append(parse_time(i['Timestamp']))
        continue;

      timeStamps.append(parse_time(i['Timestamp']))
      values.append(i['Value'])



  results = machine_learning(timeStamps, values)

  if(len(timeStamps) > 0):
    pair = zip(timeStamps, values)
    pairCycle = zip(timeStamps, results)

  context['pair'] = pair
  context['pairCycle'] = pairCycle

  if(day != 30):
    context['events'] = events


  #context['results'] = results
  return render(request, 'SmartSleeperApp/analytics.html', context)

#Settings Page
def settings(request):
  context = {}
  return render(request, 'SmartSleeperApp/settings.html', context)

#LED On
def led_on(request):
  context = {}
  #Table stuff
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
  table = dynamodb.Table('SensorData')


  sensorID = "Alarm"
  timestamp = "1"
  value = True

  response = table.update_item(
      Key={
          'SensorId': sensorID,
          'Timestamp': timestamp
      },
      ExpressionAttributeNames={
      "#v" : "Value"
      },
      UpdateExpression="set #v = :v",
      ExpressionAttributeValues={
          ':v': value
      },
      ReturnValues="UPDATED_NEW"
  )

  return render(request, 'SmartSleeperApp/settings.html', context)

#LED Off
def led_off(request):
  context = {}
  #Table stuff
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
  table = dynamodb.Table('SensorData')


  sensorID = "Alarm"
  timestamp = "1"
  value = False

  response = table.update_item(
      Key={
          'SensorId': sensorID,
          'Timestamp': timestamp
      },
      ExpressionAttributeNames={
      "#v" : "Value"
      },
      UpdateExpression="set #v = :v",
      ExpressionAttributeValues={
          ':v': value
      },
      ReturnValues="UPDATED_NEW"
  )

  return render(request, 'SmartSleeperApp/settings.html', context)



train = pd.read_csv(os.getcwd() + '/SmartSleeperApp/train.csv',nrows=30000)
cols = ['Start__sec_', 'ihr']
colsRes = ['sleepstage01']
trainArr = train.as_matrix(cols) #training array
trainRes = train.as_matrix(colsRes) # training results
## Training!
rf = RandomForestClassifier(n_estimators=50) # initialize
rf.fit(trainArr, trainRes) 

#ML Stuff
def machine_learning(timeStamps, values):


  #[0][0] is elapsed time, [0][1] is the ihr at the time
  initialTime = 0

  if(len(timeStamps) > 0): 
    initialTime = convert(timeStamps[len(timeStamps) - 1])


  testArr = []
  for i in range(0, len(timeStamps)):
    timeInSeconds = convert(timeStamps[i])
    elapsedTime = (timeInSeconds - initialTime)
    #print(elapsedTime)
    arr = [elapsedTime, values[i]]
    testArr.append(arr)

  results = []
  if(len(testArr) != 0):
    results = rf.predict(testArr)

  #Fixes the initial time
  for i in range(0, len(timeStamps)):
    timeInSeconds = convert(timeStamps[i])
    elapsedTime = abs(timeInSeconds - initialTime)
    if(results[i] > 1 and elapsedTime < 1200):
      results[i] = 1

  #test['predictions'] = results
  #print(results)

  return results

  # df = pd.DataFrame(test)
  # df.to_csv(r'C:\Users\Patrick\Desktop\18549\SmartSleeperWebPage\SmartSleeper\SmartSleeperApp\predictions.csv')

#date time conversion
def convert(timestamp):
  year = int(timestamp[0:4])
  month = int(timestamp[5:7])
  day = int(timestamp[8:10])
  hour = int(timestamp[11:13])
  minute = int(timestamp[14:16])
  second = int(timestamp[17:19])
  newDate = datetime(year, month, day, hour, minute, second)
  timeInSeconds = time.mktime(newDate.timetuple())
  return timeInSeconds

#Checks alarm
@csrf_exempt
def check_alarm(request):
  context = {}
  currentTime = datetime.today()
  for alarm in Alarm.objects.all():
    timeDelta = abs(unix_time(currentTime) - float(alarm.text)) - 14400 #FIX THIS LATER
    #If within 1 minute
    print(timeDelta)
    if(abs(timeDelta) < 60):
      print("TIME TO WAKE UP!")
      alarm.delete()
      led_on(request)

  return render(request, 'SmartSleeperApp/secret.html', context)

#Adds to alarm list
def add_alarm(request):
    errors = []  # A list to record messages for any errors we encounter.

    # Adds the new item to the database if the request parameter is present
    if not 'datetime' in request.POST or not request.POST['datetime']:
        errors.append('You must enter an alarm to add.')
    
    else:
        date = request.POST['datetime']
        newDate = datetime.strptime(date, '%d-%m-%Y %I:%M %p')
        new_alarm = Alarm(text=str(unix_time(newDate) + timeOffset))
        new_alarm.save()

    return alarm(request)
    # alarms = []
    # ids = []
    # for alarm in Alarm.objects.all():
    #   alarms.append(datetime.fromtimestamp(float(alarm.text)))
    #   ids.append(alarm.id)

    # alarmpair = zip(alarms, ids)
    # context = {'alarms':alarmpair, 'errors':errors}
    # return render(request, 'SmartSleeperApp/alarm.html', context)

#Remove alarm
def delete_alarm(request, item_id):
    errors = []

    # Deletes the item if present in the todo-list database.
    try:
        item_to_delete = Alarm.objects.get(id=item_id)
        item_to_delete.delete()
    except ObjectDoesNotExist:
        errors.append('The item did not exist in the todo list.')

    return alarm(request)

    # alarms = Alarm.objects.all()
    # context = {'alarms':alarms, 'errors':errors}
    # return render(request, 'SmartSleeperApp/alarm.html', context)
