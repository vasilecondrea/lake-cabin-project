# INGESTION LAMBDA FUNCTION
echo "Creating ingestion deployment package..."
cd ../extract/src/package
zip --q -r ../extract.zip .
cd ../
zip --q extract.zip extract.py
cd ../../deployment
wait

echo "Uploading ingestion deployment package..."
aws s3 cp ../extract/src/extract.zip s3://${CODE_BUCKET_NAME}/${FUNCTION_NAME}/extract.zip >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

rm ../extract/src/extract.zip

echo 'Creating ingestion lambda function...'
FUNCTION=$(aws lambda create-function \
--function-name ${FUNCTION_NAME} \
--runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler extract.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${FUNCTION_NAME}/extract.zip \
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
cd ../transform/src/package 
zip --q -r ../transform.zip .
cd ../
zip --q transform.zip transform_helper.py transform.py transform_retrieve.py transform_tables.py transform_upload.py currency-symbols.json
cd ../../deployment
wait

echo "Uploading transformation deployment package..."
aws s3 cp ../transform/src/transform.zip s3://${CODE_BUCKET_NAME}/${TRANSFORMATION_FUNCTION_NAME}/transform.zip >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

rm ../transform/src/transform.zip

echo 'Creating transformation lambda function...'
FUNCTION=$(aws lambda create-function \
--function-name ${TRANSFORMATION_FUNCTION_NAME} \
--runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler transform.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${TRANSFORMATION_FUNCTION_NAME}/transform.zip \
--timeout 30)
wait

echo "Giving permission to eventbridge rule to invoke transformation lambda function..."
aws lambda add-permission --function-name ${TRANSFORMATION_FUNCTION_NAME} --principal events.amazonaws.com --statement-id eventbridge-invoke-${SUFFIX} --action "lambda:InvokeFunction" --source-arn ${TRANSFORMATION_RULE} >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

echo "Creating eventbridge target from template..."
TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${TRANSFORMATION_FUNCTION_NAME}" --arg ingest_bucket "${INGESTION_BUCKET_NAME}" --arg process_bucket "${PROCESSED_BUCKET_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name | .Input = "{\"ingested_bucket\":" + "\"" + $ingest_bucket + "\"" + ", \"processed_bucket\":" + "\"" + $process_bucket + "\"" + "}"' templates/eventbridge_targets.json)

echo "Adding lambda function as target for eventbridge rule..."
aws events put-targets --rule transformation-rule-${SUFFIX} --targets "[${TARGET_JSON}]" >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

# LOAD LAMBDA FUNCTION
echo "Creating load function deployment package..."
cd ../load/src/package
zip --q -r ../load.zip .
cd ../
zip --q load.zip load.py
cd ../../deployment
wait

echo "Uploading load deployment package..."
aws s3 cp ../load/src/load.zip s3://${CODE_BUCKET_NAME}/${LOAD_FUNCTION_NAME}/load.zip >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

rm ../load/src/load.zip

echo 'Creating load lambda function...'
FUNCTION=$(aws lambda create-function \
--function-name ${LOAD_FUNCTION_NAME} \
--runtime python3.9 --role ${IAM_ROLE} --package-type Zip --handler load.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${LOAD_FUNCTION_NAME}/load.zip \
--timeout 30)
wait

echo "Giving permission to eventbridge rule to invoke load lambda function..."
aws lambda add-permission --function-name ${LOAD_FUNCTION_NAME} --principal events.amazonaws.com --statement-id eventbridge-invoke-${SUFFIX} --action "lambda:InvokeFunction" --source-arn ${LOAD_RULE} >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

echo "Creating eventbridge target from template..."
TARGET_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${LOAD_FUNCTION_NAME}" --arg ingest_bucket "${INGESTION_BUCKET_NAME}" --arg process_bucket "${PROCESSED_BUCKET_NAME}" '.Arn |= "arn:aws:lambda:us-east-1:" + $aws_id + ":function:" + $func_name | .Input = "{\"ingested_bucket\":" + "\"" + $ingest_bucket + "\"" + ", \"processed_bucket\":" + "\"" + $process_bucket + "\"" + "}"' templates/eventbridge_targets.json)

echo "Adding lambda function as target for eventbridge rule..."
aws events put-targets --rule load-rule-${SUFFIX} --targets "[${TARGET_JSON}]" >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait