#!/usr/bin/env python3

# Checks google file 'suggestions.csv' against an lvl version of the pron dict


import sys

def compare_words(ipd_file, googlei18n_suggestion_file):

    google_list = []
    pron_dict = []

    for line in open(googlei18n_suggestion_file).readlines():
        arr = line.split(',')
        google_list.append(arr[1])

    for line in open(ipd_file).readlines():
        word, transcr = line.split('\t')
        pron_dict.append(word)

    still_in_dict = [x for x in google_list if x in pron_dict]

    return still_in_dict

def compare_words_with_transcr(ipd_file, googlei18n_suggestion_file):

    google_dict = {}
    errors_in_dict = []

    for line in open(googlei18n_suggestion_file).readlines():
        arr = line.split(',')
        word = arr[1]
        transcr = arr[3]
        if word in google_dict:
            google_dict[word].append(transcr)
        else:
            google_dict[word] = [transcr]

    for line in open(ipd_file).readlines():
        word, transcr_aligned = line.split('\t')
        transcr = transcr_aligned.replace(' ', '').strip()
        if word in google_dict:
            if transcr in google_dict[word]:
                errors_in_dict.append(line.strip())

    return errors_in_dict


def main():

    ipd_in = sys.argv[1]
    googlei18n_in = sys.argv[2]

    #result = compare_words(ipd_in, googlei18n_in)

    compare_words_with_transcr(ipd_in, googlei18n_in)

    #for res in result:
    #    print(res)


if __name__ == '__main__':
    main()