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
import phoneset_consistency

############################################################
#
#    1. Phoneset consistency
#
############################################################


def cut_columns():
    # The original IPD has three comma separated columns: <word>,<IPA-transcription>,<SAMPA-transcription>
    # Create two dictionaries, one for each kind of transcriptions, have them tab-separated
    # Replace ':' with the IPA length-symbol 'ː' in the IPA version

    cmd = "cut -d',' -f{} data/01_original_frob/original_IPD_WordList_IPA_SAMPA.csv |" \
          " sed 's/,/\t/g' {} > {}"
    ipa_cmd = cmd.format('1,2', " | sed 's/:/ː/g' ",  'data/01_original_frob/original_IPD_IPA.csv')
    sampa_cmd = cmd.format('1,3', '', 'data/01_original_frob/original_IPD_SAMPA.csv')
    subprocess.call(ipa_cmd, shell=True)
    subprocess.call(sampa_cmd, shell=True)

def extract_inconsistencies():

    cmd = "python3 phoneset_consistency/{} {} {} --output-cols 1,2 > {}"
    ipa_cmd = cmd.format('align_phonemes.py', 'data/01_original_frob/original_IPD_IPA.csv',
                         'data/01_original_frob/IPD_IPA_errors.txt', 'data/01_original_frob/IPD_IPA_consistent.csv')
    sampa_cmd = cmd.format('align_sampa.py','data/01_original_frob/original_IPD_SAMPA.csv',
                           'data/01_original_frob/IPD_SAMPA_errors.txt', 'data/01_original_frob/IPD_SAMPA_consistent.csv')
    subprocess.call(ipa_cmd, shell=True)
    subprocess.call(sampa_cmd, shell=True)


def phoneset_consistency_check():
    cut_columns()
    extract_inconsistencies()



# the set of IPA phoneme symbols to be used in the IPD is contained in data/00_phonesets/phone_set_IPA.txt



def main():

    phoneset_consistency_check()

if __name__=='__main__':
    main()