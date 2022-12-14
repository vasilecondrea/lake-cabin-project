
echo "Setting up the variables"

SUFFIX=141222
FUNCTION_NAME=ingestion-script-${SUFFIX}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account | tr -d '"')
AWS_REGION=us-east-1
CODE_BUCKET_NAME=code-bucket-${SUFFIX}
INGESTION_BUCKET=ingested-data-bucket-1


echo "create deployment package containing the test (python) function"

cd ../src/ingestion-folder/
zip ../../deployment/test-ingestion.zip test-ingestion.py 
cd ../../deployment

wait


echo "Uploading the deployment package"

aws s3 cp test-ingestion.zip s3://${CODE_BUCKET_NAME}/${FUNCTION_NAME}/test-ingestion.zip


wait

S3_READ_WRITE_JSON=$(jq --arg i_bucket "${INGESTION_BUCKET}" \
'.Statement[0].Resource[0] |= "arn:aws:s3:::" + $i_bucket + "/*"' templates/s3_ingestion_policy_template.json)


CLOUD_WATCH_JSON=$(jq --arg aws_id "${AWS_ACCOUNT_ID}" --arg func_name "${FUNCTION_NAME}" \
'.Statement[0].Resource |= "arn:aws:logs:us-east-1:" + $aws_id + ":*" | .Statement[1].Resource[0] |= "arn:aws:logs:us-east-1:" + $aws_id + ":log-group:/aws/lambda/" + $func_name + ":*"' templates/cloudwatch_log_policy_template.json)


echo 'Create IAM policies for cloudwatch and s3'

CLOUDWATCH_POLICY=$(aws iam create-policy --policy-name cloudwatch-policy-${FUNCTION_NAME} --policy-document "${CLOUD_WATCH_JSON}" | jq .Policy.Arn | tr -d '"')

S3_READ_WRITE_POLICY=$(aws iam create-policy --policy-name s3-policy-${FUNCTION_NAME} --policy-document "${S3_READ_WRITE_JSON}" | jq .Policy.Arn | tr -d '"')

wait 


echo 'Creating the IAM role'

IAM_ROLE=$(aws iam create-role --role-name ${FUNCTION_NAME}-role \
--assume-role-policy-document file://templates/trust.json | jq .Role.Arn | tr -d '"')

echo $IAM_ROLE

wait

echo 'Attaching policy to role'
S3_READ_WRITE_POLICY=arn:aws:iam::094362209857:policy/s3-policy-ingestion-script-141222

aws iam attach-role-policy --policy-arn ${CLOUDWATCH_POLICY} --role-name ${FUNCTION_NAME}-role
aws iam attach-role-policy --policy-arn ${S3_READ_WRITE_POLICY} --role-name ${FUNCTION_NAME}-role


echo 'Creating function'

EXECUTION_ROLE=arn:aws:iam::094362209857:role/ingestion-script-141222-role

FUNCTION=$(aws lambda create-function --function-name ${FUNCTION_NAME} --runtime python3.9 --role ${EXECUTION_ROLE} --package-type Zip --handler test-ingestion.ingestion_handler --code S3Bucket=${CODE_BUCKET_NAME},S3Key=${FUNCTION_NAME}/test-ingestion.zip)

wait

echo $FUNCTION