echo "Creating load function deployment package..."
cd ../extract/src/package
zip --q -r ../extract.zip .
cd ../
zip --q extract.zip extract.py
cd ../../deployment
wait

echo "Uploading load deployment package..."
aws s3 cp ../extract/src/extract.zip s3://${CODE_BUCKET_NAME}/${FUNCTION_NAME}/extract.zip >> $LOG_PATH/deployment_log_${SUFFIX}.out
wait

rm ../extract/src/extract.zip

aws lambda update-function-code --function-name ${FUNCTION_NAME} \
--s3-bucket ${CODE_BUCKET_NAME} \
--s3-key ${FUNCTION_NAME}/extract.zip
wait