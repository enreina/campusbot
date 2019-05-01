import requests
import settings as env
from pprint import pprint

def generate_enrichment_task(domainName, itemId=None):
    if itemId is None:
        itemId = ""

    requestUrl = "{baseUrl}/{domainName}/generate-enrichment-task/{itemId}".format(
        baseUrl=env.API_BASE_URL,
        domainName=domainName.lower(),
        itemId=itemId
    )
    
    response = requests.post(requestUrl)
    pprint(response.status_code)
    pprint(response.content)

    return response

def generate_validation_task(domainName, userId, enrichmentTaskInstanceId):

    requestUrl = "{baseUrl}/{domainName}/generate-validation-task/{userId}/{enrichmentTaskInstanceId}".format(
        baseUrl=env.API_BASE_URL,
        domainName=domainName.lower(),
        userId=userId,
        enrichmentTaskInstanceId=enrichmentTaskInstanceId
    )

    response = requests.post(requestUrl)
    pprint(response.status_code)
    pprint(response.content)

    return response

def assign_task_to_user(domainName, userId):

    requestUrl = "{baseUrl}/{domainName}/assign-task-to-user/{userId}".format(
        baseUrl=env.API_BASE_URL,
        domainName=domainName.lower(),
        userId=userId
    )

    response = requests.post(requestUrl)
    pprint(response.status_code)
    pprint(response.content)

    return response

