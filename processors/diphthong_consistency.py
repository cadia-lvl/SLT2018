#!/usr/bin/env python3

"""
Ensure that all diphthongs are transcribed in the same way:

    'ei/ey'     /ei(ː)/
    'au'        /œy(ː)/
    'æ'         /ai(ː)/
    'ó'         /ou(ː)/
    'á'         /au(ː)/

    'ugi'       /ʏi j ɪ/
    'ogi'       /ɔi j ɪ/

    'agi'       /ai j ɪ/
    'an[gk]'    /au/
    'eg[ij]'    /ei j (ɪ)/
    'en[gk]'    /ei/
    'un[gk]'    /u/
    'ögi'       /œy j ɪ/
    'ön[gk]'    /œy/
    '[iy]n[gk]' /i/

1) collect statistics on how the transcriptions of the above are in original (IPA-valid) frob
2) write out correct and non-correct entries

We will not correct the entries, but rather remove them from the dictionary and later transcribe them via g2p

Input: aligned frob file of the format:

a	aː
abbast	a p a s t
Adam	aː t a m
Adams	aː t a m s
...


"""

import sys
import re

# the transcription of the following words should not be treated as errors
exception_list = ['andagift',
                  'Hrafnagili',
                  'Kjærnested',
                  'liðagigt',
                  'liðagigtar',
                  'magister',
                  'notagildi',
                  'notagildis',
                  'Alzheimer',
                  'stöðugildi',
                  'stöðugildum']

regex_dict = { re.compile('æ|agi'): 'ai',
                    re.compile('ó|on[gk]'): 'ou',
                    re.compile('ei|ey|en[gk]|eg[ij]]'): 'ei',
                    re.compile('au|ön[gk]|ögi'): 'œy',
                    re.compile('á|an[gk]'): 'au',
                    re.compile('[^a]ugi'): 'ʏi j ɪ',
                    re.compile('ogi'): 'ɔi j ɪ',
            }

def find_inconsistencies(inputfile):

    error_list = []
    for line in open(inputfile).readlines():
        word, transcr = line.strip().split('\t')
        if word in exception_list:
            continue
        for pattern in regex_dict.keys():
            if pattern.search(word):
                if not re.search(regex_dict[pattern], transcr):
                    error_list.append(line.strip())
    return error_list

def filter_consistent_transcripts(inputfile):

    new_dict = []
    for line in open(inputfile).readlines():
        error_in_entry = False
        word, transcr = line.strip().split('\t')
        if word in exception_list:
            new_dict.append(line.strip())
            continue
        for pattern in regex_dict.keys():
            if pattern.search(word):
                if not re.search(regex_dict[pattern], transcr):
                    error_in_entry = True

        if not error_in_entry:
            new_dict.append(line.strip())

    return new_dict



def main():
    frob_file = sys.argv[1]

    correct = filter_consistent_transcripts(frob_file)
    error = find_inconsistencies(frob_file)

    print("DIPHTHONG CONSISTENT ENTRIES: " + str(len(correct)))
    for line in correct:
        print(line)

    print("DIPHTHONG INCONSISTENCIES: " + str(len(error)))
    for line in error:
        print(line)


if __name__ == '__main__':
    main()