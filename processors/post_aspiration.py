#!/usr/bin/env python3

# Ensures that plosives in the beginning of a word, followed by a vowel or a liquid (r)
# are transcribed with post aspiration (/pʰtʰkʰ/).
# Input file format: <word>\t<ipa-transcript>[further columns not considered]

import sys, csv, re


def write_list(filename, list2write):

    with open(filename, 'w') as f:
        for line in list2write:
            f.write(line)


def find_postaspir(input_file, out_dir):

    c_postaspir = []
    k_postaspir = []
    p_postaspir = []
    t_postaspir = []

    for line in input_file:
        word, transcr = line.strip().split('\t')
        if re.search('cʰ', transcr):
            c_postaspir.append(line)
        if re.search('kʰ', transcr):
            k_postaspir.append(line)
        if re.search('pʰ', transcr):
            p_postaspir.append(line)
        if re.search('tʰ', transcr):
            t_postaspir.append(line)

    write_list(out_dir + '/c_postaspir.txt', c_postaspir)
    write_list(out_dir + '/k_postaspir.txt', k_postaspir)
    write_list(out_dir + '/p_postaspir.txt', p_postaspir)
    write_list(out_dir + '/t_postaspir.txt', t_postaspir)


def find_beginning_postaspir(input_file, out_dir):
    c_postaspir = []
    k_postaspir = []
    p_postaspir = []
    t_postaspir = []

    for line in input_file:
        word, transcr = line.strip().split('\t')
        if re.match('cʰ.+', transcr):
            c_postaspir.append(line)
        if re.match('kʰ.+', transcr):
            k_postaspir.append(line)
        if re.match('pʰ.+', transcr):
            p_postaspir.append(line)
        if re.match('tʰ.+', transcr):
            t_postaspir.append(line)

    write_list(out_dir + '/c_beginningpostaspir.txt', c_postaspir)
    write_list(out_dir + '/k_beginningpostaspir.txt', k_postaspir)
    write_list(out_dir + '/p_beginningpostaspir.txt', p_postaspir)
    write_list(out_dir + '/t_beginningpostaspir.txt', t_postaspir)



def find_missing_postaspir(input_file, out_dir):
    c_postaspir = []
    k_postaspir = []
    p_postaspir = []
    t_postaspir = []

    for line in input_file:
        word, transcr = line.split('\t')
        if re.match('[pP][aeiouyáéíóúýöæjlrv].*', word):
            if not re.match('pʰ.+', transcr):
                p_postaspir.append(line)
        if re.match('[tT][aeiouyáéíóúýöæjrv].*', word):
            if not re.match('tʰ.+', transcr):
                t_postaspir.append(line)
        if re.match('[kK][aouáóúölrv].*', word):
            if not re.match('kʰ.+', transcr):
                k_postaspir.append(line)
        if re.match('[hH]v[aeiouyáéíóúýöæjr].*', word):
            if not re.match('kʰ.+', transcr):
                k_postaspir.append(line)
        if re.match('[kK][eiéíyýæj].*', word):
            if not re.match('cʰ.+', transcr):
                c_postaspir.append(line)

    write_list(out_dir + '/c_missingpostaspir.txt', c_postaspir)
    write_list(out_dir + '/k_missingpostaspir.txt', k_postaspir)
    write_list(out_dir + '/p_missingpostaspir.txt', p_postaspir)
    write_list(out_dir + '/t_missingpostaspir.txt', t_postaspir)


def ensure_postaspir(input_file):
    corrected = []
    for line in input_file:
        word, transcr = line.split('\t')
        if re.match('[pP][aeiouyáéíóúýöæjlrv].*', word):
            if not re.match('pʰ.+', transcr):
                new_ipa = transcr.replace('p', 'pʰ', 1)
                transcr = new_ipa
        if re.match('[tT][aeiouyáéíóúýöæjrv].*', word):
            if not re.match('tʰ.+', transcr):
                new_ipa = transcr.replace('t', 'tʰ', 1)
                transcr = new_ipa
        if re.match('[kK][aouáóúölrv].*', word):
            if not re.match('kʰ.+', transcr):
                new_ipa = transcr.replace('k', 'kʰ', 1)
                transcr = new_ipa
        if re.match('[hH]v[aeiouyáéíóúýöæ].*', word):
            if not re.match('kʰ.+', transcr):
                new_ipa = transcr.replace('k', 'kʰ', 1)
                transcr = new_ipa
        if re.match('[kK][eiéíyýæj].*', word):
            if not re.match('cʰ.+', transcr):
                new_ipa = transcr.replace('c', 'cʰ', 1)
                transcr = new_ipa

        #print(word + '\t' + transcr.strip())
        corrected.append(word + '\t' + transcr.strip())
    return corrected


def main():
    import argparse
    parser = argparse.ArgumentParser(description='post aspiration',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input file')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output file')

    args = parser.parse_args()

    dict_list = args.input.readlines()
    #find_postaspir(dict_list)
    find_missing_postaspir(dict_list)
    find_beginning_postaspir(dict_list)
    corrected = ensure_postaspir(dict_list)


if __name__ == '__main__':
    main()
