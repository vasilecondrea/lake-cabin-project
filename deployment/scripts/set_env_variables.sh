echo "Loading available resource variables from resource.json..."
# opens resources.json file and retrieves any stored resource ARNs
# if key does not exist, value will be set to null and variable will be created
# when relevant resources are created later on

SUFFIX=$(cat resources.json | jq .resource_suffix | tr -d '"')
S3_READ_WRITE_POLICY=$(cat resources.json | jq .s3_read_write_policy | tr -d '"')
CLOUDWATCH_POLICY=$(cat resources.json | jq .cloudwatch_log_policy | tr -d '"')
IAM_ROLE=$(cat resources.json | jq .iam_role | tr -d '"')
INGESTION_RULE=$(cat resources.json | jq .ingestion_rule | tr -d '"')
TRANSFORMATION_RULE=$(cat resources.json | jq .transformation_rule | tr -d '"')
LOAD_RULE=$(cat resources.json | jq .load_rule | tr -d '"')
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
TRANSFORMATION_FUNCTION_NAME=data-transformation-${SUFFIX}
LOAD_FUNCTION_NAME=data-load-${SUFFIX}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account | tr -d '"')
INGESTION_BUCKET_NAME=ingestion-bucket-${SUFFIX}
PROCESSED_BUCKET_NAME=processed-bucket-${SUFFIX}
CODE_BUCKET_NAME=code-bucket-${SUFFIX}
LOG_PATH=logs
wait