#!/usr/bin/env python3

"""

Filters words having multiple transcriptions and writes to file. Also keeps track
on unique words belonging to this file and writes to another file.
Takes a pronunciation dictionary as an input.

"""
import sys
import re


class MultipleTranscripts:

    KEEP_BOTH = 'KEEP_BOTH'
    NO_CHOICE = 'NO_CHOICE'

    def __init__(self):
        # collective lists, sets and dictionaries
        self.filtered_dictionary = []
        self.no_choice_made = []
        self.lines2write = []
        self.transcript_diffs_stats = {}
        self.words_with_multiple_transcr = set()

        # tmp variables for keeping record of previeous entry
        self.last_word = ''
        self.last_line = ''
        self.last_single = ''
        self.multiple_transcripts = []

    def process_dictionary(self, filename):

        for line in open(filename).readlines():
            word, transcr = line.split('\t')
            if word == self.last_word:
                # we have multiple transcripts, collect
                if not self.multiple_transcripts:
                    self.multiple_transcripts.append(self.last_line)
                self.multiple_transcripts.append(line)
                self.words_with_multiple_transcr.add(word)
                self.last_single = ''
            elif self.multiple_transcripts:
                self._process_multiple_transcripts()

            else:
                # a single entry or the first of more entries
                if self.last_single:
                    self.filtered_dictionary.append(self.last_single)
                self.last_single = line

            self.last_word = word
            self.last_line = line

    def _process_multiple_transcripts(self):

        self.lines2write.extend(self.multiple_transcripts)
        transcr_diffs, chosen_transcript = self._transcript_diff(self.multiple_transcripts)
        if chosen_transcript == self.KEEP_BOTH:
            self.filtered_dictionary.extend(self.multiple_transcripts)
        elif chosen_transcript != self.NO_CHOICE:
            self.filtered_dictionary.append(self.last_word + '\t' + chosen_transcript)
        else:
            self.no_choice_made.extend(self.multiple_transcripts)
        self._update_transcript_diffs_stats(transcr_diffs)
        self.multiple_transcripts = []

    def _choose_transcript(self, result_arr, transcr1, transcr2, word):
        # chose the preferred transcript from transcr1 and transcr2
        # they might be identical, there might not be a decision possible
        # return either the preferred transcript or a KEEP_BOTH or NO_CHOICE variable

        if transcr1 == transcr2:
            return transcr1

        if ('k', 'x') in result_arr:
            return transcr1
        if ('x', 'k') in result_arr:
            return transcr2
        if ('n̥', 'n') in result_arr or ('ŋ̊', 'ŋ') in result_arr or ('ɲ̊', 'ɲ') in result_arr or ('m̥', 'm') in result_arr or ('r̥', 'r') in result_arr:
            return transcr1
        if ('n','n̥') in result_arr or ('ŋ', 'ŋ̊') in result_arr or ('ɲ', 'ɲ̊') in result_arr or ('m', 'm̥') in result_arr or ('r', 'r̥') in result_arr:
            return transcr2
        if ('l̥', 'l') in result_arr or ('t', '') in result_arr:
            if re.match('.+ll[aáeéiíoóuúyýöæ].*', word):
                return self.KEEP_BOTH
            else:
                return transcr1
        if ('l', 'l̥') in result_arr or ('', 't') in result_arr:
            if re.match('.+ll[aáeéiíoóuúyýöæ].*', word):
                return self.KEEP_BOTH
            else:
                return transcr2
        if ('c', 'k') in result_arr or ('h k', 'x') in result_arr or ('', 'k') in result_arr:
            return transcr1
        if ('k', 'c') in result_arr or ('x', 'h k') in result_arr or ('k', '') in result_arr:
            return transcr2

        else:
            return self.NO_CHOICE


    def _compare_same_len(self, transcr_arr1, transcr_arr2):
        result = []
        for i in range(len(transcr_arr1)):
            if transcr_arr1[i] != transcr_arr2[i]:
                result.append((transcr_arr1[i], transcr_arr2[i]))

        return result


    def _init_match_matrix(self, arr1, arr2):
        """
        Initializes a len(arr1) x len(arr2) matrix and set each matching cell to 'True'
        :param arr1:
        :param arr2:
        :return:
        """
        # create a arr1 x arr2 matrix
        match_matrix = [None] * len(arr1)
        for i in range(len(arr1)):
            match_matrix[i] = [None] * len(arr2)

        end_1 = len(arr1)
        end_2 = len(arr2)
        # set matching cells to 'True'
        for i in range(len(arr2)):
            if i > end_1 or i > end_2:
                # already checked all indices upto index i from the end
                break
            if arr1[i] == arr2[i]:
                match_matrix[i][i] = True

            else:
                # check matches from end
                while end_1 > i and end_2 > i:
                    end_1 -= 1
                    end_2 -= 1
                    if arr1[end_1] == arr2[end_2]:
                        match_matrix[end_1][end_2] = True
                    else:
                        break

                # find matches with uneven indices, arr2[i] is the anchor, we search for matches in arr1
                for j in range(i, end_1):
                    if arr2[i] == arr1[j]:
                        match_matrix[j][i] = True
                        break

        return match_matrix


    def _compare_transcripts(self, transcr1, transcr2):
        """
        Compare two transcripts and extract substitutions and/or insertions.
        Example:
        transcr1: r eiː k j a v iː k ʏ r v eiː j ɪ
        transcr2: r eiː c a v i k ʏ r v ei j ɪ

        returns a list of tuples containing non-matching phones: [('k j', 'c'), ('iː', 'i'), ('eiː', 'ei')]

        Could easily be extended to collect the corresponding indices, but no need for that by now.

        :param transcr1:
        :param transcr2:
        :return: a list of tuples of non-matching phones
        """

        arr1 = transcr1.split()
        arr2 = transcr2.split()
        result = []

        if len(arr1) == len(arr2):
            return self._compare_same_len(arr1, arr2)

        if len(arr1) < len(arr2):
            return self._compare_transcripts(transcr2, transcr1)

        match_matrix = self._init_match_matrix(arr1, arr2)

        # create a list of tuples with cell coordinates of all 'True' cells
        matches = [(index, row.index(True)) for index, row in enumerate(match_matrix) if True in row]

        # find all non-matching cells and collect inserts and substitutions
        last_tup_1 = -1
        last_tup_2 = -1
        for i in range(len(matches)):
            tup = matches[i]
            # no gap, hence no substitution/insertion before the current match
            # e.g.: (0,0), (1,1) etc., or (5,4), (6,5), etc.
            if tup[0] == last_tup_1 + 1 and tup[1] == last_tup_2 + 1:
                last_tup_1 = tup[0]
                last_tup_2 = tup[1]
            else:
                sub1 = []
                sub2 = []
                # collect the phones from the gap
                for j in range(last_tup_1 + 1, tup[0]):
                    sub1.append(arr1[j])
                for j in range(last_tup_2 + 1, tup[1]):
                    sub2.append(arr2[j])

                sub_tup = (' '.join(sub1), ' '.join(sub2))

                result.append(sub_tup)
                last_tup_1 = tup[0]
                last_tup_2 = tup[1]
                #if sub_tup == ('', ''):
                    #print(' '.join(arr1) + ' -- ' + ' '.join(arr2))

        # insertion at the end of arr1?
        if len(arr1) > last_tup_1 + 1:
            ins = arr1[last_tup_1 + 1:]
            ins_tup = (' '.join(ins), '')
            #print(' '.join(arr1) + ' -- ' + ' '.join(arr2))
            result.append(ins_tup)

        return result


    def _transcript_diff(self, entry_arr):
        """
        Find the differences in transcripts of the same word.
        :param entry_arr: array of entries 'word\tt r a n s c r i p t'
        :return: array of tuples [(diff1a, diff2a, ...), (diff1b, diff2b, ...)]
        """

        same_word = set()
        transcripts = []
        for entry in entry_arr:
            word, transcr = entry.split('\t')
            same_word.add(word)
            if len(same_word) > 1:
                raise ValueError("not all words in the input are the same! " + str(same_word))

            transcripts.append(transcr)

        result = []
        if len(transcripts) == 2:
            result = self._compare_transcripts(transcripts[0], transcripts[1])
            chosen_transcript = self._choose_transcript(result, transcripts[0], transcripts[1], word)

        elif len(transcripts) > 2:
            reference_transcr = transcripts[0]
            for i in range(1,len(transcripts)):
                result.extend(self._compare_transcripts(reference_transcr, transcripts[i]))
                chosen_transcript = self._choose_transcript(result, reference_transcr, transcripts[i], word)

        else:
            raise ValueError("No transcripts to compare! " + str(transcripts))

        return result, chosen_transcript


    def _update_transcript_diffs_stats(self, diffs):

        for diff_tuple in diffs:
            if diff_tuple in self.transcript_diffs_stats:
                val = self.transcript_diffs_stats[diff_tuple]
                val.append(self.last_word)
                self.transcript_diffs_stats[diff_tuple] = val
            elif diff_tuple[::-1] in self.transcript_diffs_stats:
                # we don't care about the order in the tuple, ('k', 'c') equivalent to ('c', 'k')
                val = self.transcript_diffs_stats[diff_tuple[::-1]]
                val.append(self.last_word)
                self.transcript_diffs_stats[diff_tuple[::-1]] = val

            else:
                self.transcript_diffs_stats[diff_tuple] = [self.last_word]




