#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Convert the transcriptions of a pronunciation dictionary according to a phoneme table.

Note that the transcriptions have to be aligned - no attempt is made to identify diphthongs or other
combined phonetic symbols. It is assumed that the words and their transcriptions are separated by tab
and that the symbols in the transcriptions are separated by a space

"""

import sys
import argparse


def create_transcription_map(mapping_file):

    transcr_map = {}
    for line in mapping_file.readlines():
        key, value = line.split()
        transcr_map[key] = value

    return transcr_map


def transcribe_dictionary(dict_file, transcr_map):

    transcribed_dict = []

    for line in dict_file.readlines():
        error_in_transcript = False
        word, transcr = line.split('\t')
        transcr_arr = transcr.strip().split()

        for ind, item in enumerate(transcr_arr):
            if item in transcr_map:
                transcr_arr[ind] = transcr_map[item]
            else:
                print(item + ' - ' + line.strip())
                error_in_transcript = True

        if not error_in_transcript:
            transcribed_dict.append(word + '\t' + ' '.join(transcr_arr))

    return transcribed_dict


def parse_args():
    parser = argparse.ArgumentParser(description='Transcription converter for aligned phonetic transcriptions',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('i', type=argparse.FileType('r'), help='Pronunciation dictionary')
    parser.add_argument('d', type=argparse.FileType('r'), help='Symbol map (e.g. IPA-to-XSAMPA')
    parser.add_argument('-o', type=argparse.FileType('w'), help='Output dictionary', default='converted_transcripts.txt')

    return parser.parse_args()


def main():
    args = parse_args()

    transcription_map = create_transcription_map(args.d)

    transcribed_dict = transcribe_dictionary(args.i, transcription_map)

    for line in transcribed_dict:
        args.o.write(line + '\n')


if __name__ == '__main__':
    sys.exit(main())