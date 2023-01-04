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

aws lambda update-function-code --function-name ${LOAD_FUNCTION_NAME} \
--s3-bucket ${CODE_BUCKET_NAME} \
--s3-key ${LOAD_FUNCTION_NAME}/load.zip
wait