echo "Deploying AWS application..."
echo "---[RUNNING set_env_variables.sh]---"
source scripts/set_env_variables.sh 
printf "\n---[RUNNING get_db_credentials.sh]---\n"
source scripts/get_db_credentials.sh
printf "\n---[RUNNING create_s3_buckets.sh]---\n"
source scripts/create_s3_buckets.sh 
printf "\n---[RUNNING create_iam_role.sh]---\n"
source scripts/create_iam_role.sh
printf "\n---[RUNNING create_iam_policies.sh]---\n"
source scripts/create_iam_policies.sh 
printf "\n---[RUNNING create_eventbridge_rule.sh]---\n"
source scripts/create_eventbridge_rule.sh
printf "\n---[RUNNING create_lambda_function.sh]---\n"
source scripts/create_lambda_functions.sh
printf "\nApplication deployment complete, took ${SECONDS} seconds...\n"