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

aws lambda update-function-code --function-name ${TRANSFORMATION_FUNCTION_NAME} \
--s3-bucket ${CODE_BUCKET_NAME} \
--s3-key ${TRANSFORMATION_FUNCTION_NAME}/transformation.zip
wait