echo "Creating landing zone bucket '${INGESTION_BUCKET_NAME}'..."
aws s3 mb s3://${INGESTION_BUCKET_NAME} >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

echo "Creating processed zone bucket '${PROCESSED_BUCKET_NAME}'..."
aws s3 mb s3://${PROCESSED_BUCKET_NAME} >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

echo "Creating bucket code bucket '${CODE_BUCKET_NAME}'..."
aws s3 mb s3://${CODE_BUCKET_NAME} >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait