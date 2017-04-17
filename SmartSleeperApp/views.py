from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr
from django.shortcuts import render

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
  dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')

  table = dynamodb.Table('data')

  response = table.query(KeyConditionExpression=Key('pptid').eq('1'))

  timeStamps = []
  values = []
  pair = []

  for i in response['Items']:
    timeStamps.append(i['start_sec'])
    values.append(i['ihr'])

  pair = zip(timeStamps, values)
  context['pair'] = pair

  results = machine_learning()

  context['results'] = results
  return render(request, 'SmartSleeperApp/analytics.html', context)

#Settings Page
def settings(request):
  context = {}
  return render(request, 'SmartSleeperApp/settings.html', context)

#ML Stuff
def machine_learning():
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

  results = rf.predict(testArr)

  test['predictions'] = results

  return results[0:3]

  # df = pd.DataFrame(test)
  # df.to_csv(r'C:\Users\Patrick\Desktop\18549\SmartSleeperWebPage\SmartSleeper\SmartSleeperApp\predictions.csv')
