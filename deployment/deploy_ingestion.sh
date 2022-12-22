set -e
set -u

echo "Loading available resource variables from resource.json..."
# opens resources.json file and retrieves any stored resource ARNs
# if key does not exist, value will be set to null and variable will be created
# when relevant resources are created later on

SUFFIX=$(cat resources.json | jq .resource_suffix | tr -d '"')
S3_READ_WRITE_POLICY=$(cat resources.json | jq .s3_read_write_policy | tr -d '"')
CLOUDWATCH_POLICY=$(cat resources.json | jq .cloudwatch_log_policy | tr -d '"')
IAM_ROLE=$(cat resources.json | jq .iam_role | tr -d '"')
EVENTBRIDGE_RULE=$(cat resources.json | jq .eventbridge_rule | tr -d '"')
SOURCE_DB_CREDS=$(cat resources.json | jq .source_db_creds | tr -d '"')
DESTINATION_DB_CREDS=$(cat resources.json | jq .destination_db_creds | tr -d '"')
wait

echo "Setting up deployment variables..."
# checks if SUFFIX variable has been retrieved from resources.json
# if not (when SUFFIX is null or "") then it generates a suffix
# based off the current date's 6 digit date code

if [ $SUFFIX == null ] || [ $SUFFIX == "" ]; then
    SUFFIX=$(date +%d%m%y)
    RESOURCES_JSON=$(cat resources.json)
    jq --arg suffix "${SUFFIX}" '.resource_suffix |= $suffix' <<< $RESOURCES_JSON > resources.json
fi

FUNCTION_NAME=data-ingestion-${SUFFIX}
TRANSFORMATION_FUNCTION_NAME=transformation-${SUFFIX}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account | tr -d '"')
INGESTION_BUCKET_NAME=ingestion-bucket-${SUFFIX}
PROCESSED_BUCKET_NAME=processed-bucket-${SUFFIX}
CODE_BUCKET_NAME=code-bucket-${SUFFIX}
wait