def main():
    transcr_file = sys.argv[1]

    processor = MultipleTranscripts()
    processor.process_dictionary(transcr_file)

    words_outfile = 'words_with_multiple_transcripts.txt'
    multiple_transcripts_outfile = 'multiple_transcripts.csv'



    print("Number of words with multiple transcripts: " + str(len(processor.words_with_multiple_transcr)))

    out = open(words_outfile, 'w')
    for w in processor.words_with_multiple_transcr:
        out.write(w + '\n')

    out = open(multiple_transcripts_outfile, 'w')
    out.writelines(processor.lines2write)

    out = open('dict_step_5.txt', 'w')
    out.writelines(processor.filtered_dictionary)

    out = open('no_choice.txt', 'w')
    out.writelines(processor.no_choice_made)

    out = open('transcript_diff_stats.txt', 'w')
    for diff in sorted(processor.transcript_diffs_stats, key=lambda x: len(processor.transcript_diffs_stats[x]), reverse=True):
        out.write(str(diff) + '\t' + str(processor.transcript_diffs_stats[diff]) + '\t' + str(len(processor.transcript_diffs_stats[diff])) + '\n')

    out = open('transcript_stats_only.txt', 'w')
    for diff in sorted(processor.transcript_diffs_stats, key=lambda x: len(processor.transcript_diffs_stats[x]), reverse=True):
        out.write(
            str(diff) + '\t' + str(len(processor.transcript_diffs_stats[diff])) + '\n')


if __name__ == '__main__':
    main()
