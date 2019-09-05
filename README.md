# aws-cloudwatch-tools
Some tools for streamlining working with AWS Cloudwatch alarms to augment the AWS CLI

## cw-alarm-helper.py
Update, Copy, or Recreate a cloudwatch alarm - doing this natively with the CLI with put-metric-alarm is extremely long winded due to the need to pass in every single parameter even if you only want to change one, or else temporarily dump the config to Json, edit and pass it back in.  This tool essentially automates the second option (but using boto3 rather than CLI) so you only have to pass the parameters that you want to change.

## cw-alarm-action-helper.py
Add, Replace or Remove a Cloudwatch alarm action by specifying an action ARN to add and/or remove.  Uses boto3.

## cw-show-alarm-sns-actions.py
Display all SNS actions associated with Cloudwatch alarms in a linear, CSV-style format.  Wraps around CLI (needs a re-write to use boto3).
