#!/usr/bin/env python


from scipy.fftpack import fft,fftfreq
from scipy.stats import skew 
import matplotlib.pyplot as plt
import numpy as np
from numpy.lib import stride_tricks
from pydub import AudioSegment
import warnings
import os,sys
import logging

warnings.filterwarnings('ignore')


def stft(sig, frameSize, overlapFac=0.5, window=np.hanning):
    """
    calculates FFT
    """
    
    win = window(frameSize)
    hopSize = int(frameSize - np.floor(overlapFac * frameSize))
    
    # zeros at beginning (thus center of 1st window should be for sample nr. 0)
    samples = np.append(np.zeros(np.floor(frameSize/2.0)), sig)
    
     
    # cols for windowing
    cols = np.ceil( (len(samples) - frameSize) / float(hopSize)) + 1
    
    # zeros at end (thus samples can be fully covered by frames)
    samples = np.append(samples, np.zeros(frameSize))    
    
    frames = stride_tricks.as_strided(samples, shape=(cols, frameSize), strides=(samples.strides[0]*hopSize, samples.strides[0])).copy()
    frames *= win

    return np.fft.rfft(frames)    
    
def logscale_spec(spec, sr=44100, factor=20.):
    """ 
    scale frequency axis logarithmically 
    """      
    
    timebins, freqbins = np.shape(spec)

    scale = np.linspace(0, 1, freqbins) ** factor
    scale *= (freqbins-1)/max(scale)
    scale = np.unique(np.round(scale))
    
    
    # create spectrogram with new freq bins
    newspec = np.complex128(np.zeros([timebins, len(scale)]))
    for i in range(0, len(scale)):
        if i == len(scale)-1:
            newspec[:,i] = np.sum(spec[:,scale[i]:], axis=1)
        else:        
            newspec[:,i] = np.sum(spec[:,scale[i]:scale[i+1]], axis=1)
    
    # list center freq of bins
    allfreqs = np.abs(np.fft.fftfreq(freqbins*2, 1./sr)[:freqbins+1])
    freqs = []

    for i in range(0, len(scale)):
        if i == len(scale)-1:
            freqs += [np.mean(allfreqs[scale[i]:])]
            # print "fq", i, np.mean(allfreqs[scale[i]:])  
        else:
            freqs += [np.mean(allfreqs[scale[i]:scale[i+1]])]
            # print "fq", i+1, np.mean(allfreqs[scale[i]:scale[i+1]])
    
    return newspec, freqs

def print_chunk_data(mono, binsize=2**10, save_spectro=True):
    
    
    # print "Reading audio..."
