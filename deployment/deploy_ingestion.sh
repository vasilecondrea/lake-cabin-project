echo "Loading available resource variables from resource.json..."
SUFFIX=$(cat resources.json | jq .resource_suffix | tr -d '"')
S3_READ_WRITE_POLICY=$(cat resources.json | jq .s3_read_write_policy | tr -d '"')
CLOUDWATCH_POLICY=$(cat resources.json | jq .cloudwatch_log_policy | tr -d '"')
IAM_ROLE=$(cat resources.json | jq .iam_role | tr -d '"')
EVENTBRIDGE_RULE=$(cat resources.json | jq .eventbridge_rule | tr -d '"')
wait

echo "Setting up deployment variables..."
if [ $SUFFIX == null ] || [ $SUFFIX == "" ]; then
    SUFFIX=$(date +%d%m%y)
    RESOURCES_JSON=$(cat resources.json)
    jq --arg suffix "${SUFFIX}" '.resource_suffix |= $suffix' <<< $RESOURCES_JSON > resources.json
fi
FUNCTION_NAME=data-ingestion-${SUFFIX}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account | tr -d '"')
CODE_BUCKET_NAME=code-bucket-${SUFFIX}
INGESTION_BUCKET=ingested-data-bucket-1
wait

echo "Generating AWS secret for source database credentials..."
aws secretsmanager create-secret --name source-db-creds --secret-string file://db_creds_source.json
aws secretsmanager create-secret --name destination-db-creds --secret-string file://db_creds_destination.json
wait

echo "Creating bucket code bucket '${CODE_BUCKET_NAME}'..."
aws s3 mb s3://${CODE_BUCKET_NAME}
wait

echo "Creating function deployment package..."
cd ../src/ingestion-folder/
zip ../../deployment/test-ingestion.zip test-ingestion.py 
cd ../../deployment
wait

echo "Uploading the deployment package..."
aws s3 cp test-ingestion.zip s3://${CODE_BUCKET_NAME}/${FUNCTION_NAME}/test-ingestion.zip
wait

echo "Setting up s3 read/write policy template..."
S3_READ_WRITE_JSON=$(jq --arg i_bucket "${INGESTION_BUCKET}" \
'.Statement[0].Resource[0] |= "arn:aws:s3:::" + $i_bucket + "/*"' templates/s3_ingestion_policy_template.json)

echo "Setting up cloudwatch log policy template..."
CLOUD_WATCH_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${FUNCTION_NAME}" \
'.Statement[0].Resource |= "arn:aws:logs:us-east-1:" + $aws_id + ":*" | .Statement[1].Resource[0] |= "arn:aws:logs:us-east-1:" + $aws_id + ":log-group:/aws/lambda/" + $func_name + ":*"' templates/cloudwatch_log_policy_template.json)

if [ "$CLOUDWATCH_POLICY" == "" ] || [ "$CLOUDWATCH_POLICY" == null ]; then
    echo "Creating cloudwatch policy from template..."

    CLOUDWATCH_POLICY=$(aws iam create-policy --policy-name cloudwatch-ingestion-${SUFFIX} --policy-document "${CLOUD_WATCH_JSON}" | jq .Policy.Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${CLOUDWATCH_POLICY}" '.cloudwatch_log_policy |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "Cloudwatch policy already created, skipping..."
fi
wait

if [ "$S3_READ_WRITE_POLICY" == "" ] || [ "$S3_READ_WRITE_POLICY" == null ]; then
    echo "Creating s3 read/write policy from template..."
    
    S3_READ_WRITE_POLICY=$(aws iam create-policy --policy-name s3-ingestion-${SUFFIX} --policy-document "${S3_READ_WRITE_JSON}" | jq .Policy.Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${S3_READ_WRITE_POLICY}" '.s3_read_write_policy |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "S3 policy already created, skipping..."
fi
wait 

if [ "$IAM_ROLE" == "" ] || [ "$IAM_ROLE" == null ]; then
    echo "Creating IAM role to carry policies..."

    IAM_ROLE=$(aws iam create-role --role-name lambda-role-${SUFFIX} \
    --assume-role-policy-document file://templates/trust.json | jq .Role.Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${IAM_ROLE}" '.iam_role |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "IAM role already created, skipping..."
fi
wait

echo 'Attaching policies to IAM role...'
aws iam attach-role-policy --policy-arn ${CLOUDWATCH_POLICY} --role-name lambda-role-${SUFFIX}
aws iam attach-role-policy --policy-arn ${S3_READ_WRITE_POLICY} --role-name lambda-role-${SUFFIX}
wait

echo 'Creating lambda function...'
FUNCTION=$(aws lambda create-function --function-name ${FUNCTION_NAME} --runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler test-ingestion.ingestion_handler --code S3Bucket=${CODE_BUCKET_NAME},S3Key=${FUNCTION_NAME}/test-ingestion.zip)
wait

if [ "$EVENTBRIDGE_RULE" == "" ] || [ "$EVENTBRIDGE_RULE" == null ]; then
    echo "Creating eventbridge rule..."

    EVENTBRIDGE_RULE=$(aws events put-rule --name ingestion-rule-${SUFFIX} --schedule-expression "rate(5 minutes)" | jq .RuleArn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${EVENTBRIDGE_RULE}" '.eventbridge_rule |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "Eventbridge rule already created, skipping..."
fi
wait

echo "Giving permission to eventbridge rule to invoke lambda function..."
aws lambda add-permission --function-name ${FUNCTION_NAME} --principal events.amazonaws.com --statement-id eventbridge-invoke-${SUFFIX} --action "lambda:InvokeFunction" --source-arn ${EVENTBRIDGE_RULE} 
wait

TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${FUNCTION_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name' templates/eventbridge_targets.json)
echo "Adding lambda function as target for eventbridge rule..."
aws events put-targets --rule ingestion-rule-${SUFFIX} --targets "[${TARGET_JSON}]"