#!/usr/bin/env python
from pydub import AudioSegment
from pydub.silence import split_on_silence
import sys
import os
import logging

"""
input: a MP3 file (from command line)
output : a list of new chunks 
"""

def export_chunk(chunk, chunk_file):
    chunk.export(chunk_file, format="mp3")
    logging.info("Exported %s" % chunk_file)

def get_chunks(audio_file,configs):
    
    # read audio
    logging.info("Reading audio %s..." % audio_file)
    mp3audio = AudioSegment.from_file(audio_file, format="mp3",  frame_rate=44100, channels=2) # sample_width : 1 for 
    
    # convert mono and 16k
    logging.info("Converting to 16KHz...")
    
    mono = mp3audio.set_channels(1) # merge channels
    
    mono_16khz = mono.set_frame_rate(16000)
    
    
    logging.info("Split into silence (min silence len %s)...this will take forever" % configs['min_silence_length'])
    chunks = split_on_silence(mono_16khz,        
        min_silence_len=configs['min_silence_length'],  # must be silent for at least  1 sec
        silence_thresh=configs['silence_threshold'], # consider it silent if quieter than -30 dBFS
        keep_silence=configs['keep_silence']
    )
    return chunks
  
def is_too_long(audio,sync_req_max_length):
    """
    sync or async google speech?
    """
    if len(audio) > sync_req_max_length:
        return True
    else:
        return False
      
 
def chunk_file(audio_file,chunk_dir):
    try:
        os.mkdir(chunk_dir)
    except OSError :
        # then it exists
        pass
    
    # read audio
    print "Reading audio..."
    mp3audio = AudioSegment.from_file(audio_file, format="mp3",  frame_rate=44100, channels=2) # sample_width : 1 for 
    
    # merge to mono
    # print "Convert to mono..."
    # mono = mp3audio.set_channels(1) # merge channels
    
    # reduce sample rate
    # print "Convert to 22KHz..."
    # mono_22khz = mono.set_frame_rate(22050)
    
    # TODO adapt min_silence_len     
    min_silence_length = 1000
    
    print "Split into silence (min silence len %s)..." % str(min_silence_length)
    chunks = split_on_silence(mp3audio,        
        min_silence_len=min_silence_length,  # must be silent for at least  1 sec
        silence_thresh=-30, # consider it silent if quieter than -30 dBFS
        keep_silence=200
    )
    for i, chunk in enumerate(chunks):
        print "Chunk [%s] of %s secs" % (str(i), str(len(chunk)/1000.0))
        # if len(chunk) > 0:
        chunk.export(chunk_dir+"/chunk{0}.mp3".format(i), format="mp3")
    

if __name__ == '__main__':
    epi = sys.argv[1]
    chunk_file(epi, "data/chunks/"+epi[22:-4])

