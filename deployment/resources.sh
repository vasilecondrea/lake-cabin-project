#!/bin/bash

S3_READ_WRITE_POLICY=$(cat resources.json | jq .s3_read_write_policy)
CLOUDWATCH_LOG_POLICY=$(cat resources.json | jq .cloudwatch_log_policy)
IAM_ROLE=$(cat resources.json | jq .iam_role)
EVENTBRIDGE_RULE=$(cat resources.json | jq .eventbridge_rule)

if [ "$S3_READ_WRITE_POLICY" == "" ] || [ "$S3_READ_WRITE_POLICY" == null ]; then
    echo "creating S3_READ_WRITE_POLICY..."
    S3_READ_WRITE_POLICY="arn_has_been_created"
    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${S3_READ_WRITE_POLICY}" '.s3_read_write_policy |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "S3_READ_WRITE_POLICY already exists, skipping..."
fi

if [ "$CLOUDWATCH_LOG_POLICY" == "" ] || [ "$CLOUDWATCH_LOG_POLICY" == null ]; then
    echo "creating CLOUDWATCH_LOG_POLICY..."
    CLOUDWATCH_LOG_POLICY="arn_has_been_created"
    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${CLOUDWATCH_LOG_POLICY}" '.cloudwatch_log_policy |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "CLOUDWATCH__POLICY already exists, skipping..."
fi