from dotenv import load_dotenv
import os


# load the api secret
load_dotenv()
api_key = os.getenv('api_key')

# create expected headers
headers = {
    'x-apisports-key': {api_key}
}

print(headers)



