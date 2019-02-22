#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test quality of automatic g2p using Sequitur.

1) Train a model using a selected training set (self.train_file). The training file is of the format:
    word w o r d

2) Test the model using an input test file, see main()
    When testing, the number of errors, the error rate and all errors with correct transcriptions are written
    to a result file. Computes PER and WER.

Be careful to use the same sort of training and test data, i.e. with or without stress labels.

If you don't have the Levenshtein module installed:

    pip install python-levenshtein

The 'lts' abbreviation used in the code stands for 'letter-to-sound'

"""

import os
import configparser
import argparse
import time
import shutil
import subprocess
import unicodedata
import re
import Levenshtein

from processors import multiple_transcripts


class G2P_Experiment:

    def __init__(self, model_filename, train_file='', ntrain=0, configfile='g2p.conf'):

        current_dir = os.getcwd() + '/'
        config = configparser.ConfigParser()
        config.read(current_dir + configfile)
        self.g2p_path = config['pythonpath']['path_export']
        self.lts_tool = config['g2p_tool']['g2p']
        self.train_file = train_file
        self.lts_fname = model_filename
        self.lts_model = '' # derived from lts_fname while processing
        # number of training instances, if default (0): train on all training input
        self.lts_ntrain = ntrain

    ##################################################################
    #
    #       TRAINING
    #
    ##################################################################

    def set_parameters(self, max_letters=1, max_phones=1, gram_len=3):
        """
        max_graphone_letters and max_graphone_phones correspond to parameter L in Sequitur. letters and phones can take
        different values, values from 1 - 3 are sensible for each parameter.
        gram_length corresponds to parameter M in Sequitur. Values from 2 - 6 are probably sensible in most cases.
        Note: the higher the L parameter value, the lower the M parameter should be and vice versa.
        E.g. L=1, M=6 or L=3, M=3. Setting gram_length

        """
        self.max_graphone_letters = max_letters
        self.max_graphone_phones = max_phones
        self.lts_gram_length = gram_len


    def train_sequitur_g2p(self):

        lts_model = self.lts_fname
        print('Training Letter-To-Sound with sequitur...')
        ## train unigram model:
        n = 1
        comm = '%s %s --train %s -s 1,%s,1,%s --devel 5%% --encoding utf8 --write-model %s_%s > %s.log' % (self.g2p_path, self.lts_tool,
                                                                                                       self.train_file,
                                                                                                       self.max_graphone_letters, \
                                                                                                       self.max_graphone_phones,
                                                                                                       lts_model, n,
                                                                                                       lts_model)
        print(comm)
        os.system(comm)
        n += 1
        # train an ngram model according to self.lts_gram_length
        while n <= self.lts_gram_length:
            comm = '%s %s --model %s_%s --ramp-up --train %s --devel 5%% --encoding utf8 --write-model %s_%s >> %s.log' % (
                self.g2p_path, self.lts_tool, lts_model, n - 1, self.train_file, lts_model, n, lts_model)
            print(comm)
            os.system(comm)
            n += 1
        shutil.copy('%s_%s' % (lts_model, self.lts_gram_length), lts_model)
        self.lts_model = lts_model

    ########################################################################
    #
    #       TESTING
    #
    ########################################################################

    def test_g2p(self, test_file, test_out):
        multi_transcr = multiple_transcripts.MultipleTranscripts()
        in_file = open(test_file)
        test_data = in_file.readlines()
        errors = []
        per_count = 0
        phone_count = 0
        subst_tuples = {}
        sum_PER = 0.0
        for line in test_data:
            if len(line.split('\t')) != 2:
                print("Error in line: " + line)
            else:
                word, transcr = line.split('\t')

            pron = self.get_oov_pronunciation(word)
            PER = self.compute_PER(transcr.strip(), pron)
            sum_PER += PER

            if pron != transcr.strip():
                res = multi_transcr.compare_transcripts(pron, transcr.strip())
                errors.append(word + '\tg2p: ' + pron + '\ttest: ' + transcr.strip() + ' - ' + str(res))
                per_count += len(res)

                for diff_tuple in res:
                    if diff_tuple in subst_tuples:
                        subst_tuples[diff_tuple] = subst_tuples[diff_tuple] + 1

                    elif diff_tuple[::-1] in subst_tuples:
                        # we don't care about the order in the tuple, ('k', 'c') equivalent to ('c', 'k')
                        subst_tuples[diff_tuple[::-1]] = subst_tuples[diff_tuple[::-1]] + 1

                    else:
                        subst_tuples[diff_tuple] = 1

            phone_count += len(transcr.strip().split())

        print('PER: ' + str(sum_PER / float(len(test_data))))
        print('Errors: ' + str(per_count))
        print('Erroneous words: ' + str(len(errors)))
        print('WER: ' + str((len(errors) / len(test_data)) * 100.0) + '%')
        with open(test_out + '_phone_errors.txt', 'w') as f:
            for diff in sorted(subst_tuples, key=lambda x: subst_tuples[x], reverse=True):
                f.write(
                    str(diff) + '\t' + str(subst_tuples[diff]) + '\n')

        with open(test_out + '_errors.txt', 'w') as f:
            for entry in errors:
                f.write(entry + '\n')

    def get_oov_pronunciation(self, word):

        escaped_word = "'" + word.lower() + "'"

        comm = '%s echo %s | %s  --model %s --encoding utf8 --apply -' % (self.g2p_path, \
                                                                          escaped_word, self.lts_tool, self.lts_fname)


        pronun = subprocess.check_output(comm.encode('utf8'), shell=True, stderr=subprocess.STDOUT)

        ## remove the 'stack usage' output line -- its position varies:
        pronun = unicodedata.normalize('NFKD', pronun.decode('utf-8'))
        pronun = pronun.strip(' \n').split('\n')

        assert len(pronun) >= 2, str(pronun)  ## ==   -->   >=     to handle extra warnings

        normalised_word = unicodedata.normalize('NFKD', word)
        for line in pronun:
            if 'stack usage' not in line and normalised_word in line:
                pronun = line

        (outword, pronun) = re.split('\s+', pronun, maxsplit=1)
        outword = unicodedata.normalize('NFKD', outword)
        word = unicodedata.normalize('NFKD', word)

        if outword != word:
            print(outword + ' as outword does not match ' + word)

        return pronun


    @staticmethod
    def compute_PER(transcr, hyp):
        """
        Phoneme-error-rate: edit distance between the automatic transcription result (candidate) and reference
        pronunciation divided by the number of phonemes in the reference pronunciation.
        :param transcr: reference transcription
        :param hyp: hypothesis, automatic transcription
        :return: phone-error-rate (PER)
        """
        dist = Levenshtein.distance(transcr, hyp)
        if dist > 0:
            # missing or inserting '_h' or '_0' counts as ed. dist 2, remove underscore to get the correct dist. 1
            trimmed_transcr = transcr.replace('_', '')
            trimmed_hyp = hyp.replace('_', '')
            trimmed_transcr = trimmed_transcr.replace(' ', '')
            trimmed_hyp = trimmed_hyp.replace(' ', '')
            dist = Levenshtein.distance(trimmed_transcr, trimmed_hyp)
        transcr_arr = transcr.split()
        PER = float(dist / len(transcr_arr))
        return PER



def get_args_parser():

    parser = argparse.ArgumentParser(
        description='Trains a g2p model or tests g2p results',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--model', default='g2p_model_' + time.strftime("%Y%m%d-%H%M%S"),
                        help='The name of the model to train or use. It is sensible to use a more informative name,'
                             ' e.g. training data and the model parameters used.')
    parser.add_argument('--train_file', default='',
                        help='Train a g2p model using this file. A required argument in train mode.')
    parser.add_argument('--test_file', default='',
                        help='Transcribe the words from this file using a given model, test against the transcripts in this file.'
                             ' A required argument in test mode.')
    parser.add_argument('--test_out', default='testresults_' + time.strftime("%Y%m%d-%H%M%S"))
    parser.add_argument('--max_letters', default=1,
                        help='Max letters per graphone.')
    parser.add_argument('--max_phones', default=1,
                        help='Max phones per graphone.')
    parser.add_argument('--gram_len', default=3,
                        help='Number of graphones to take into account.')

    return parser

def main():

    parser = get_args_parser()
    args = parser.parse_args()

    training = True
    if args.train_file:
        pass
    elif args.test_file:
        training = False
    else:
        print('Please provide a training file for training or a test file for testing!')
        parser.print_help()
        exit(1)


    if training:
        experiment = G2P_Experiment(args.model, train_file=args.train_file)
        experiment.set_parameters()
        print('train model ...')
        experiment.train_sequitur_g2p()

    else:
        experiment = G2P_Experiment(args.model)
        print('testing ...')
        experiment.test_g2p(args.test_file, args.test_out)


if __name__ == '__main__':

    main()
