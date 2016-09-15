#!/usr/bin/env python
from chunk_episode import get_chunks, export_chunk, is_too_long
from filter_music import to_raw, is_speech
from speech_to_text import synch_request, asynch_request
from cloud_storage import upload_to_GCloud

import sys,os,io
import json
import logging

# global vars



def read_config_file(config_file):
    return json.loads(io.open(config_file, 'r', encoding='utf-8').read())
      
    
def create_dirs(episode):
    try:
        os.mkdir("output")
        os.mkdir("output/"+episode)
        os.mkdir("output/"+episode+"/chunks")
        os.mkdir("output/"+episode+"/raws")
        os.mkdir("output/"+episode+"/images")
        os.mkdir("output/"+episode+"/transcripts")
        
        fileHandler = logging.FileHandler("output/{0}/{1}.log".format(episode, "log-"+episode))
        fileHandler.setLevel(logging.INFO)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)
        
    except OSError : pass
    logging.info("Created dirs")
    
# input: an episode
configs=read_config_file(sys.argv[2])
episode=sys.argv[1].split("/")[-1][:-4]

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] [%(module)s, %(lineno)d] %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
        



# create episode dirs
create_dirs(episode)

# chunking ... this takes forever
chunking_configs=configs['chunking']
chunks=get_chunks(sys.argv[1],chunking_configs)

for i, chunk in enumerate(chunks):
    
    #do not request already requested!!
    if (os.path.exists("output/{0}/transcripts/chunk{1}.json".format(episode, i))):
        logging.info("output/{0}/transcripts/chunk{1}.json already trascribed!".format(episode, i))
        continue
        
    logging.info("Chunk {0} out of {1}, {2} secs".format(i, len(chunks), len(chunk)/1000.0 ) )
    
    chunk_file="output/{0}/chunks/chunk{1}.mp3".format(episode,i)
    export_chunk(chunk, chunk_file)
    
    if is_speech(chunk):
        logging.debug("Converting output/{0}/chunks/chunk{1}.mp3 to mono...".format(episode, i))
        
        # converto to mono, 16k, .raw
        raw_chunk = "output/{0}/raws/chunk{1}.raw".format(episode,i)
        to_raw(chunk, raw_chunk)
        
        # speech 
        if is_too_long(chunk,configs['speech_to_text']['sync_req_max_length']):
            # then get it from CloudStorage
            logging.info("chunk{0} must be async...".format(i))

            upload_to_GCloud(raw_chunk,configs['gcloud_storage'])
            
            transcript=asynch_request('gs://{0}/data/raws/{1}/chunk{2}.raw'.format(configs['gcloud_storage']['cloud_storage_bucket'],episode,i)) 
            
        else:
            # can be synchronized
            transcript=synch_request(raw_chunk)
            
        # FINALLY write output!
        with io.open("output/{0}/transcripts/chunk{1}.json".format(episode,i), 'w', encoding='utf-8') as f:
            f.write(unicode(json.dumps(transcript, ensure_ascii=False, indent=2)))
            logging.info("Transcript output/{0}/transcripts/chunk{1}.json OK." .format(episode, i))
    
    else :
        logging.debug("Detected output/{0}/chunks/chunk{1} as music".format(episode,i))
    
    