#     mp3audio = AudioSegment.from_file(audiopath, format="mp3",  frame_rate=44100)
#
#
#     if len(mp3audio) < 3000:
#         print "Audio %s was less than 3 secs, skipping..." % audiopath
#         return False
#
#     elif len(mp3audio) > 120000:
#         return False
#     else:
#         return True
#
#     print "Convert to mono..."
#     mono = mp3audio.set_channels(1) # merge channels
#     # mono = mp3audio[:10000].split_to_mono()[0]
    
    samples = mono[:10000].get_array_of_samples()
    samplerate = mono.frame_rate 
    
    # binsize : 32k
    print "Calculating FFT..."
    s = stft(samples, binsize)
    
    
    print "(Log?) scaling..."
    sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
    ims = 20.*np.log10(np.abs(sshow)/10e-6) # amplitude to decibel
    
    
    timebins, freqbins = np.shape(ims) # shape of the matrix, rows (timebin) * cols (frqbin)
    
    # save spectro
    if save_spectro:
        print "Saving spectro..."
        plt.figure(figsize=(15, 7.5))
        # transpose time (x axis) and fq (y ax)
        plt.imshow(np.transpose(ims), origin="lower", aspect="auto", cmap="jet", interpolation="spline36")
        plt.colorbar()

        # plot stuff (location of labels and ticks)
        plt.xlabel("time (s)")
        plt.ylabel("frequency (hz)")
        plt.xlim([0, timebins-1])
        plt.ylim([0, freqbins])

        xlocs = np.float32(np.linspace(0, timebins-1, 5))
        plt.xticks(xlocs, ["%.02f" % l for l in ((xlocs*len(samples)/timebins)+(0.5*binsize))/samplerate])
        ylocs = np.int16(np.round(np.linspace(0, freqbins-1, 10)))
        plt.yticks(ylocs, ["%.02f" % freq[i] for i in ylocs])

        plot_dir="data/images/"+audiopath.split('/')[2]
        try :
            os.mkdir(plot_dir)
        except OSError: 
            pass 
        plt.savefig(plot_dir+"/"+audiopath.split('/')[-1][:-4], bbox_inches="tight")
        # plt.show()
        plt.clf()
    
    
    list_human_freq = list(fq for fq in freq if fq > 80 and fq < 300)
    list_others = list(fq for fq in freq if fq > 30 and fq < 5000)    
    humanFreqs = list()
    musicFreqs = list()
    highestDB = list()
    highestFreq = list()
    skewness = list()
    
    print "Getting stats..."
    # over the 10 secs (862 timebins) calculates the average freq of each frequency in the human range and in the non human range  
    for time in range(0,timebins):
        
        
        highest = max(ims[time]) # highest freq in decibels
        highestDB.append(highest)
        highestFreq.append(freq[list(ims[time]).index(highest)]) # which is the frequency in Hz with the highest DB

        # print time, freq[list(ims[time]).index(highest)], highest
        skewness.append(skew(ims[time]))
  
        
        humanFreqs.append( np.average(list(ims[time][freq.index(hfq)] for hfq in list_human_freq )) )
        musicFreqs.append( np.average( list ( ims[time][freq.index(ofq)]  for ofq in list_others)) )
        
    
    logs = [ audiopath.split("/")[3][5:-4], np.average(humanFreqs),np.var(humanFreqs), np.std(humanFreqs) , np.average(musicFreqs),np.var(musicFreqs) , np.std(musicFreqs), np.average(highestDB),np.var(highestDB),np.average(highestFreq),np.var(highestFreq), np.average(skewness), np.var(skewness) ]
    
    return True
     

def read_audio(audio_file):
    return AudioSegment.from_file(audio_file, format="mp3",  frame_rate=44100)
   
def is_speech(mp3audio):
    if len(mp3audio) < 2000:

        logging.debug("Audio was less than 2 secs, skipping...")
        return False
    elif len(mp3audio) > 120000:
        return False
    else:
        return True
    
 
def to_raw(mp3audio, mono_dir):
    mono = mp3audio.set_channels(1) # merge channels
    mono = mono.set_frame_rate(16000)
    mono.export(mono_dir,  format="raw")
    return mono
        
""""
input : an audio file
outputs : True (is speech) or False (is music) 
    currently it is just music if len(chunk) > 2 mins 
"""
# logsFirstLine = ["chunk","avg Hfq (db)","var Hfq  (db)","stddev Hfq (db)","avg Mfq (db) ","var Mfq (db)","stddev Mfq (db)","avg highestFq (db)","var highestFq (db)","avg highestFq (Hz)","var highestFq (Hz)","avg skewness (db)","var skewness (db)"]

if __name__ == '__main__':

    print "Reading audio..."
    mp3audio = read_audio(sys.argv[1])
    
    isVoice=is_speech(mp3audio)
    
    if isVoice:
        print "Convert to mono..."
       
        raws_dir="data/raws/"+sys.argv[1].split("/")[2]
        try:
            os.mkdir(raws_dir)
        except OSError :
            # then it exists
            pass
        
        mono=to_raw(mp3audio, raws_dir+"/"+sys.argv[1].split("/")[-1][:-4]+".raw")
        print "True"
    else :
        print "Audio %s was less than 2 secs, skipping..." % sys.argv[1]


