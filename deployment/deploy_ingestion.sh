echo "Setting up the variables"

SUFFIX=151222-7
FUNCTION_NAME=ingestion-script-${SUFFIX}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account | tr -d '"')
AWS_REGION=us-east-1
CODE_BUCKET_NAME=code-bucket-${SUFFIX}
INGESTION_BUCKET=ingested-data-bucket-1

# create variables for state file
echo "loading available from the resource variables from resource.json"

S3_READ_WRITE_POLICY=$(cat resources.json | jq .s3_read_write_policy | tr -d '"')
CLOUDWATCH_POLICY=$(cat resources.json | jq .cloudwatch_log_policy | tr -d '"')
IAM_ROLE=$(cat resources.json | jq .iam_role | tr -d '"')
EVENTBRIDGE_RULE=$(cat resources.json | jq .eventbridge_rule | tr -d '"')


echo "Creating bucket ${CODE_BUCKET_NAME}"

RESPONSE=$(aws s3 mb s3://${CODE_BUCKET_NAME})

wait

echo "create deployment package containing the test (python) function"

cd ../src/ingestion-folder/
zip ../../deployment/test-ingestion.zip test-ingestion.py 
cd ../../deployment

wait


echo "Uploading the deployment package"

aws s3 cp test-ingestion.zip s3://${CODE_BUCKET_NAME}/${FUNCTION_NAME}/test-ingestion.zip

wait

echo "Setting up policy templates"

S3_READ_WRITE_JSON=$(jq --arg i_bucket "${INGESTION_BUCKET}" \
'.Statement[0].Resource[0] |= "arn:aws:s3:::" + $i_bucket + "/*"' templates/s3_ingestion_policy_template.json)

CLOUD_WATCH_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${FUNCTION_NAME}" \
'.Statement[0].Resource |= "arn:aws:logs:us-east-1:" + $aws_id + ":*" | .Statement[1].Resource[0] |= "arn:aws:logs:us-east-1:" + $aws_id + ":log-group:/aws/lambda/" + $func_name + ":*"' templates/cloudwatch_log_policy_template.json)


echo 'Create IAM policies for cloudwatch and s3'


if [ "$CLOUDWATCH_POLICY" == "" ] || [ "$CLOUDWATCH_POLICY" == null ]; then
    echo "creating CLOUDWATCH_POLICY..."

    CLOUDWATCH_POLICY=$(aws iam create-policy --policy-name cloudwatch-policy-${FUNCTION_NAME} --policy-document "${CLOUD_WATCH_JSON}" | jq .Policy.Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${CLOUDWATCH_POLICY}" '.cloudwatch_log_policy |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "CLOUDWATCH__POLICY already exists, skipping..."
fi


if [ "$S3_READ_WRITE_POLICY" == "" ] || [ "$S3_READ_WRITE_POLICY" == null ]; then
    echo "creating S3_READ_WRITE_POLICY..."
    
    S3_READ_WRITE_POLICY=$(aws iam create-policy --policy-name s3-policy-${FUNCTION_NAME} --policy-document "${S3_READ_WRITE_JSON}" | jq .Policy.Arn | tr -d '"')


    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${S3_READ_WRITE_POLICY}" '.s3_read_write_policy |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "S3_READ_WRITE_POLICY already exists, skipping..."
fi

wait 


if [ "$IAM_ROLE" == "" ] || [ "$IAM_ROLE" == null ]; then
    echo "creating IAM_ROLE..."

    IAM_ROLE=$(aws iam create-role --role-name ${FUNCTION_NAME}-role \
    --assume-role-policy-document file://templates/trust.json | jq .Role.Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${IAM_ROLE}" '.iam_role |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "IAM_ROLE already exists, skipping..."
fi


echo 'Attaching policy to role'

aws iam attach-role-policy --policy-arn ${CLOUDWATCH_POLICY} --role-name ${FUNCTION_NAME}-role
aws iam attach-role-policy --policy-arn ${S3_READ_WRITE_POLICY} --role-name ${FUNCTION_NAME}-role

sleep 10

echo 'Creating function'


FUNCTION=$(aws lambda create-function --function-name ${FUNCTION_NAME} --runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler test-ingestion.ingestion_handler --code S3Bucket=${CODE_BUCKET_NAME},S3Key=${FUNCTION_NAME}/test-ingestion.zip)

wait


if [ "$EVENTBRIDGE_RULE" == "" ] || [ "$EVENTBRIDGE_RULE" == null ]; then
    echo "creating EVENTBRIDGE_RULE..."

    EVENTBRIDGE_RULE=$(aws events put-rule --name ${FUNCTION_NAME}-rule --schedule-expression "rate(5 minutes)" | jq .RuleArn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${EVENTBRIDGE_RULE}" '.eventbridge_rule |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "EVENTBRIDGE_RULE already exists, skipping..."
fi

wait

echo "Adding Eventbridge permissions to Lambda"

aws lambda add-permission --function-name ${FUNCTION_NAME} --principal events.amazonaws.com --statement-id eventbridgeInvokeLambda --action "lambda:InvokeFunction" --source-arn ${EVENTBRIDGE_RULE} 

wait

TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${FUNCTION_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name' templates/eventbridge_targets.json)

echo "Adding Lambda as target for Eventbridge rule"

aws events put-targets --rule ${FUNCTION_NAME}-rule --targets "[${TARGET_JSON}]"