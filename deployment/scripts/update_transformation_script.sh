echo "Creating transformation function deployment package..."
cd ../transformation/src/data_transformation_code/package 
zip --q -r ../transformation.zip .
cd ../
zip --q transformation.zip transformation_helper.py transformation_lambda.py transformation_retrieve.py transformation_tables.py transformation_upload.py currency-symbols.json
cd ../../../deployment
wait

echo "Uploading transformation deployment package..."
aws s3 cp ../transformation/src/data_transformation_code/transformation.zip s3://${CODE_BUCKET_NAME}/${TRANSFORMATION_FUNCTION_NAME}/transformation.zip >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

aws lambda update-function-code --function-name ${TRANSFORMATION_FUNCTION_NAME} \
--s3-bucket ${CODE_BUCKET_NAME} \
--s3-key ${TRANSFORMATION_FUNCTION_NAME}/transformation.zip
wait