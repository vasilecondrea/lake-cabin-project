# lake-cabin-project
This is a repository to hold the final project of team lake-cabin. 
Team members are Anthony Wong, Samuel Fowler, Shehryar Mughal, Vasile Condrea and Hana Mohamed.

The deployment script automatically sets up an AWS deployment that is capable of taking data from a OLTP source database, then transforming that data so it is suitable to be used in an OLAP database.

## DEPENDENCY REQUIREMENTS
The following dependencies are required in order for the deployment to run. 

### TRANSFORMATION SCRIPT
In order to get the packages for the transformation script, there are 2 methods.

#### METHOD 1
These can be found hosted under the python package index https://pypi.org/.
 - numpy-1.24.0-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
 - pandas-1.5.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
 - pyarrow-10.0.1-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
 - pytz-2022.7-py2.py3-none-any.whl

Then follow the steps to place these in the correct location:
- Create the `package` directory in the path `Data_Manipulation/src/data_transformation_code/`
- Unzip the .whl files and place the resulting folders in the `package` directory created earlier

#### METHOD 2
 - cd into the `Data_Manipulation` directory
 - run the command `pip install -r package-requirements.txt -t src/data_transformation/package`

### DEPLOYMENT SCRIPT
The deployment script requires pg8000 as a dependency to be installed.
 - cd into the `deployment` directory
 - run the command `pip install pg8000 -t src/ingestion-folder/package`

## RUNNING THE SCRIPT
Before running deployment script:
 - Set up AWS credentials with awsume using 'alias awsume=". awsume"' and 'awsume [profile]'
 - Confirm that the credentials are valid and you are connected to AWS using 'aws sts get-caller-identity' in terminal
 - Please ensure database credentials are added to the 'deployment/db_creds_source.json' and 'deployment/db_creds_destination.json' files

Then cd into the `deployment` directory and run the command `bash deploy_ingestion.sh`

