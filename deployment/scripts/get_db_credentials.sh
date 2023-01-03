# checks whether AWS source database credentials have already been retrieved 
# from resources.json, if not (SOURCE_DB_CREDS is null or "") then credentials
# are loaded from the relevant .json file and secret created using contents
if [ "$SOURCE_DB_CREDS" == "" ] || [ "$SOURCE_DB_CREDS" == null ]; then
    echo "Generating AWS secret for source database credentials..."

    SOURCE_DB_CREDS=$(aws secretsmanager create-secret --name db-creds-source --secret-string file://db_creds_source.json | jq .ARN | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg source_creds "${SOURCE_DB_CREDS}" '.source_db_creds |= $source_creds' <<< $RESOURCES_JSON > resources.json
else
    echo "AWS source database credentials already generated, skipping..."
fi
wait


# checks whether AWS destination database credentials have already been retrieved 
# from resources.json, if not (DESTINATION_DB_CREDS is null or "") then credentials
# are loaded from the relevant .json file and secret created using contents
if [ "$DESTINATION_DB_CREDS" == "" ] || [ "$DESTINATION_DB_CREDS" == null ]; then
    echo "Generating AWS secret for destination database credentials..."

    DESTINATION_DB_CREDS=$(aws secretsmanager create-secret --name db-creds-destination --secret-string file://db_creds_destination.json | jq .Arn | tr -d '"')

    RESOURCES_JSON=$(cat resources.json)
    jq --arg destination_creds "${DESTINATION_DB_CREDS}" '.destination_db_creds |= $destination_creds' <<< $RESOURCES_JSON > resources.json
else
    echo "AWS destination database credentials already generated, skipping..."
fi
wait