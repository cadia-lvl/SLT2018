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
import os
import subprocess
import sys
import argparse
import phoneset_consistency.ipa_corrector as corr
import diphthong_consistency.diphthong_consistency as diph
import processors.post_aspiration as postaspir
import processors.length_symbol_analysis as length_sym
import processors.compound_analysis as comp
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


def cut_columns(inputfile, output_dir):
    # The original IPD has three comma separated columns: <word>,<IPA-transcription>,<SAMPA-transcription>
    # Create two dictionaries, one for each kind of transcriptions, have them tab-separated
    # Replace ':' with the IPA length-symbol 'ː' in the IPA version

    cmd = "cut -d',' -f{} {} |" \
          " sed 's/,/\t/g' {} > {}"
    ipa_cmd = cmd.format('1,2', inputfile, " | sed 's/:/ː/g' ",  output_dir + '/original_IPD_IPA.csv')
    sampa_cmd = cmd.format('1,3', inputfile, '', output_dir + '/original_IPD_SAMPA.csv')
    subprocess.call(ipa_cmd, shell=True)
    subprocess.call(sampa_cmd, shell=True)

def extract_inconsistencies(input_file, error_file, output_file, ipa=True):
    if ipa:
        align_script = 'align_phonemes.py'
    else:
        align_script = 'align_sampa.py'

    cmd = "python3 phoneset_consistency/{} {} {} --output-cols 1,2 > {}".format(
        align_script, input_file, error_file, output_file)
    subprocess.call(cmd, shell=True)


def correct_inconsistencies(inputfile):

    corr.correct_inconsistencies(inputfile)


def phoneset_consistency_check(inputfile):

    data_dir, filename_ext = os.path.split(inputfile)
    cut_columns(inputfile, data_dir)
    extract_inconsistencies(data_dir + '/original_IPD_IPA.csv',
                            data_dir + '/IPD_IPA_errors.txt',
                            data_dir + '/IPD_IPA_valid.csv')
    extract_inconsistencies(data_dir + '/original_IPD_SAMPA.csv',
                            data_dir + '/IPD_SAMPA_errors.txt',
                            data_dir + '/IPD_SAMPA_valid.csv', ipa=False)
    correct_inconsistencies(data_dir + '/original_IPD_IPA.csv')
    extract_inconsistencies(data_dir + '/original_IPD_IPA_consistent.csv',
                            data_dir + '/IPD_IPA_consistent_errors.txt',
                            data_dir + '/IPD_IPA_consistent_aligned.csv')


#################################################################################
#
#    2. Diphthong consistency
#
#   Input: data/01_phoneset_consistency/IPD_IPA_consistent_aligned.csv  (64,861 entries)
#
#   Final output: data/02_diphthongs/IPD_IPA_diphthong_consistent.csv   (60,693 entries)
#
#################################################################################

def diphthong_consistency_check(inputfile, outputfile):

    consistent_entries = diph.filter_consistent_transcripts(inputfile)
    write_list(consistent_entries, outputfile)


#################################################################################
#
#    3. Transcription variants and dialects
#
#   Input: data/02_diphthongs/IPD_IPA_diphthong_consistent.csv  (60,693 entries)
#
#   Final output: data/03_multiple_transcripts/IPD_IPA_multiple_transcript_processed.csv (54,360 entries)
#
#################################################################################

