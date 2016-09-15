"""Google Cloud Speech API sample application using the REST API for batch
processing."""

import argparse
import base64
import json
import io,os

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials
from read_phrases import wards
import time
import logging

DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')


def get_speech_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    return discovery.build('speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

def write_output(in_file, response):
    file_dir = "data/transcripts/"+in_file.split("/")[2]
    print file_dir
    try:
        os.mkdir(file_dir)
    except OSError :
        # then it exists
        pass
    with io.open(file_dir+'/'+in_file.split("/")[-1][:-4]+".json", 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(response, ensure_ascii=False, indent=2)))
    
def is_cached(speech_file):
    
    file_path = "data/transcripts/"+speech_file.split("/")[2]+"/"+speech_file.split("/")[-1][:-4]+".json"
     
    if os.path.exists(file_path):
        # with open(file_path) as data_file:
            # print "Trascript exists."
            # print json.load(data_file)
        return True
    else :
        # print "Trascript does not exist. Calling Google Speech API..."
        return False

def asynch_request(speech_remote_file):
    service = get_speech_service()
    
    service_request = service.speech().asyncrecognize(
        body={ 
            'config': {
                        'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                        'sampleRate': 16000,  # 16 khz
                        'languageCode': 'en-GB',  # a BCP-47 language tag,
                         "speech_context":  {"phrases": wards }
                     },
            'audio' : {
                    'uri': speech_remote_file
                }
            })
    response = service_request.execute()
    name = response['name']
    
    # Construct a GetOperation request.
    service_request = service.operations().get(name=name)
    
    while True:
        # Give the server a few seconds to process.
        logging.debug('Waiting for Google Speech API processing...')
        time.sleep(1)
        
        # Get the long running operation with response.
        response = service_request.execute()
        
        if 'done' in response and response['done']: break
    
    # logging.info(json.dumps(response['response']['results']))
    
    return response

def synch_request(speech_file):   
    with open(speech_file, 'rb') as speech:
        speech_content = base64.b64encode(speech.read())
    
    service = get_speech_service()
    service_request = service.speech().syncrecognize(
            body={
                'config': {
                    'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                    'sampleRate': 16000,  # 16 khz
                    'languageCode': 'en-GB' , # a BCP-47 language tag,
                    "speech_context":
                        {"phrases": wards }
                },
                'audio': {
                    'content': speech_content.decode('UTF-8')
                    }
                })
    response = service_request.execute()
    # logging.info(json.dumps(response))
    return response
    


def main(speech_file):
    """Transcribe the given audio file.

    Args:
        speech_file: the name of the audio file.
    """
    # do not run it again if we have already the trascript 
    # if (is_cached(speech_file)) :
#         return
    response = synch_request(speech_content)
    
    print(json.dumps(response))
    write_output(speech_file,response)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'speech_file', help='Full path of audio file to be recognized')
    args = parser.parse_args()
    main(args.speech_file)
