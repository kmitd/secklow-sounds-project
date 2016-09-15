# secklow-sounds-project
Python pipeline to process data from Secklow Sound Community Radio for Milton Keynes 

(Requires a config.json and Google Cloud credentials)

Usage
python2.7 run.py <audiofile> <configfile>

Given an audio_file:

1) reduce audio to mono, 22kh

2) chunk based on silence and export chunks 

3) filter out chunks that are music

4) get chunk transcript using Google Speech API

Outputs (chunks,images,raws,transcripts) are saved in output/<audiofile>/
