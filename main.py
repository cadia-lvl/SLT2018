#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

This script contains the steps for the cleaning of the Icelandic Pronunciation Dictionary (herafter: IPD),
as described in the paper:

Nikulásdóttir, Anna B.; Jón Guðnason, and Eiríkur Rögnvaldsson (2018): An Icelandic Pronunciation Dictionary for TTS.
In: Proceedings of SLT, Athens, Greece.

The repository contains all scripts, input and expected output data. All manual steps are described at the corresponding
places in this script.

The 'frob' token sometimes found when referring to the IPD comes from the Icelandic name:
FRamburðarOrðaBók (pronunciation dictionary)

"""

import subprocess
import phoneset_consistency.ipa_corrector as corr
import diphthong_consistency.diphthong_consistency as diph
from processors.multiple_transcripts import MultipleTranscripts

################################################################################
#
#   UTILITIY METHODS
#
################################################################################

def write_list(list2write, filename):

    with open(filename, 'w') as f:
        for entry in list2write:
            f.write(entry + '\n')

#################################################################################
#
#    1. Phoneset consistency
#
#   Input: data/01_phoneset_consistency/original_IPD_WordList_IPA_SAMPA.csv (65,020 entries)
#
#   Final output: data/01_phoneset_consistency/IPD_IPA_consistent_aligned.csv (64,861 entries)
#
#################################################################################


def cut_columns():
    # The original IPD has three comma separated columns: <word>,<IPA-transcription>,<SAMPA-transcription>
    # Create two dictionaries, one for each kind of transcriptions, have them tab-separated
    # Replace ':' with the IPA length-symbol 'ː' in the IPA version

    cmd = "cut -d',' -f{} data/01_phoneset_consistency/original_IPD_WordList_IPA_SAMPA.csv |" \
          " sed 's/,/\t/g' {} > {}"
    ipa_cmd = cmd.format('1,2', " | sed 's/:/ː/g' ",  'data/01_phoneset_consistency/original_IPD_IPA.csv')
    sampa_cmd = cmd.format('1,3', '', 'data/01_phoneset_consistency/original_IPD_SAMPA.csv')
    subprocess.call(ipa_cmd, shell=True)
    subprocess.call(sampa_cmd, shell=True)

def extract_inconsistencies(input_file, error_file, output_file, ipa=True):
    if ipa:
        align_script = 'align_phonemes.py'
    else:
        align_script = 'align_sampa.py'

    cmd = "python3 phoneset_consistency/{} {} {} --output-cols 1,2 > {}".format(align_script, input_file, error_file, output_file)
    subprocess.call(cmd, shell=True)


def correct_inconsistencies(inputfile):

    corr.correct_inconsistencies(inputfile)


def phoneset_consistency_check():
    data_dir = 'data/01_phoneset_consistency/'
    cut_columns()
    extract_inconsistencies(data_dir + 'original_IPD_IPA.csv',
                            data_dir + 'IPD_IPA_errors.txt',
                            data_dir + 'IPD_IPA_valid.csv')
    extract_inconsistencies(data_dir + 'original_IPD_SAMPA.csv',
                            data_dir + 'IPD_SAMPA_errors.txt',
                            data_dir + 'IPD_SAMPA_valid.csv', ipa=False)
    correct_inconsistencies(data_dir + 'original_IPD_IPA.csv')
    extract_inconsistencies(data_dir + 'original_IPD_IPA_consistent.csv',
                            data_dir + 'IPD_IPA_consistent_errors.txt',
                            data_dir + 'IPD_IPA_consistent_aligned.csv')


#################################################################################
#
#    2. Diphthong consistency
#
#   Input: data/01_phoneset_consistency/IPD_IPA_consistent_aligned.csv  (64,861 entries)
#
#   Final output: data/02_diphthongs/IPD_IPA_diphthong_consistent.csv   (60,693 entries)
#
#################################################################################

def diphthong_consistency_check():

    consistent_entries = diph.filter_consistent_transcripts('data/01_phoneset_consistency/IPD_IPA_consistent_aligned.csv')
    write_list(consistent_entries, 'data/02_diphthongs/IPD_IPA_diphthong_consistent.csv')


#################################################################################
#
#    3. Transcription variants and dialects
#
#   Input: data/02_diphthongs/IPD_IPA_diphthong_consistent.csv  (60,693 entries)
#
#   Final output: data/03_multiple_transcripts/IPD_IPA_multiple_transcript_processed.csv (54,381 entries)
#
#################################################################################

def multiple_transcripts():

    out_data_dir = 'data/03_multiple_transcripts/'
    processor = MultipleTranscripts()
    processor.process_dictionary('data/02_diphthongs/IPD_IPA_diphthong_consistent.csv')

    # Filtered dictionary, only selected multiple transcripts
    out = open(out_data_dir + 'IPD_IPA_multiple_transcript_processed.csv', 'w')
    out.writelines(processor.filtered_dictionary)

    # Statistics on multiple entries
    words_outfile = out_data_dir + 'words_with_multiple_transcripts.txt'
    multiple_transcripts_outfile = out_data_dir + 'multiple_transcripts.csv'

    #print("Number of words with multiple transcripts: " + str(len(processor.words_with_multiple_transcr)))

    out = open(words_outfile, 'w')
    for w in processor.words_with_multiple_transcr:
        out.write(w + '\n')

    out = open(multiple_transcripts_outfile, 'w')
    out.writelines(processor.lines2write)

    out = open(out_data_dir + 'no_choice.txt', 'w')
    out.writelines(processor.no_choice_made)

    out = open(out_data_dir + 'transcript_diff_stats.txt', 'w')
    for diff in sorted(processor.transcript_diffs_stats, key=lambda x: len(processor.transcript_diffs_stats[x]),
                       reverse=True):
        out.write(str(diff) + '\t' + str(processor.transcript_diffs_stats[diff]) + '\t' + str(
            len(processor.transcript_diffs_stats[diff])) + '\n')

    out = open(out_data_dir + 'transcript_stats_only.txt', 'w')
    for diff in sorted(processor.transcript_diffs_stats, key=lambda x: len(processor.transcript_diffs_stats[x]),
                       reverse=True):
        out.write(
            str(diff) + '\t' + str(len(processor.transcript_diffs_stats[diff])) + '\n')

def main():

    #phoneset_consistency_check()
    #diphthong_consistency_check()
    multiple_transcripts()

if __name__=='__main__':
    main()