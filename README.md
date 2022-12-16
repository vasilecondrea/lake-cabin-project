# lake-cabin-project
This is a repository to hold the final project of team lake-cabin. 
Team members are Anthony Wong, Samuel Fowler, Shehryar Mughal, Vasile Condrea and Hana Mohamed.

# DEPLOYMENT SCRIPT
Before running deployment script:
 - Set up AWS credentials with awsume using 'alias awsume=". awsume"' and 'awsume [profile]'
 - Confirm that the credentials are valid and you are connected to AWS using 'aws sts get-caller-identity' in terminal
 - Please ensure database credentials are added to the 'deployment/db_creds_source.json' and 'deployment/db_creds_destination.json' files
Run deployment script in the terminal using 'bash deployment/deploy_ingestion.sh'

