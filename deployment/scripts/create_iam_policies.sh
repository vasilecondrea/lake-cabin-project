echo "Setting up s3 read/write policy template..."
S3_READ_WRITE_JSON=$(jq --arg i_bucket "arn:aws:s3:::${INGESTION_BUCKET_NAME}/*" \
'.Statement[0].Resource = [$i_bucket]' templates/s3_ingestion_policy_template.json |\
jq --arg p_bucket "arn:aws:s3:::${PROCESSED_BUCKET_NAME}/*" '.Statement[0].Resource += [$p_bucket]' | jq --arg i_buck "arn:aws:s3:::${INGESTION_BUCKET_NAME}" '.Statement[0].Resource += [$i_buck]' | jq --arg p_buck "arn:aws:s3:::${PROCESSED_BUCKET_NAME}" '.Statement[0].Resource += [$p_buck]')

if [ "$S3_READ_WRITE_POLICY" == "" ] || [ "$S3_READ_WRITE_POLICY" == null ]; then
    echo "Creating s3 read/write policy from template..."
    
    S3_READ_WRITE_POLICY=$(aws iam create-policy --policy-name s3-ingestion-${SUFFIX} --policy-document "${S3_READ_WRITE_JSON}" | jq .Policy.Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${S3_READ_WRITE_POLICY}" '.s3_read_write_policy |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "S3 policy already created, skipping..."
fi
wait 

aws iam attach-role-policy --policy-arn ${S3_READ_WRITE_POLICY} --role-name lambda-role-${SUFFIX}


echo "Setting up cloudwatch log policy template..."
CLOUD_WATCH_JSON=$(jq \
--arg aws_id "${AWS_ACCOUNT_ID}" \
--arg ingest_func_name "${FUNCTION_NAME}" \
--arg transform_func_name "${TRANSFORMATION_FUNCTION_NAME}" \
--arg load_func_name "${LOAD_FUNCTION_NAME}" \
--arg source_secret_arn "${SOURCE_DB_CREDS}" \
--arg destination_secret_arn "${DESTINATION_DB_CREDS}" \
'.Statement[0].Resource |= "arn:aws:logs:us-east-1:" + $aws_id + ":*" | .Statement[1].Resource[0] |= "arn:aws:logs:us-east-1:" + $aws_id + ":log-group:/aws/lambda/" + $ingest_func_name + ":*" | .Statement[1].Resource[1] |= "arn:aws:logs:us-east-1:" + $aws_id + ":log-group:/aws/lambda/" + $transform_func_name + ":*" | .Statement[1].Resource[2] |= "arn:aws:logs:us-east-1:" + $aws_id + ":log-group:/aws/lambda/" + $load_func_name + ":*" | .Statement[2].Resource[0] |= $source_secret_arn | .Statement[2].Resource[1] |= $destination_secret_arn | .Statement[3].Resource |= "arn:aws:logs:us-east-1:" + $aws_id + ":log-group:*"' templates/cloudwatch_log_policy_template.json)

if [ "$CLOUDWATCH_POLICY" == "" ] || [ "$CLOUDWATCH_POLICY" == null ]; then
    echo "Creating cloudwatch policy from template..."

    CLOUDWATCH_POLICY=$(aws iam create-policy --policy-name cloudwatch-ingestion-${SUFFIX} --policy-document "${CLOUD_WATCH_JSON}" | jq .Policy.Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${CLOUDWATCH_POLICY}" '.cloudwatch_log_policy |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "Cloudwatch policy already created, skipping..."
fi
wait

aws iam attach-role-policy --policy-arn ${CLOUDWATCH_POLICY} --role-name lambda-role-${SUFFIX}
