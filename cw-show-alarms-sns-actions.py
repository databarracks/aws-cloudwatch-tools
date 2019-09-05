#!/usr/bin/python

# needs a re-write to use boto3 not CLI scraping

import os
import json
import argparse

def show_actions(actionName, alarmName):
    nSNScount = 0
    
    for snsTopicArn in alarmJson[actionName]:
        if snsTopicArn.find("arn:aws:sns:") != -1:
            snsTopicName = snsTopicArn[snsTopicArn.rfind(":")+1:]
            for k in snsSubscriptionsJson["Subscriptions"]:
                if (k["TopicArn"] == snsTopicArn):
                    print (f'{actionName},{alarmName},{snsTopicName},{k["Endpoint"]}')
                    nSNScount += 1

    return nSNScount

def printverbose(sStr):
    
    if bVerbose:
        print (f'Verbose Message: {sStr}')
    return
    

def main(args):

    global alarmJson 
    global snsSubscriptionsJson
    global bVerbose
    nAlarmActions = 0
    nInsufficientDataActions = 0
    nOKActions = 0
    
    bVerbose = args.verbose
    
    if args.region: 
        sRegionParam = f'--region {args.region}'
    else:
        sRegionParam = ""

    if args.profile: 
        sProfileParam = f'--profile {args.profile}'
    else:
        sProfileParam = ""

    sAlarmsQuery = f'aws {sRegionParam} {sProfileParam} cloudwatch describe-alarms --max-items 1000'
    printverbose(sAlarmsQuery)
    result = os.popen(sAlarmsQuery).read()
    cwAlarmsJson = json.loads(result)
    
    sSNSQuery = f'aws {sRegionParam} {sProfileParam} sns list-subscriptions --max-items 1000'
    printverbose(sSNSQuery)
    result = os.popen(sSNSQuery).read()
    snsSubscriptionsJson = json.loads(result)

    if not args.noheader: 
        print ("Actions,Alarm Name,Topic,Subscription Endpoint")

    for alarmJson in cwAlarmsJson["MetricAlarms"]:
        alarmName = alarmJson["AlarmName"]

        nAlarmActions += show_actions("AlarmActions", alarmName)
        nInsufficientDataActions += show_actions("InsufficientDataActions", alarmName)
        nOKActions += show_actions("OKActions", alarmName)
    
    printverbose ("Alarms Returned: " + str(len(alarmJson)))
    printverbose (f"Distinct SNS Actions Returned: Alarm Actions {nAlarmActions}, Insufficient Data Actions {nInsufficientDataActions}, OK Actions {nOKActions} = Total {nAlarmActions+nInsufficientDataActions+nOKActions}")
    
if __name__== "__main__":
    parser = argparse.ArgumentParser(description="List Cloudwatch alarms and show their corresponding SNS actions in a linear, CSV-style format.  Note this tool only shows SNS actions and ignores scaling actions.")
    parser.add_argument('--region', help='The AWS region name, e.g. eu-west-1')
    parser.add_argument('--profile', help='The AWS CLI profile to use')
    parser.add_argument('--noheader', action='store_true', help='don\'t add the CSV header row')
    parser.add_argument('--verbose', action='store_true', help='Verbose mode - display aws commands to execute, etc')
    args = parser.parse_args()
    main(args)    

