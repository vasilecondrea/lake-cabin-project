if [ "$IAM_ROLE" == "" ] || [ "$IAM_ROLE" == null ]; then
    echo "Creating IAM role to carry policies..."

    IAM_ROLE=$(aws iam create-role --role-name lambda-role-${SUFFIX} \
    --assume-role-policy-document file://templates/trust.json | jq .Role.Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${IAM_ROLE}" '.iam_role |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "IAM role already created, skipping..."
fi
sleep 10