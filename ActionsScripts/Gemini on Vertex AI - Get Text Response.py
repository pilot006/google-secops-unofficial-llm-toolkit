from SiemplifyAction import SiemplifyAction
from SiemplifyUtils import unix_now, convert_unixtime_to_datetime, output_handler
from ScriptResult import EXECUTION_STATE_COMPLETED, EXECUTION_STATE_FAILED,EXECUTION_STATE_TIMEDOUT
import google.auth.transport.requests
from google.oauth2 import service_account
import json
import requests

@output_handler

def main():
    siemplify = SiemplifyAction()

    SA_JSON = siemplify.extract_action_param("Service Account JSON", print_value=False)
    SA_JSON = json.loads(SA_JSON)
    PROJECT_ID = siemplify.extract_action_param("GCP Project ID", print_value=False)
    REGION = siemplify.extract_action_param("GCP Region", print_value=False)
    inbound_prompt = siemplify.extract_action_param("Prompt", print_value=True)
    MODEL_ID = siemplify.extract_action_param("Model Resource ID", print_value=True)
    
    endpoint = 'https://' + REGION
    endpoint = endpoint + '-aiplatform.googleapis.com/v1/projects/' 
    endpoint = endpoint + PROJECT_ID + "/locations/" + REGION
    endpoint = endpoint + '/publishers/google/models/' + MODEL_ID + ':streamGenerateContent'
    siemplify.LOGGER.info("endpoint: " + endpoint)

    # Gemini model structure
    llm_prompt = {
                    "contents": {
                        "role": "user",
                        "parts": {
                            "text": inbound_prompt
                        }
                    }
                }
    credentials = service_account.Credentials.from_service_account_info(
        SA_JSON, scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    hd = {
      "Authorization": "Bearer " + credentials.token,
      "Content-Type": "application/json"
    }
    req = requests.post(endpoint, headers=hd, json=llm_prompt)
    r_json = json.loads(req.text)
    siemplify.LOGGER.info(r_json)
    siemplify.result.add_result_json(r_json)
    full_txt = ""

    # The response comes back in a multi-part array, which we'll choose the first candidate and combine
    for i in r_json:
        if 'parts' in str(i):
            full_txt = full_txt + (i['candidates'][0]['content']['parts'][0]['text'])

    status = EXECUTION_STATE_COMPLETED
    output_message = full_txt
    result_value = full_txt

    siemplify.LOGGER.info("\n  status: {}\n  result_value: {}\n  output_message: {}".format(status,result_value, output_message))
    siemplify.end(output_message, result_value, status)


if __name__ == "__main__":
    main()
