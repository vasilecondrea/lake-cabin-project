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

aws lambda update-function-code --function-name ${TRANSFORMATION_FUNCTION_NAME} \
--s3-bucket ${CODE_BUCKET_NAME} \
--s3-key ${TRANSFORMATION_FUNCTION_NAME}/transform.zip
wait