def multiple_transcripts(inputfile, out_data_dir):

    processor = MultipleTranscripts()
    processor.process_dictionary(inputfile)

    # Filtered dictionary, the final output will be created at the end of this method
    out = open(out_data_dir + '/IPD_IPA_multiple_transcript_processed_TMP.csv', 'w')
    out.writelines(processor.filtered_dictionary)

    # Statistics on multiple entries
    words_outfile = out_data_dir + '/words_with_multiple_transcripts.txt'
    multiple_transcripts_outfile = out_data_dir + '/multiple_transcripts.csv'

    #print("Number of words with multiple transcripts: " + str(len(processor.words_with_multiple_transcr)))

    out = open(words_outfile, 'w')
    for w in processor.words_with_multiple_transcr:
        out.write(w + '\n')

    out = open(multiple_transcripts_outfile, 'w')
    out.writelines(processor.lines2write)

    out = open(out_data_dir + '/no_choice.txt', 'w')
    out.writelines(processor.no_choice_made)

    out = open(out_data_dir + '/transcript_diff_stats.txt', 'w')
    for diff in sorted(processor.transcript_diffs_stats, key=lambda x: len(processor.transcript_diffs_stats[x]),
                       reverse=True):
        out.write(str(diff) + '\t' + str(processor.transcript_diffs_stats[diff]) + '\t' + str(
            len(processor.transcript_diffs_stats[diff])) + '\n')

    out = open(out_data_dir + '/transcript_stats_only.txt', 'w')
    for diff in sorted(processor.transcript_diffs_stats, key=lambda x: len(processor.transcript_diffs_stats[x]),
                       reverse=True):
        out.write(
            str(diff) + '\t' + str(len(processor.transcript_diffs_stats[diff])) + '\n')

    # clean the last multiple transcript entries, run again
    processor = MultipleTranscripts()
    processor.process_dictionary(out_data_dir + '/IPD_IPA_multiple_transcript_processed_TMP.csv')

    # Final filtered dictionary, only entries with one transcript and selected entries with multiple transcripts
    out = open(out_data_dir + '/IPD_IPA_multiple_transcript_processed.csv', 'w')
    out.writelines(processor.filtered_dictionary)

#################################################################################
#
#    4. Postaspiration
#
#   Input: data/03_multiple_transcripts/IPD_IPA_multiple_transcript_processed.csv (54,360 entries)
#
#   Final output: data/04_postaspiration/IPD_IPA_postaspir_corrected.csv (54,360 entries)
#
#################################################################################

def correct_postaspiration(inputfile, output_dir):
    dict_list = open(inputfile).readlines()

    postaspir.find_missing_postaspir(dict_list, output_dir)
    postaspir.find_beginning_postaspir(dict_list, output_dir)
    corrected = postaspir.ensure_postaspir(dict_list)
    write_list(corrected, output_dir + '/IPD_IPA_postaspir_corrected.csv')

#################################################################################
#
#    5. Vowel length
#
#   Input: data/04_postaspiration/IPD_IPA_postaspir_corrected.csv (54,360 entries)
#
#   Output: data/05_vowel_length/IPD_IPA_no_length_symbols (54,360 entries)
#   NO CHANGES MADE TO THE DICTIONARY, SOLELY AN ANALYSIS STEP
#   Keep on using the results of step 4, postaspiration, as input to step 6
#
#################################################################################

def vowel_length_analysis(inputfile, out_dir):
    pron_dict = open(inputfile).readlines()
    no_len_symbols = length_sym.remove_length_symbols_from_dict(pron_dict)
    non_initial_len_symbols = length_sym.find_length_symbol_after_1st(pron_dict)

    write_list(no_len_symbols, out_dir + '/IPD_IPA_no_len_symbols.csv')
    write_list(non_initial_len_symbols, out_dir + '/IPD_IPA_vowel_lengths_internal.csv')

#################################################################################
#
#    6. Compound analysis
#
#   Input: data/04_postaspiration/IPD_IPA_postaspir_corrected.csv (54,360 entries)
#
#   Output 1: data/06_compound_analysis/IPD_IPA_compounds.csv
#   Output 2: data/06_compound_analysis/IPD_IPA_multitranscr.csv
#
#   Final output: data/06_compound_analysis/IPD_IPA_compound_filtered.csv (40,946 entries)
#
#################################################################################

def compound_analysis(inputfile, output_dir):

    frob_in = open(inputfile).readlines()
    pron_dict = comp.process_dictionary(frob_in)
    compounds = comp.collect_entries(pron_dict)
    #non_comps = comp.collect_entries(pron_dict, comp=False)
    multi_transcr = comp.collect_multi_transcripts(pron_dict)

    write_list(compounds, output_dir + '/IPD_IPA_compounds.csv')
    write_list(multi_transcr, output_dir + '/IPD_IPA_multitranscr.csv')

    # Remove compounds from dictionary:
    list2remove = []
    for entry in compounds:
        word, transcr, elems = entry.split('\t')
        list2remove.append(word + '\t' + transcr)

    clean_list = remove_list_by_word(list2remove, frob_in)
    write_list(clean_list, output_dir + '/IPD_IPA_compound_filtered.csv')

