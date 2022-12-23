# INGESTION LAMBDA FUNCTION
echo "Creating ingestion deployment package..."
cd src/ingestion-folder/package
zip --q -r ../../../test-ingestion.zip .
cd ../
zip --q ../../test-ingestion.zip function.py
cd ../../
wait

echo "Uploading ingestion deployment package..."
aws s3 cp test-ingestion.zip s3://${CODE_BUCKET_NAME}/${FUNCTION_NAME}/test-ingestion.zip >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

echo 'Creating ingestion lambda function...'
FUNCTION=$(aws lambda create-function \
--function-name ${FUNCTION_NAME} \
--runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler function.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${FUNCTION_NAME}/test-ingestion.zip \
--timeout 30)
wait

echo "Giving permission to eventbridge rule to invoke ingestion lambda function..."
aws lambda add-permission --function-name ${FUNCTION_NAME} --principal events.amazonaws.com --statement-id eventbridge-invoke-${SUFFIX} --action "lambda:InvokeFunction" --source-arn ${INGESTION_RULE} >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

echo "Creating eventbridge target from template..."
TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${FUNCTION_NAME}" --arg ingest_bucket "${INGESTION_BUCKET_NAME}" --arg process_bucket "${PROCESSED_BUCKET_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name | .Input = "{\"ingested_bucket\":" + "\"" + $ingest_bucket + "\"" + ", \"processed_bucket\":" + "\"" + $process_bucket + "\"" + "}"' templates/eventbridge_targets.json)

echo "Adding lambda function as target for eventbridge rule..."
aws events put-targets --rule ingestion-rule-${SUFFIX} --targets "[${TARGET_JSON}]" >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

# TRANSFORMATION LAMBDA FUNCTION
echo "Creating transformation function deployment package..."
cd ../Data_Manipulation/src/data_transformation_code/package 
zip --q -r ../transformation.zip .
cd ../
zip --q transformation.zip transformation.py currency-symbols.json
cd ../../../deployment
wait

echo "Uploading transformation deployment package..."
aws s3 cp ../Data_Manipulation/src/data_transformation_code/transformation.zip s3://${CODE_BUCKET_NAME}/${TRANSFORMATION_FUNCTION_NAME}/transformation.zip >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

echo 'Creating transformation lambda function...'
FUNCTION=$(aws lambda create-function \
--function-name ${TRANSFORMATION_FUNCTION_NAME} \
--runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler transformation.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${TRANSFORMATION_FUNCTION_NAME}/transformation.zip \
--timeout 30)
wait

echo "Creating eventbridge target from template..."
TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${TRANSFORMATION_FUNCTION_NAME}" --arg ingest_bucket "${INGESTION_BUCKET_NAME}" --arg process_bucket "${PROCESSED_BUCKET_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name | .Input = "{\"ingested_bucket\":" + "\"" + $ingest_bucket + "\"" + ", \"processed_bucket\":" + "\"" + $process_bucket + "\"" + "}"' templates/eventbridge_targets.json)

echo "Adding lambda function as target for eventbridge rule..."
aws events put-targets --rule transformation-rule-${SUFFIX} --targets "[${TARGET_JSON}]" >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

# LOAD LAMBDA FUNCTION
echo "Creating load function deployment package..."
mkdir -p ../OLAP_load/package
cd ../OLAP_load/package
zip --q -r ../load.zip .
cd ../
zip --q load.zip load.py
cd ../deployment
wait

echo "Uploading load deployment package..."
aws s3 cp ../OLAP_load/load.zip s3://${CODE_BUCKET_NAME}/${LOAD_FUNCTION_NAME}/load.zip >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

echo 'Creating load lambda function...'
FUNCTION=$(aws lambda create-function \
--function-name ${LOAD_FUNCTION_NAME} \
--runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler load.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${LOAD_FUNCTION_NAME}/load.zip \
--timeout 30)
wait

echo "Creating eventbridge target from template..."
TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${LOAD_FUNCTION_NAME}" --arg ingest_bucket "${INGESTION_BUCKET_NAME}" --arg process_bucket "${PROCESSED_BUCKET_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name | .Input = "{\"ingested_bucket\":" + "\"" + $ingest_bucket + "\"" + ", \"processed_bucket\":" + "\"" + $process_bucket + "\"" + "}"' templates/eventbridge_targets.json)

echo "Adding lambda function as target for eventbridge rule..."
aws events put-targets --rule load-rule-${SUFFIX} --targets "[${TARGET_JSON}]" >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait