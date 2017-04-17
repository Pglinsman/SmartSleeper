from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr
from django.shortcuts import render
import datetime
import time
from dateutil import parser

#ML STUFF
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import numpy as np
##
import os

PATH = "C:\\" + "Users\Patrick\Desktop\18549\SmartSleeperWebPage\SmartSleeper\SmartSleeperApp"

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

  #Table stuff
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
  table = dynamodb.Table('SensorData')
  response = table.query(
      KeyConditionExpression=Key('SensorId').eq("Temperature")
  )


  #Gets dates
  now = datetime.datetime.now()
  month = int(now.month)
  day = int(now.day)

  #Some awful logic to show today and yesterday - wont work at end of a month
  for i in response['Items']:
    timestampMonth = int(i['Timestamp'][6:7])
    timestampDay = int(i['Timestamp'][8:10])
    if(month == timestampMonth and (day == timestampDay or (day-1) == timestampDay)):
      timeStamps.append(parse_time(i['Timestamp']))
      values.append(i['Value'])

  #A way to return data
  if(len(timeStamps) > 0):
    pair = zip(timeStamps, values)
  context['pair'] = pair

  return render(request, 'SmartSleeperApp/home.html', context)

#Alarm Page
def alarm(request):
  context = {}
  return render(request, 'SmartSleeperApp/alarm.html', context)


#Analytics Page
def analytics(request):
  context = {}
  timeStamps = []
  values = []
  pair = []
  pairCycle = []
  now = datetime.datetime.now()
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
      month = 0

  #Table stuff
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
  table = dynamodb.Table('SensorData')
  response = table.query(
      KeyConditionExpression=Key('SensorId').eq("Temperature")
  )

  for i in response['Items']:

    timestampYear = int(i['Timestamp'][0:4])

    timestampMonth = int(i['Timestamp'][6:7])

    timestampDay = int(i['Timestamp'][8:10])



    if((month == timestampMonth) and (day == timestampDay or (day-1) == timestampDay) and (year == timestampYear)):
      timeStamps.append(parse_time(i['Timestamp']))
      values.append(i['Value'])

  results = machine_learning(timeStamps, values)

  if(len(timeStamps) > 0):
    pair = zip(timeStamps, values)
    pairCycle = zip(timeStamps, results)

  context['pair'] = pair
  context['pairCycle'] = pairCycle


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



#ML Stuff
def machine_learning(timeStamps, values):
  train = pd.read_csv(os.getcwd() + '/SmartSleeperApp/train.csv',nrows=30000)
  test = pd.read_csv(os.getcwd() + '/SmartSleeperApp/test.csv')

  cols = ['Start__sec_', 'ihr']
  colsRes = ['sleepstage01']

  trainArr = train.as_matrix(cols) #training array
  trainRes = train.as_matrix(colsRes) # training results


  ## Training!
  rf = RandomForestClassifier(n_estimators=50) # initialize
  rf.fit(trainArr, trainRes) 

  testArr = test.as_matrix(cols)

  #[0][0] is elapsed time, [0][1] is the ihr at the time

  elapsedTime = 0
  prevTime = 0
  testArr = []
  for i in range(0, len(timeStamps)):
    timeInSeconds = convert(timeStamps[i])
    if(prevTime != 0):
      elapsedTime = (timeInSeconds - prevTime) + 1000
    else:
      elapsedTime = 1000

    arr = [elapsedTime, values[i]]
    testArr.append(arr)
    prevTime = timeInSeconds

  results = []
  if(len(testArr) != 0):
    results = rf.predict(testArr)


  #test['predictions'] = results

  print(results)

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
  newDate = datetime.datetime(year, month, day, hour, minute, second)
  timeInSeconds = time.mktime(newDate.timetuple())
  return timeInSeconds