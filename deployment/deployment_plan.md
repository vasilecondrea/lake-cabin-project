1. Set up variables: (get AWS credentials from sts with jq, ARNS taken from resources JSON file with jq)
    - AWS_ACCOUNT_ID (AWS secret)
    - AWS_REGION (AWS secret)
    - FUNCTION_NAME (fixed to some unique name)
    - CODE_BUCKET_ARN (resources JSON key)
    - INGESTION_BUCKET_ARN (resources JSON key)

2. Generate deployment package .zip file with src/data_ingestion/ folder containing python function
3. Upload deployment package to the code bucket
4. Generate policy documents from templates:
    - S3_READ_WRITE_POLICY (from s3_ingestion_policy_template.json)
    - CLOUDWATCH_LOG_POLICY (from cloudwatch_log_policy_template.json)
5. Create IAM role to contain both policies
6. Attach policies to IAM role
7. Create lambda function with IAM role
8. Create eventbridge rule to run every 5 minutes using put-rule command
9. Add permission for eventbridge rule to invoke lambda using lambda add-permission
10. Add lambda function as target for eventbridge rule

.github
    workflows
        deploy.yaml
deployment
    policy-templates
        s3_ingestion_policy_templates.json
        cloudwatch_log_policy_template.json
        eventbridge_targets.json
src
    ingestion_function
        ingestion.py
    transform_function
        tranfsorm.py
    load_function
        load.py
tests
    tests.py
requirements.txt
deploy.sh
.gitignore
makefile


Documentation links:
S3 read & write policy template: https://docs.amazonaws.cn/en_us/IAM/latest/UserGuide/reference_policies_examples_s3_rw-bucket-console.html
Eventbridge rule creation: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-run-lambda-schedule.html