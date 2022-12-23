if [ "$INGESTION_RULE" == "" ] || [ "$INGESTION_RULE" == null ]; then
    echo "Creating ingestion eventbridge rule..."

    INGESTION_RULE=$(aws events put-rule --name ingestion-rule-${SUFFIX} --schedule-expression "rate(5 minutes)" | jq .RuleArn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${INGESTION_RULE}" '.ingestion_rule |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "Ingestion eventbridge rule already created, skipping..."
fi
wait

if [ "$TRANSFORMATION_RULE" == "" ] || [ "$TRANSFORMATION_RULE" == null ]; then
    echo "Creating transformation eventbridge rule..."

    TRANSFORMATION_RULE=$(aws events put-rule --name transformation-rule-${SUFFIX} --schedule-expression "rate(5 minutes)" | jq .RuleArn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${TRANSFORMATION_RULE}" '.transformation_rule |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "Transformation eventbridge rule already created, skipping..."
fi
wait

if [ "$LOAD_RULE" == "" ] || [ "$LOAD_RULE" == null ]; then
    echo "Creating load eventbridge rule..."

    LOAD_RULE=$(aws events put-rule --name load-rule-${SUFFIX} --schedule-expression "rate(5 minutes)" | jq .RuleArn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg policy "${LOAD_RULE}" '.load_rule |= $policy' <<< $RESOURCES_JSON > resources.json
else
    echo "Load eventbridge rule already created, skipping..."
fi
wait