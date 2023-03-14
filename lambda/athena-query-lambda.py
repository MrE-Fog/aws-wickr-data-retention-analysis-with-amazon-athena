import time
import boto3

query = 'SELECT * FROM table'
DATABASE = 'wickr-retention'
output='s3://<bucket>/'
path='<path>'

def lambda_handler(event, context):
    query = "SELECT * FROM table"
    client = boto3.client('athena')
    # Execution
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': DATABASE
        },
        ResultConfiguration={
            'OutputLocation': "{}{}".format(output, path),
        }
    )
    return response
    return