echo "Creating updated load function deployment package..."
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

aws lambda update-function-code --function-name ${LOAD_FUNCTION_NAME} \
--s3-bucket ${CODE_BUCKET_NAME} \
--s3-key ${LOAD_FUNCTION_NAME}/load.zip
wait