#!/usr/bin/python

# Manipulate a cloudwatch alarm and optionally set/modify specified properties.
#
# Actions available are:
#   Update: update and change specified properties of an existing alarm
#   Copy: copy an existing alarm and optionally change specified properties 
#   Recreate: because you can't rename an alarm directly - basically a copy and delete 
#
# Run the script with --help to see syntax
#
# IMPORTANT TO NOTE WHEN MODIFYING ANY ALARM PROPERTIES: AWS will often accept invalid values as alarm parameters that would not be allowed via the GUI, for example 
# AWS will accept a Period of 600 seconds even though the AWS console only permits 5 or 15 minutes (300 or 900 seconds).  In these cases the alarms may never function 
# correctly and remain in 'Insufficient Data' status indefinitely.
#
# Potential improvements: check the destination/new alarm doesn't already exist 

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
    if (args.action == "update") and (args.new_name):
        print ("Error:  You specified a new name for an update action.  You cannot rename an alarm using the update method.  Please use the recreate method instead.")
        exit()

    if (args.action in ["copy","recreate"]) and not (args.new_name):
        print ("Error:  You did not include the new alarm name for an alarm copy or recreate action.")
        exit()

    if (args.action in ["copy","recreate"]) and (args.new_name == args.alarm_name):
        print ("Error:  Your current and new alarm names are the same.  Maybe you want to use the update action instead?")
        exit()

    if args.action in ["copy","recreate"]:
        sPutAlarmName = args.new_name
    else:
        sPutAlarmName = args.alarm_name
    
    # create boto client
    if args.profile:
        boto3.setup_default_session(profile_name = args.profile)

    if args.region:
        client = boto3.client('cloudwatch', region_name = args.region)
    else:
        client = boto3.client('cloudwatch')
   
    # describe alarm pre-change 
    try:
        alarms = client.describe_alarms(AlarmNames=[args.alarm_name])
    except: 
        print (f"Error:  Couldn't find an alarm named '{args.alarm_name}'")
        exit()

    if (len(alarms['MetricAlarms'])) < 1:
        print (f"Error:  describe-alarms did not return a valid dictionary.  Check the alarm \'{args.alarm_name}\' exists in the region and profile and that your profile has correct credentials.")
        exit()
    
    # clear the properties that are unique to the source alarm or are state-based
    alarms['MetricAlarms'][0].pop('AlarmName', None)
    alarms['MetricAlarms'][0].pop('AlarmArn', None)
    alarms['MetricAlarms'][0].pop('AlarmConfigurationUpdatedTimestamp', None)
    alarms['MetricAlarms'][0].pop('StateValue', None)
    alarms['MetricAlarms'][0].pop('StateReason', None)
    alarms['MetricAlarms'][0].pop('StateReasonData', None)
    alarms['MetricAlarms'][0].pop('StateUpdatedTimestamp', None)

    # specify the destination alarm name
    alarms['MetricAlarms'][0]['AlarmName'] = sPutAlarmName
    
    # validate the specified key-value pairs and modify the dictionary as required
    if args.set:
        for setkeyval in args.set:
            setkey = setkeyval[:setkeyval.find("=")]
            setvalue = setkeyval[setkeyval.find("=")+1:]
            if setvalue.isnumeric():
                setvalue = int(setvalue)
            else:
                try:
                    setvalue = float(setvalue)
                except ValueError:
                    pass
            if (not setkey): 
                print ("Invalid key=value pair. Ensure there are no spaces between the key, the equals sign, and the value.")
                exit()
            if setkey.lower() in ["alarmname", "alarmarn"]:
                print (setkey + " can't be modified this way.  If you are trying to change the name of an alarm use the Recreate action.")
                exit()
            if not alarms["MetricAlarms"][0].get(setkey):
                print (f"Warning: Key \'{setkey}\' was not found in the current alarm dict.  Key names are case sensitive.  This might not be an issue if you are setting a property that wasn't previously set.")
            if (setvalue[:1] == '[') and (setvalue[-1:] == ']'): # convert string lists to actual lists 
                setlist = list(map(str.strip, setvalue.strip('][').split(',')))
                alarms["MetricAlarms"][0][setkey] = setlist 
            else: 
                alarms["MetricAlarms"][0][setkey] = setvalue
            print_verbose(f"Key '{setkey}' will be given new value '{setvalue}'")
    
    
    print_verbose(f"About to attempt to put_metric_alarm with configuration as follows: {alarms['MetricAlarms'][0]}")
    
    # call put_metric_alarm
    result = client.put_metric_alarm(**alarms['MetricAlarms'][0])

    if result['ResponseMetadata']['HTTPStatusCode'] == 200:
        print (f"Successfully completed {args.action} for alarm '{sPutAlarmName}'")
        if args.action == 'recreate':
            result = client.delete_alarms(AlarmNames=[args.alarm_name])
            if result['ResponseMetadata']['HTTPStatusCode'] == 200:
                print (f'Alarm \'{args.alarm_name}\' successfully deleted')
            else:
                print (f'Something went wrong and alarm \'{args.alarm_name}\' probably wasn\'t deleted')
    else:
        print (f'Something went wrong and alarm \'{sAlarmName}\' probably wasn\'t updated/copied.')    


if __name__== "__main__":
    parser = argparse.ArgumentParser(description="Manipulate a cloudwatch alarm and optionally set/modify specified properties.")
    parser.add_argument('--action', required=True, choices=['update', 'copy', 'recreate'], help='the action to perform on the cloudwatch alarm')
    parser.add_argument('--alarm-name', required=True, help='the name of the cloudwatch alarm')
    parser.add_argument('--new-name', help='the new name for the alarm - required for copy and recreate actions')
    parser.add_argument('--set', nargs='*', metavar="KEY=VALUE", help='List of properties to set (update) in format keyname=value e.g. AlarmDescription="fred loves cheese".  \
        Make sure there are no spaces around the = sign.  Note that the keyname should be in JSON format returned by \'aws cloudwatch describe-alarms\' not in AWS CLI input format, \
        e.g. \'InsufficientDataActions\' not \'insufficient-data-actions\'')
    parser.add_argument('--region', help='The AWS region name, e.g. eu-west-1')
    parser.add_argument('--profile', help="The AWS CLI profile to use, otherwise the default session defined by 'AWS configure' is used")
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    main(args)

