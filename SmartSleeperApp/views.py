from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from django.views.decorators.csrf import csrf_exempt
from boto3.dynamodb.conditions import Key, Attr
from django.shortcuts import render
from datetime import datetime
import time
import math
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
tolerance = 1

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


  return render(request, 'SmartSleeperApp/home.html', context)

#Alarm Page
def alarm(request):
  global tolerance
  context = {}
  errors = []
  alarms = []
  ids = []
  for alarm in Alarm.objects.all():
    alarms.append(datetime.fromtimestamp(float(alarm.text)))
    ids.append(alarm.id)
    print(alarm.id)

  alarmpair = zip(alarms, ids)
  sleep = getSleepTime(-1)
  wakeup = getSleepTime(-2)
  print("Tolerance " + str(tolerance))
  context = {'alarms':alarmpair, 'errors':errors, 'wakeup':wakeup, 'sleep':sleep, 'tolerance':tolerance, 'wakeup':wakeup}
  return render(request, 'SmartSleeperApp/alarm.html', context)


def getSleepTime(offset):

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
    eastTime = datetime.fromtimestamp(unix_time(newDate) - 14400) #4 hours

    if(i['Value'] == -1 and offset == -1):
      hour = int(eastTime.hour)
      minute = int(eastTime.minute)
      if(hour>12):
        hour = (-12 + hour%12)
        minute *= -1
      hour *= 60
      events.append(hour+minute)

    if(i['Value'] == -2 and offset == -2):
      hour = int(eastTime.hour)
      minute = int(eastTime.minute)
      if(hour>12):
        hour = (-12 + hour%12)
        minute *= -1
      hour *= 60
      events.append(hour+minute)

  average = sum(events)/len(events)

  print(average)

  hour = int(math.floor(average/60))
  minute = average%60
  if(hour < 0):
    average *= -1
    hour = 11 + hour
    minute = 60 - average%60
    amOrPm = "pm"
  elif(hour > 0):
    hour = hour
    minute = minute
    amOrPm = "am"
  else:
    hour = 12
    amOrPm = "am"

  addZeroMinute = ""

  if(minute<10):
    addZeroMinute = "0"

  if(minute == 0):
    addZeroMinute = "00"

  sleepTime = str(hour) + ":" + addZeroMinute + str(minute) + " " + amOrPm

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
    if(request.POST['month'] == "Jan"):
      month = 1
    elif(request.POST['month'] == "Feb"):
      month = 2
    elif(request.POST['month'] == "Mar"):
      month = 3
    elif(request.POST['month'] == "Apr"):
      month = 4
    elif(request.POST['month'] == "May"):
      month = 5
    elif(request.POST['month'] == "Jun"):
      month = 6
    elif(request.POST['month'] == "Jul"):
      month = 7
    elif(request.POST['month'] == "Aug"):
      month = 8
    elif(request.POST['month'] == "Sep"):
      month = 9
    elif(request.POST['month'] == "Oct"):
      month = 10
    elif(request.POST['month'] == "Nov"):
      month = 11
    elif(request.POST['month'] == "Dec"):
      month = 12
    else:
      month = 5

  #####
  selectedDate = datetime.strptime(str(year) + "-" + str(month) + "-" + str(day) + " " + "17", '%Y-%m-%d %H')

  #Table stuff
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
  table = dynamodb.Table('SensorData')
  response = table.query(
      KeyConditionExpression=Key('SensorId').eq("Heartrate")
  )

  events = []
  results = []
  tempTimeStamps = []
  tempValues = []
  lastTime = 0

  for i in reversed(response['Items']):

    date = parse_time(i['Timestamp'])
    newDate = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    eastTime = datetime.fromtimestamp(unix_time(newDate) - 14400) #4 hours


    timestampYear = int(eastTime.year)

    timestampMonth = int(eastTime.month)

    timestampDay = int(eastTime.day)

    timeDif = unix_time(eastTime) - unix_time(selectedDate)

    lastTime = unix_time(eastTime)


    if(timeDif > 0 and timeDif < 86400):
      if(i['Value'] == -1 or i['Value'] == -2):
        events.append(str(eastTime))
        if(i['Value'] == -1):
          initialTime = unix_time(eastTime)
          for result in machine_learning(tempTimeStamps, tempValues, initialTime):
            results.append(result)
          timeStamps += tempTimeStamps
          values += tempValues
          tempTimeStamps = []
          tempValues = []
        continue;

      tempTimeStamps.append(str(eastTime))
      tempValues.append(i['Value'])



  # results += machine_learning(timeStamps, values)


  #Calculate percents
  timeStamps += tempTimeStamps
  values += tempValues
  if((len(results) == 0) and (len(timeStamps) != 0)):
    for result in machine_learning(tempTimeStamps, values, lastTime):
      results.append(result)

  numAsleep = 0
  numREM = 0
  cycleZero = 0
  cycleOne = 0
  cycleTwo = 0
  cycleThree = 0
  cycleFour = 0

  for result in results:
    if(result >= 2):
      numAsleep += 1
    if(result == 5):
      numREM += 1
    if(result == 0):
      cycleZero += 1
    if(result == 1):
      cycleOne += 1
    if(result == 2):
      cycleTwo += 1
    if(result == 3):
      cycleThree += 1
    if(results == 4):
      cycleFour += 1

  # AVERAGES
  # 1: 4-5%
  # 2: 45-55%
  # 3: 4-6%
  # 4: 12-15%
  # 5: 20-25%

  percentAsleep = 100 * float(numAsleep)/max(1, len(results))
  percentREM = 100 * float(numREM)/max(1, len(results))
  percentZero = 100 * float(cycleZero)/max(1, len(results))
  percentOne = 100 * float(cycleOne)/max(1, len(results))
  percentTwo = 100 * float(cycleTwo)/max(1, len(results))
  percentThree = 100 * float(cycleThree)/max(1, len(results))
  percentFour = 100 * float(cycleFour)/max(1, len(results))
  averageOne = "5%"
  averageTwo = "50%"
  averageThree = "5%"
  averageFour = "13.5%"
  averageREM = "22.5%"


  if(len(timeStamps) > 0):
    pair = zip(timeStamps, values)
    pairCycle = zip(timeStamps, results)

  context['pair'] = pair
  context['pairCycle'] = pairCycle
  context['percentAsleep'] = "%.2f" % (percentAsleep)
  context['percentREM'] = "%.2f" % (percentREM)
  context['percentZero'] = "%.2f" % (percentZero)
  context['percentOne'] = "%.2f" % (percentOne)
  context['percentTwo'] = "%.2f" % (percentTwo)
  context['percentThree'] = "%.2f" % (percentThree)
  context['percentFour'] = "%.2f" % (percentFour)
  context['averageOne'] = averageOne
  context['averageTwo'] = averageTwo
  context['averageThree'] = averageThree
  context['averageFour'] = averageFour
  context['averageREM'] = averageREM
  context['events'] = events
  context['dateInfo'] = str(month) + "/" + str(day)  + "/" + str(year)


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

  return alarm(request)

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

  return alarm(request)



