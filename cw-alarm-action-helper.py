#!/usr/bin/python

# Manipulate a cloudwatch alarm's actions.
# Designed to only deal with adding/removing/replacing one action arn at a time, passing a list of arns is not supported
#
# Functions available are:
#   Add: add an alarm action arn 
#   Remove: remove an alarm action arn 
#   Replace: replace an alarm action arn (add + remove in one step)
#
# Run the script with --help to see syntax

import boto3
import argparse

def print_verbose(pMsg):

    if bVerbose:
        print (f'Verbose Message:  {pMsg}')
        
    return
    

def main(args):

    global bVerbose
    bVerbose = args.verbose

    # parameter sanity checks
    sCurrentActionArn = args.current_action_arn
    
    if args.change in ["replace-alarm-action", "add-alarm-action"]:
        if args.new_action_arn:
            sNewActionArn = args.new_action_arn
        else:
            print ("Error:  You must specify both the new action arn for a change of type 'add' or 'replace'")
            exit()

    if args.change in ["replace-alarm-action", "remove-alarm-action"]:
        if not args.current_action_arn:
            print ("Error:  You must specify a current alarm arn for a change of type 'replace' or 'remove'")

    # prepare session parameters     
    if args.profile:
        boto3.setup_default_session(profile_name = args.profile)

    if args.region:
        client = boto3.client('cloudwatch', region_name = args.region)
    else:
        client = boto3.client('cloudwatch')
   
    # create session
    try:
        alarms = client.describe_alarms(AlarmNames=[args.alarm_name])
    except: 
        print (f"Error:  Couldn't find an alarm named '{args.alarm_name}'")
        exit()

    if (len(alarms['MetricAlarms'])) < 1:
        print (f"Error:  describe-alarms did not return a valid dictionary.  Check the alarm \'{args.alarm_name}\' exists in the region and profile and that your profile has correct credentials.")
        exit()
    
    # clear the properties that are unique to the source alarm or are state-based
    alarms['MetricAlarms'][0].pop('AlarmArn', None)
    alarms['MetricAlarms'][0].pop('AlarmConfigurationUpdatedTimestamp', None)
    alarms['MetricAlarms'][0].pop('StateValue', None)
    alarms['MetricAlarms'][0].pop('StateReason', None)
    alarms['MetricAlarms'][0].pop('StateReasonData', None)
    alarms['MetricAlarms'][0].pop('StateUpdatedTimestamp', None)

    
    if (args.event == "ok") or (args.event == "alarm-and-ok") or (args.event == "all"):
        lCurOKActions = alarms['MetricAlarms'][0]['OKActions']
        if (args.change == "add-alarm-action") or (args.change == "replace-alarm-action" and sCurrentActionArn in lCurOKActions):
            lCurOKActions.append(sNewActionArn)
        if (args.change == "remove-alarm-action") or (args.change == "replace-alarm-action"):
            if sCurrentActionArn in lCurOKActions:
                lCurOKActions.remove(sCurrentActionArn)
        print_verbose (f'OKActions will be set to: {lCurOKActions}')
    
    if (args.event == "alarm") or (args.event == "alarm-and-ok") or (args.event == "all"):
        lCurAlarmActions = alarms['MetricAlarms'][0]['AlarmActions']
        if (args.change == "add-alarm-action") or (args.change == "replace-alarm-action" and sCurrentActionArn in lCurAlarmActions):
            lCurAlarmActions.append(sNewActionArn)
        if (args.change == "remove-alarm-action") or (args.change == "replace-alarm-action"):
            if sCurrentActionArn in lCurAlarmActions:
                lCurAlarmActions.remove(sCurrentActionArn)
        print_verbose (f'AlarmActions will be set to: {lCurAlarmActions}')
    
    if (args.event == "insufficient-data") or (args.event == "all"):
        lCurInsufficientDataActions = alarms['MetricAlarms'][0]['InsufficientDataActions']
        if (args.change == "add-alarm-action") or (args.change == "replace-alarm-action" and sCurrentActionArn in lCurInsufficientDataActions):
            lCurInsufficientDataActions.append(sNewActionArn)
        if (args.change == "remove-alarm-action") or (args.change == "replace-alarm-action"):
            if sCurrentActionArn in lCurInsufficientDataActions:
                lCurInsufficientDataActions.remove(sCurrentActionArn)
        print_verbose (f'InsufficientDataActions will be set to: {lCurInsufficientDataActions}')
    
    
    print_verbose(f"About to attempt to put_metric_alarm with configuration as follows: {alarms['MetricAlarms'][0]}")
    
    # call put_metric_alarm
    result = client.put_metric_alarm(**alarms['MetricAlarms'][0])

    if result['ResponseMetadata']['HTTPStatusCode'] == 200:
        print (f"Successfully completed {args.change} for alarm actions '{args.event}' alarm '{args.alarm_name}'")
    else:
        print (f'Something went wrong and alarm \'{args.alarm_name}\' probably wasn\'t modified.')    


if __name__== "__main__":
    parser = argparse.ArgumentParser(description="Manipulate a cloudwatch alarm's actions")
    parser.add_argument('--change', required=True, choices=['add-alarm-action', 'replace-alarm-action', 'remove-alarm-action'], help='the change to perform on the cloudwatch alarm action')
    parser.add_argument('--event', required=True, choices=['alarm', 'ok', 'insufficient-data', 'alarm-and-ok', 'all'], help="the type of event")
    parser.add_argument('--alarm-name', required=True, help='the name of the cloudwatch alarm')
    parser.add_argument('--current-action-arn', help='the arn (string) of action to remove / replace')
    parser.add_argument('--new-action-arn', help='the new arn of the new action to add / replace with')
    parser.add_argument('--region', help='The AWS region name, e.g. eu-west-1')
    parser.add_argument('--profile', help="The AWS CLI profile to use, otherwise the default session defined by 'AWS configure' is used")
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    main(args)
