#!/bin/bash

echo "Setting up the variables"

SUFFIX=141222
CODE_BUCKET_NAME=code-bucket-${SUFFIX}

echo "Creating bucket ${CODE_BUCKET_NAME}"

RESPONSE=$(aws s3 mb s3://${CODE_BUCKET_NAME})

echo $RESPONSE

