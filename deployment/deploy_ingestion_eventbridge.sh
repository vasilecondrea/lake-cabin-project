SUFFIX=141222
FUNCTION_NAME=ingestion-script-${SUFFIX}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account | tr -d '"')
AWS_REGION=us-east-1

# EVENTBRIDGE_RULE=$(aws events put-rule --name ${FUNCTION_NAME}-rule --schedule-expression "rate(5 minutes)" | jq .RuleArn | tr -d '"')

EVENTBRIDGE_RULE=arn:aws:events:us-east-1:094362209857:rule/ingestion-script-141222-rule

# aws lambda add-permission --function-name ${FUNCTION_NAME} --principal events.amazonaws.com --statement-id eventbridgeInvokeLambda --action "lambda:InvokeFunction" --source-arn ${EVENTBRIDGE_RULE} 

TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${FUNCTION_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name' templates/eventbridge_targets.json)

aws events put-targets --rule ${FUNCTION_NAME}-rule --targets "[${TARGET_JSON}]"
 
 echo $TARGET_JSON