def remove_list_by_word(list2remove, dict_list):
    set2remove = set()
    for elem in list2remove:
        set2remove.add(elem.split('\t')[0])
    print(str(len(set2remove)))
    clean_list = [x.strip() for x in dict_list if x.split('\t')[0].lower() not in set2remove]

    return clean_list

#####################################################################################
#
#   MANUAL STEP: search the IPD_IPA_multitranscr.csv for errors,
#   collected into data/05_compound_analysis/spotted_errors_comp.txt
#
#####################################################################################

#################################################################################
#
#    7. Remove error list from IPD
#
#   Input: data/06_compound_analysis/IPD_IPA_compound_filtered.csv (40,946 entries)
#
#   Final output: data/06_compound_analysis/IPD_IPA_compound_filtered_final.csv (40,885 entries)
#
#   (There are 208 entries in the 'spotted_errors' file, a lot of compounds in that file
#    were already removed during automatic removal of compounds in the previous step)
#
#################################################################################

def remove_list(list2remove, dict_list, out_dir):

    all_lower = [x.lower() for x in list2remove]
    set2remove = set(all_lower)
    clean_list = [x.strip() for x in dict_list if x.strip().lower() not in set2remove]

    write_list(clean_list, out_dir + '/IPD_IPA_compound_filtered_final.csv')

#################################################################################
#
#    8. Forced alignment
#
#   Input: data/06_compound_analysis/IPD_IPA_compound_filtered.csv (40,946 entries)
#
#   Final output: data/07_alignment/IPD_IPA_aligned.csv (X entries)
#
#
#################################################################################

def parse_args():

    parser = argparse.ArgumentParser(
        description='Processes the raw Icelandic pronunciation dictionary to create a cleaner version',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--step', type=int, default=1,
                        help='The first step of the process to run, then runs all subsequent steps')
    parser.add_argument('--comp_errors', type=argparse.FileType('r'), default=sys.stdin,
                        help='Error file, remove this content from dictionary')

    return parser.parse_args()

def main():

    args = parse_args()
    step = args.step
    #step = 6
    out_data_dirs = ['data/02_diphthongs', 'data/03_multiple_transcripts', 'data/04_postaspiration',
                     'data/05_vowel_length', 'data/06_compounds', 'data/07_alignment']

    create_dirs = out_data_dirs[step - 1:]

    for out_dir in create_dirs:
        # if exists, add a date suffix to each dir?
        os.makedirs(out_dir, exist_ok=True)
        #os.makedirs(out_dir)

    if step == 1:
        phoneset_consistency_check('data/01_phoneset_consistency/original_IPD_WordList_IPA_SAMPA.csv')
        step +=1

    if step == 2:
        diphthong_consistency_check('data/01_phoneset_consistency/IPD_IPA_consistent_aligned.csv',
                                out_data_dirs[0] + '/IPD_IPA_diphthong_consistent.csv')
        step += 1

    if step == 3:
        multiple_transcripts(out_data_dirs[0] + '/IPD_IPA_diphthong_consistent.csv',
                         out_data_dirs[1])
        step += 1
    if step == 4:
        correct_postaspiration(out_data_dirs[1] + '/IPD_IPA_multiple_transcript_processed.csv', out_data_dirs[2])
        step += 1

    if step == 5:
        vowel_length_analysis(out_data_dirs[2] + '/IPD_IPA_postaspir_corrected.csv', out_data_dirs[3])
        step += 1

    if step == 6:
        compound_analysis(out_data_dirs[2] + '/IPD_IPA_postaspir_corrected.csv', out_data_dirs[4])
        print("Finished compound analysis. Please control 'IPD_IPA_multitranscr.csv' for errors."
              "Collect the errors into a text file and run main.py again from step 7")
        sys.exit(0)

    if step == 7:
        error_file = args.comp_errors
        inp_dict = open(out_data_dirs[4] + '/IPD_IPA_compound_filtered.csv').readlines()
        remove_list(error_file.read().splitlines(), inp_dict, out_data_dirs[4])

if __name__=='__main__':
    main()