import boto3

# Create a new Lambda client
lambda_client = boto3.client('lambda')

# Define the function code and configuration
function_code = {
    'zip_file': open('', 'rb'), #take the code I want to run 
    'function_name': 'my_function',
    'runtime': 'python3.8',
    'handler': 'lambda_function.handler',
    'description': 'My Lambda function',
    'role': 'arn:', #need to input 
    'timeout': 30,
    'memory_size': 128
}


# Create the function
response = lambda_client.create_function(**function_code)


# Print the ARN of the newly created function
print(response.function_arn)