# checks whether AWS source database credentials have already been retrieved 
# from resources.json, if not (SOURCE_DB_CREDS is null or "") then credentials
# are loaded from the relevant .json file and secret created using contents
if [ "$SOURCE_DB_CREDS" == "" ] || [ "$SOURCE_DB_CREDS" == null ]; then
    echo "Generating AWS secret for source database credentials..."

    SOURCE_DB_CREDS=$(aws secretsmanager create-secret --name db-creds-source --secret-string file://db_creds_source.json | jq .Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg source_creds "${SOURCE_DB_CREDS}" '.source_db_creds |= $source_creds' <<< $RESOURCES_JSON > resources.json
else
    echo "AWS source database credentials already generated, skipping..."
fi
wait


# checks whether AWS destination database credentials have already been retrieved 
# from resources.json, if not (DESTINATION_DB_CREDS is null or "") then credentials
# are loaded from the relevant .json file and secret created using contents
if [ "$DESTINATION_DB_CREDS" == "" ] || [ "$DESTINATION_DB_CREDS" == null ]; then
    echo "Generating AWS secret for destination database credentials..."

    DESTINATION_DB_CREDS=$(aws secretsmanager create-secret --name db-creds-destination --secret-string file://db_creds_destination.json | jq .Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg destination_creds "${SOURCE_DB_CREDS}" '.destination_db_creds |= $destination_creds' <<< $RESOURCES_JSON > resources.json
else
    echo "AWS destination database credentials already generated, skipping..."
fi
wait

echo "Creating landing zone bucket '${INGESTION_BUCKET_NAME}'..."
aws s3 mb s3://${INGESTION_BUCKET_NAME} >> deployment-log-${SUFFIX}.out
wait

echo "Creating processed zone bucket '${PROCESSED_BUCKET_NAME}'..."
aws s3 mb s3://${PROCESSED_BUCKET_NAME} >> deployment-log-${SUFFIX}.out
wait

echo "Creating bucket code bucket '${CODE_BUCKET_NAME}'..."
aws s3 mb s3://${CODE_BUCKET_NAME} >> deployment-log-${SUFFIX}.out
wait

echo "Creating function deployment package..."
cd src/ingestion-folder/
zip ../../test-ingestion.zip function.py >> deployment-log-${SUFFIX}.out
cd ../../
wait

# --------------------------------
echo "Creating transformation function deployment package..."
# cd ../Data_Manipulation/src/data_transformation_code/package
# zip -r ../../../deployment/transformation.zip . >> deployment-log-${SUFFIX}.out
# cd ../
# zip -r transformation.zip transformation.py
# cd ../../../deployment
# zip transformation.zip transformation.py
cd ../Data_Manipulation/src/data_transformation_code/package 
zip -r ../transformation.zip . >> deployment-log-${SUFFIX}.out
cd ../
zip transformation.zip transformation.py currency-symbols.json
cd ../../../deployment
wait

echo "Uploading the deployment package..."
aws s3 cp test-ingestion.zip s3://${CODE_BUCKET_NAME}/${FUNCTION_NAME}/test-ingestion.zip >> deployment-log-${SUFFIX}.out
wait

# --------------------------------
echo "Uploading transformation deployment package..."
aws s3 cp ../Data_Manipulation/src/data_transformation_code/transformation.zip s3://${CODE_BUCKET_NAME}/${TRANSFORMATION_FUNCTION_NAME}/transformation.zip >> deployment-log-${SUFFIX}.out
wait

echo "Setting up s3 read/write policy template..."
S3_READ_WRITE_JSON=$(jq --arg i_bucket "arn:aws:s3:::${INGESTION_BUCKET_NAME}/*" \
'.Statement[0].Resource = [$i_bucket]' templates/s3_ingestion_policy_template.json |\
jq --arg p_bucket "arn:aws:s3:::${PROCESSED_BUCKET_NAME}/*" '.Statement[0].Resource += [$p_bucket]' | jq --arg i_buck "arn:aws:s3:::${INGESTION_BUCKET_NAME}" '.Statement[0].Resource += [$i_buck]' | jq --arg p_buck "arn:aws:s3:::${PROCESSED_BUCKET_NAME}" '.Statement[0].Resource += [$p_buck]')

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
sleep 10

echo 'Attaching policies to IAM role...'
aws iam attach-role-policy --policy-arn ${CLOUDWATCH_POLICY} --role-name lambda-role-${SUFFIX}
aws iam attach-role-policy --policy-arn ${S3_READ_WRITE_POLICY} --role-name lambda-role-${SUFFIX}
wait

echo 'Creating lambda function...'
FUNCTION=$(aws lambda create-function --function-name ${FUNCTION_NAME} \
--runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler function.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${FUNCTION_NAME}/test-ingestion.zip)
wait

# ---------------------------------
echo 'Creating transformation lambda function...'
FUNCTION=$(aws lambda create-function --function-name ${TRANSFORMATION_FUNCTION_NAME} \
--runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler transformation.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${TRANSFORMATION_FUNCTION_NAME}/transformation.zip)
wait

if [ "$EVENTBRIDGE_RULE" == "" ] || [ "$EVENTBRIDGE_RULE" == null ]; then
    echo "Creating eventbridge rule..."

    EVENTBRIDGE_RULE=$(aws events put-rule --name ingestion-rule-${SUFFIX} --schedule-expression "rate(5 minutes)" | jq .RuleArn | tr -d '"')
    
    TRANSFORMATION_EVENTBRIDGE_RULE=$(aws events put-rule --name transformation-rule-${SUFFIX} --schedule-expression "rate(5 minutes)" | jq .RuleArn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${EVENTBRIDGE_RULE}" '.eventbridge_rule |= $policy' <<< $RESOURCES_JSON > resources.json
    jq --arg policy "${TRANSFORMATION_EVENTBRIDGE_RULE}" '.transformation_eventbridge_rule |= $policy' <<< $RESOURCES_JSON > resources.json
    
    # ALT COMMAND jq --arg ingestion-policy "${EVENTBRIDGE_RULE}" --arg transformation-policy "${TRANSFORMATION_EVENTBRIDGE_RULE}" '.eventbridge_rule |= {"ingestion_rule":$policy,"transformation_rule":$policy_two}' resources.json 
else
    echo "Eventbridge rule already created, skipping..."
fi
wait

echo "Giving permission to eventbridge rule to invoke lambda function..."
aws lambda add-permission --function-name ${FUNCTION_NAME} --principal events.amazonaws.com --statement-id eventbridge-invoke-${SUFFIX} --action "lambda:InvokeFunction" --source-arn ${EVENTBRIDGE_RULE} >> deployment-log-${SUFFIX}.out
wait

aws lambda add-permission --function-name ${TRANSFORMATION_FUNCTION_NAME} --principal events.amazonaws.com --statement-id eventbridge-invoke-${SUFFIX} --action "lambda:InvokeFunction" --source-arn ${TRANSFORMATION_EVENTBRIDGE_RULE} >> deployment-log-${SUFFIX}.out
wait

TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${FUNCTION_NAME}" --arg ingest_bucket "${INGESTION_BUCKET_NAME}" --arg process_bucket "${PROCESSED_BUCKET_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name | .Input = "{\"ingested_bucket\":" + "\"" + $ingest_bucket + "\"" + ", \"processed_bucket\":" + "\"" + $process_bucket + "\"" + "}"' templates/eventbridge_targets.json)

# currently overwrites eventbridge_target.json
TRANSFORMATION_TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${TRANSFORMATION_FUNCTION_NAME}" --arg ingest_bucket "${INGESTION_BUCKET_NAME}" --arg process_bucket "${PROCESSED_BUCKET_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name | .Input = "{\"ingested_bucket\":" + "\"" + $ingest_bucket + "\"" + ", \"processed_bucket\":" + "\"" + $process_bucket + "\"" + "}"' templates/eventbridge_targets.json)

# ALT TARGET JSON  --arg transformation_func_name "${TRANSFORMATION_FUNCTION_NAME}" .... Arn |= "{\"ingestion_arn\":" + \"arn:aws:lambda:us-east-1:\" + "\"" + $aws_id + "\"" + \":function:\" + "\"" + $func_name + "\"" ", \"transformation_arn:\" + \"arn:aws:lambda:us-east-1:\" + "\"" + $aws_id + "\"" + \":function:\" + "\"" + $transformation_func_name + "\"" + "}"


echo "Adding lambda function as target for eventbridge rule..."
aws events put-targets --rule ingestion-rule-${SUFFIX} --targets "[${TARGET_JSON}]" >> deployment-log-${SUFFIX}.out

aws events put-targets --rule transformation-rule-${SUFFIX} --targets "[${TRANSFORMATION_TARGET_JSON}]" >> deployment-log-${SUFFIX}.out

set +e
set +u