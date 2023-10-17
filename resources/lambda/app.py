import boto3
from boto3.dynamodb.types import TypeDeserializer
from typing import Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth


dynamodb = boto3.resource('dynamodb')
converter = TypeDeserializer()

host = 'e4m6xkmr32a0frctv7qj.us-west-2.aoss.amazonaws.com'  # serverless collection endpoint, without https://
region = 'us-west-2'  # e.g. us-east-1

service = 'aoss'
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, service)

opensearch = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    pool_maxsize=20,
)

def handler(event, context):
    print("Received", event, "from the user table")

    # In later setup we set the batchSize of this event source to be 1 
    # so in reality this for loop will only run once each time 
    # but if you wanted to increase the batch size this Lambda can handle that
    for record in event["Records"]:
        if not record.get("eventName") or not record.get("dynamodb") or not record["dynamodb"].get("Keys"):
            continue

        partition_key = record["dynamodb"]["Keys"]["partitionKey"]["S"]
        sort_key = record["dynamodb"]["Keys"]["sortKey"]["S"]
        # Note here that we are using a pk and sk 
        # but maybe you are using only an id, this would look like:
        # id = record["dynamodb"]["Keys"]["id"]["S"]

        try:
            if record["eventName"] == "REMOVE":
                # removeDocumentFromOpenSearch will perform a DELETE request to your index
                return remove_document_from_open_search(partition_key, sort_key)
            else:
                # There are 2 types of events left to handle, INSERT and MODIFY, 
                # which will both contain a NewImage
                if not record["dynamodb"].get("NewImage"):
                    continue

                user_document_raw = record["dynamodb"]["NewImage"]
                user_document = {k: converter.deserialize(v) for k, v in user_document_raw.items()}
                # Assuming user_document type checks are handled elsewhere or aren't strictly needed in Python
                
                # index_document_in_open_search will perform a PUT request to your index
                return index_document_in_open_search(user_document, partition_key, sort_key)
        except Exception as error:
            print(f"Error occurred updating OpenSearch domain: {error}")
            raise error

def remove_document_from_open_search(partition_key: str, sort_key: str) -> None:
    # TODO: Implement the function to remove document from OpenSearch
    pass

def index_document_in_open_search(user_document: Dict[str, Any], partition_key: str, sort_key: str) -> None:
    response = opensearch.indices.create(
        index = partition_key,
    )

    response = opensearch.index(
        index = partition_key,
        body = user_document,
    )
    print(response)
    pass