train = pd.read_csv(os.getcwd() + '/SmartSleeperApp/train.csv',nrows=30000)
cols = ['Start__sec_', 'ihr']
colsRes = ['sleepstage01']
trainArr = train.as_matrix(cols) #training array
trainRes = train.as_matrix(colsRes) # training results
## Training!
rf = RandomForestClassifier(n_estimators=50) # initialize
rf.fit(trainArr, trainRes) 

#ML Stuff
def machine_learning(timeStamps, values, initialTime):
  print(" ")
  print("Independent Machine Learning Call")


  #[0][0] is elapsed time, [0][1] is the ihr at the time

  testArr = []
  for i in range(0, len(timeStamps)):
    newDate = datetime.strptime(timeStamps[i], '%Y-%m-%d %H:%M:%S')
    timeInSeconds = unix_time(newDate)
    elapsedTime = (timeInSeconds - initialTime)
    #print(elapsedTime)
    arr = [elapsedTime, values[i]]
    testArr.append(arr)
    print("Elapsed time is: " + str(elapsedTime) + ", Value is: " + str(values[i]))

 




  results = []
  if(len(testArr) != 0):
    results = rf.predict(testArr)

 


  #Fixes the initial time
  for i in range(0, len(timeStamps)):
    newDate = datetime.strptime(timeStamps[i], '%Y-%m-%d %H:%M:%S')
    timeInSeconds = unix_time(newDate)
    elapsedTime = abs(timeInSeconds - initialTime)
    if(results[i] > 1 and elapsedTime < 1800):
      results[i] = 1

  #test['predictions'] = results
  #print(results)
  return results


#Checks alarm
@csrf_exempt
def check_alarm(request):
  context = {}
  currentTime = datetime.today()
  for alarm in Alarm.objects.all():
    timeDelta = abs(unix_time(currentTime) - float(alarm.text)) - 14400 #FIX THIS LATER
    #If within 1 minute
    print(timeDelta)
    if(abs(timeDelta) < (tolerance*60)):
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

#Change tolerance
def change_tolerance(request):
  errors = []  # A list to record messages for any errors we encounter.
  global tolerance
  print("In change tolerance")
  if not 'time' in request.POST or not request.POST['time']:
      errors.append('You must enter an alarm to add.')
  else:
      print("In a good if statement")
      print(request.POST['time'])
      if(request.POST['time'].isdigit()):
          print("Time")

          tolerance = int(request.POST['time'])

  return alarm(request)


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
