#!/usr/bin/env python
# -*- coding: utf-8 -*-
## osw: received from Peter Smit on 23 Aug 2012
"""
Morfessor, implemented in python.

Runs on PyPy, Python3.2+ and Python2.7+ (in order of preference and speed)

For nice progress indications when training, install progressbar from pypi. For example with `easy_install progressbar`
"""



from argparse import ArgumentParser, SUPPRESS
from collections import Counter, namedtuple
import logging
from math import log
from random import shuffle, seed

from logging import getLogger, DEBUG, INFO
from sys import stderr

from io import open
from time import time


try:
    from math import gamma
except ImportError:
    from scipy.special import gamma


def _progress(iter_func):
    """
    Decorator for displaying a progress bar when iterating through a random word list
    """
    try:
        from progressbar import ProgressBar

        def i(*args, **kwargs):
            if logging.getLogger(__name__).isEnabledFor(INFO):
                return ProgressBar()(iter_func(*args, **kwargs))
            else:
                return iter_func(*args, **kwargs)

        return i
    except ImportError:
        pass

    return iter_func


def _get_file_object(s, encoding):
    """
    Be ignorant whether a file is a string or a file_obj
    """
    if isinstance(s, file):
        return s
    elif isinstance(s, basestring):
        return open(s, encoding=encoding)
    else:
        sys.exit("morph file "+s + "not found")

MorphInfo = namedtuple('MorphInfo', ['word_count', 'morph_count', 'split_location'])


class MorphModel:
    def __init__(self, options=None):
        """
        Initialize MorphModel. Options, if provided, must be a dictionary like object. It must quack like a dict
        """
    
        if options is None:
            options = {}
    

        #Initialize options
        self.encoding = 'utf-8'

        # harder morph length constraints, not absolute though
        self.max_len = 10 #2
        self.min_len = 5
        #self.use_gamma = False
        #self.gamma_params = (0, 0)
        self.use_gamma = True
        self.gamma_params = (8.0, 1.0)
        self.finish_threshold = 0.005
        if options.get('gammalendistr',None) is not None:
            self.use_gamma = True
            self.gamma_params = tuple(options['gammalendistr'])

        self.use_zipf = False
        self.zipf_param = 0

        if options.get('zipffreqdistr',None) is not None:
            self.use_zipf = True
            self.zipf_param = options['zipffreqdistr']
        
        if options.get('finish', None) is not None:
            self.finish_threshold = options['finish']

        if options.get('encoding',None) is not None:
            self.encoding = options.get('encoding')

        #        self.rand_seed = options.rand
        seed(options.get('rand',time()))

        # Define object variables
        self.morph_log_prob = {}
        self.num_morph_tokens = 0
        self.num_morph_types = 0
        self.log_num_morph_tokens = 0

        self.log2hapax = log(1 - self.zipf_param) / log(2)
        self.log2coeff = 1 / log(2)

        self.morph_info = {}
        self.num_virtual_morph_types = 0

        self.log_token_sum = 0
        self.freq_distr_cost = 0
        self.len_distr_cost = 0

        self.log_gamma_pdf = [0.0]

        self.letter_log_prob = {}

        self.num_letter_tokens = 0

        self.morph_string_cost = 0

        self.logger = getLogger(__name__)

        self.model_loaded = False

    def load(self, f):
        """
        Load a segmentation file into this model, enabling viterbi-segmentation
        """
        file_obj = _get_file_object(f, self.encoding)

        self.logger.info("Start loading model %s" % file_obj.name)

        morph_count = Counter()
        for line in file_obj:
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue
            try:
                word, count = MorphModel._read_word(line)
                morphs = word.split(" + ")
                for morph in morphs:
                    morph_count[morph.strip()] += count
                    self.num_morph_tokens += count
            except ValueError:
                exit("Illegal line format: %s" % line)

        self.log_num_morph_tokens = log(self.num_morph_tokens)

        for morph, count in morph_count.items():
            self.morph_log_prob[morph] = self.log_num_morph_tokens - log(count)

        self.num_morph_types = len(self.morph_log_prob)

        self.logger.info("Finished loading model")
        self.logger.info("Number of morph tokens: %d" % self.num_morph_tokens)
        self.logger.info("Number of morph types: %d" % self.num_morph_types)

    def viterbi_segment_word(self, word):
        """
        Do viterbi segmentation of word and return morphs. Load the model before using this method.
        """
        if len(self.morph_log_prob) == 0:
            raise Exception("Load model first")
        print "segmenting"
        T = len(word)
        bad_likelihood = (T + 1) * self.log_num_morph_tokens
        pseudo_infinite_cost = (T + 1) * bad_likelihood

        delta = [0]
        psi = [0]

        for t in range(1, T + 1):

            best_delta = pseudo_infinite_cost
            best_l = 0

            for l in range(1, t + 1):

 
                morph = word[t - l:t]


                if morph in self.morph_log_prob:
                    logp = self.morph_log_prob[morph]
                elif l == 1:
                    logp = bad_likelihood
                else:

                    continue

                cur_delta = delta[t - l] + logp
                
                if cur_delta < best_delta:

                    best_delta = cur_delta
                    best_l = l

            delta.append(best_delta)
            psi.append(best_l)

        morphs = []
        t = T
        while t > 0:
            morphs.insert(0, word[t - psi[t]:t])
            t -= psi[t]

        return morphs

    def train(self, f):
        """
        Train model from word count file f. The file can be both a filename string and file object.
        """
        file_obj = _get_file_object(f, self.encoding)

        num_word_tokens = 0
        num_word_types = 0
        max_word_length = 0
        letter_count = Counter()

        num_corpus_letter_tokens = 0

        self.morph_info = {}

        self.logger.info("Start reading data file %s" % file_obj.name)

        for word, count in Counter(dict([MorphModel._read_word(l) for l in file_obj])).items():
            self.morph_info[word] = MorphInfo(count, count, 0)

            num_word_tokens += count
            num_word_types += 1

            if len(word) > max_word_length:
                max_word_length = len(word)

            if not self.use_gamma:
                word += ' '

            for letter in word:
                letter_count[letter] += count

            num_corpus_letter_tokens += count * len(word)

        self.logger.info("Finished reading data file")

        self.logger.info("Start model initialization")
        log_num_corpus_letter_tokens = log(num_corpus_letter_tokens)
        self.letter_log_prob = {k: log_num_corpus_letter_tokens - log(v) for k, v in letter_count.items()}

        #If necessary, pre-initialize all loggamma values
        if self.use_gamma:
            mcl, beta = self.gamma_params
            alpha = mcl / beta + 1
            self.log_gamma_pdf.extend([log(gamma(alpha)) + alpha * log(beta) - (alpha - 1) * log(i) + i / beta for i in
                                       range(1, max_word_length + 1)])

        for morph, mi in sorted(self.morph_info.items()):
            del self.morph_info[morph]
            self._increase_morph_count(morph, mi.word_count)
            self.morph_info[morph] = mi

        new_cost = self._get_total_cost()
        old_cost = (new_cost + num_word_types * self.finish_threshold) * 2

        self.logger.info("Finished model initialization")

        self.logger.info("Start cost: %.2f" % new_cost)
        iteration = 0
        while new_cost < (old_cost - num_word_types * self.finish_threshold):
            iteration += 1
            self.logger.info("Start iteration %d" % iteration)

            for word in self._get_random_word_list():
                self._resplit_node(word)

                if self.logger.isEnabledFor(DEBUG):
                    self.logger.debug("%s: %s" % (word, ' + '.join(self._expand_morph(word))))

                    self.logger.debug("%.1f %.1f %.1f %.1f %d %d %d" % (
                        self.len_distr_cost, self.freq_distr_cost, self.morph_string_cost, self.log_token_sum,
                        self.num_morph_types, self.num_morph_tokens, self.num_virtual_morph_types))

            old_cost = new_cost
            new_cost = self._get_total_cost()
            self.logger.info("Cost on end of iteration %d: %.2f" % (iteration, new_cost))

    def _expand_morph(self, morph):
        mi = self.morph_info[morph]

        morphs = []

        if mi.split_location > 0:
        
            morphs.extend(self._expand_morph(morph[:mi.split_location]))
            morphs.extend(self._expand_morph(morph[mi.split_location:]))
        else:
            morphs.append(morph)
        return morphs

    @_progress
    def _get_random_word_list(self):
        words = [morph for morph, mi in self.morph_info.items() if mi.word_count > 0]
        shuffle(words)
        return words

    def _increase_morph_count(self, morph, delta_count):
        mi = self.morph_info.get(morph, MorphInfo(0, 0, 0))

        new_morph_count = mi.morph_count + delta_count
        assert new_morph_count >= 0

        if new_morph_count == 0:
            del self.morph_info[morph]
            self.num_virtual_morph_types -= 1
        else:
            self.morph_info[morph] = MorphInfo(mi.word_count, new_morph_count, mi.split_location)
            if mi.morph_count == 0:
                self.num_virtual_morph_types += 1

        if mi.split_location > 0:
            self._increase_morph_count(morph[:mi.split_location], delta_count)
            self._increase_morph_count(morph[mi.split_location:], delta_count)

        else:
            self.num_morph_tokens += delta_count

            if mi.morph_count > 0:
                self.log_token_sum -= mi.morph_count * log(mi.morph_count)

                if self.use_zipf:
                    self.freq_distr_cost -= -log(
                        (mi.morph_count ** self.log2hapax) - ((mi.morph_count + 1) ** self.log2hapax))

            if new_morph_count > 0:
                self.log_token_sum += new_morph_count * log(new_morph_count)

                if self.use_zipf:
                    self.freq_distr_cost += -log(
                        (new_morph_count ** self.log2hapax) - ((new_morph_count + 1) ** self.log2hapax))

            if (mi.morph_count == 0 and new_morph_count > 0) or (new_morph_count == 0 and mi.morph_count > 0):
                if new_morph_count == 0:
                    sign = -1
                else:
                    sign = 1

                self.num_morph_types += sign

                morph_len = len(morph)
                if self.use_gamma:
                    if (morph_len) > self.max_len:
                        self.len_distr_cost += sign * self.log_gamma_pdf[morph_len]*pow(morph_len, 3)
                    else:
                        self.len_distr_cost += sign * self.log_gamma_pdf[morph_len]
                   
                else:
                    if (morph_len) > self.max_len:
                         self.len_distr_cost += sign * self.letter_log_prob[' ']*pow(morph_len,3)
                    elif (morph_len) < self.min_len:
                        self.len_distr_cost += sign * self.letter_log_prob[' ']*pow((self.max_len-morph_len),3)
                    else:
                        self.len_distr_cost += sign * self.letter_log_prob[' ']
                    morph_len += 1

                self.num_letter_tokens += sign * morph_len

                for letter in morph:
                    self.morph_string_cost += sign * self.letter_log_prob[letter]

    def _get_total_cost(self):
        corpus_morph_cost = self.num_morph_tokens * log(self.num_morph_tokens) - self.log_token_sum
        factorial_num_morph_types = self.num_morph_types * (1 - log(self.num_morph_types))

        if not self.use_zipf:
            self.freq_distr_cost = 0

            if self.num_morph_tokens > 2:
                self.freq_distr_cost += (self.num_morph_tokens - 1) * log(self.num_morph_tokens - 2)
            if self.num_morph_types > 2:
                self.freq_distr_cost -= (self.num_morph_types - 1) * log(self.num_morph_types - 2)
            if self.num_morph_tokens - self.num_morph_types > 1:
                self.freq_distr_cost -= (self.num_morph_tokens - self.num_morph_types) * log(
                    self.num_morph_tokens - self.num_morph_types - 1)

        return self.log2coeff * (
            corpus_morph_cost + self.morph_string_cost + self.len_distr_cost + self.freq_distr_cost +
            factorial_num_morph_types)


    def _resplit_node(self, morph):
        mi = self._remove_morph(morph)

        self._increase_morph_count(morph, mi.morph_count)
        min_cost = self._get_total_cost()
        self._increase_morph_count(morph, -mi.morph_count)

        split_location = 0

        vow =  {'a','e','i','o','u','y', u'ä',u'ö', u'å'}
        cons =  {'b','c','d','f','g','h','j','k','l','m','n','p','r','s','t','v','w','x','z'}
        for i in range(1, len(morph)):
            """
            if morph[i-1] in cons and morph[i] in vow:
                continue

            if i< len(morph)-1 and morph[i] in cons and morph[i+1] in cons and morph[i-1] in vow:
                print morph[i-1], morph[i], morph[i+1]
                continue
            """
            #if len(morph[:i]) < 3:
            #        continue

            self._increase_morph_count(morph[:i], mi.morph_count)
            self._increase_morph_count(morph[i:], mi.morph_count)
            cost = self._get_total_cost()
            #if morph[i-1] in cons and morph[i] in vow:
            #    cost/=1.1
            #if morph[i] in cons and morph[i-1] in vow:
            #    cost/=1.1
            """
            if morph[i-1] in vow and morph[i] in vow:
                cost*=1.0001
            if i < len(morph)-1 and morph[i] in cons and morph[i-1] in vow:
                if morph[i+1] in vow:
                    cost/=5.0
                else:
                    cost*=100000.0
                    
            if (morph[i-1] in cons and morph[i] in cons):
                    cost/=5.0
            """
            self._increase_morph_count(morph[:i], -mi.morph_count)
            self._increase_morph_count(morph[i:], -mi.morph_count)
            
            #if morph[:i] in cons or morph[i:] in cons:
            #    cost = min_cost+1
                

            if cost <= min_cost:

                min_cost = cost
                #print cost, min_cost, morph, morph[:i], morph[i:]
                split_location = i
               
        if split_location > 0:
            if morph not in self.morph_info:
                self.num_virtual_morph_types += 1
            self.morph_info[morph] = MorphInfo(mi.word_count, mi.morph_count, split_location)

            self._increase_morph_count(morph[:split_location], mi.morph_count)
            self._increase_morph_count(morph[split_location:], mi.morph_count)
            self.logger.debug("%s --split --> %s + %s" % (morph, morph[:split_location], morph[split_location:]))

            self._resplit_node(morph[:split_location])
            self._resplit_node(morph[split_location:])
        else:
            self.morph_info[morph] = MorphInfo(mi.word_count, 0, 0)
            self._increase_morph_count(morph, mi.morph_count)
            self.logger.debug("%s --no-split--> %s" % (morph, morph))

    def _remove_morph(self, morph):
        assert morph in self.morph_info

        mi = self.morph_info[morph]
        self._increase_morph_count(morph, -mi.morph_count)
        return mi

    def save(self, filename):
        f = open(filename, "w")
        for morph, mi in sorted(self.morph_info.items()):
            if mi.word_count > 0:
                try:
                    f.write("%d %s\n" % (mi.word_count, ' + '.join(self._expand_morph(morph))))
                except:
                    pass

    def print_segmentation(self):
        for morph, mi in sorted(self.morph_info.items()):
            if mi.word_count > 0:
               try:
                   print("%d %s" % (mi.word_count, ' + '.join(self._expand_morph(morph))))
               except:
                   pass

    @staticmethod
    def _read_word(line):
        try:
            count, word = line.split(None, 1)
            word = word.strip()
            count = int(count)
        except ValueError:
            count = 1
            word = line.strip()

        return word, count

    def morph_length_distribution(self):
        morph_lenght_dist = Counter()

        for morph, info in self.morph_info.items():
            if info.morph_split > 0:
                morph_lenght_dist[len(morph)] += 1

        return morph_lenght_dist


def main():
    logging.basicConfig(stream=stderr, level=INFO)

    a = ArgumentParser()
    a.add_argument('-data', dest='data', required=True, metavar='WORDLIST',
                   help="a text file (the corpus) consisting of one word per line. The word may be preceded by a word"\
                        " count (separated by whitespace), otherwise a count of one is assumed. If the same word "\
                        "occurs many times, the counts are accumulated.")
    a.add_argument('-finish', dest='finish', metavar='float', type=float, default=0.005,
                   help="convergence threshold. From one pass over all input words to the next, "\
                        "if the overall coding length in bits (i.e. logprob) of the lexicon together with the corpus "\
                        "improves less than this value times the number of word types (distinct word forms) in the "\
                        "data, the program stops. (If this value is small the program runs for a longer time and the "\
                        "result is in principle more accurate. However, the changes in word splittings during the "\
                        "last training epochs are usually very small.) The value must be within the range: 0 < float "\
                        "< 1. Default 0.005")
    a.add_argument('-rand', dest='rand', metavar='int', type=int, default=0,
                   help="random seed that affects the sorting of words when processing them. Default 0")
    a.add_argument('-gammalendistr', dest='gammalendistr', type=float, metavar='float', nargs=2,
                   help="Use Gamma Length distribution with two parameters. Float1 is the prior for the most common "\
                        "morph length in the lexicon, such that 0 < float1 <= 24*float2. Float2 is the beta value of "\
                        "the Gamma pdf, such that beta > 0. The beta value affects the wideness of the morph length "\
                        "distribution. The higher beta, the wider and less discriminative the distribution. If this "\
                        "option is omitted, morphs in the lexicon are terminated with  an end-of-morph character, "\
                        "which corresponds to an exponential pdf for morph lengths. Suggested values: float1 = 7.0, "\
                        "float2 = 1.0 ")
    a.add_argument('-zipffreqdistr', dest='zipffreqdistr', type=float, metavar='float',
                   help="Use Zipf Frequency distribution with paramter float1 for the proportion of morphs in the "\
                        "lexicon that occur only once in the data (hapax legomena): 0 < value < 1. If this option is "\
                        "omitted a (non-informative) morph frequency distribution based on enumerative coding is used"\
                        " instead. Suggested value: 0.5")
    a.add_argument('-load', dest='load', metavar='filename',
                   help="An existing model for word splitting is loaded from a file (which is the output of an "\
                        "earlier run of this program) and the words in the corpus defined using the option '-data "\
                        "wordlist' are segmented according to the loaded model. That is, "\
                        "no learning of a new model takes place. The existing model is simply used for segmenting a " \
                        "list of words. The segmentation takes place using Viterbi search. No new morphs are ever " \
                        "created (except one-letter morphs, if there is no other way of segmenting a particular input" \
                        " word)")

    a.add_argument('-encoding', dest='encoding', help='Input encoding (defaults to local encoding)')

    a.add_argument('-savememory', type=int, nargs='?', help=SUPPRESS)

    options = a.parse_args()

    if options.load is not None:
        m = MorphModel(vars(options))
        m.load(options.load)

        for word in open(options.data):
            print(' + '.join(m.viterbi_segment_word(word.strip())))

    else:
        m = MorphModel(vars(options))
        m.train(options.data)
        stderr.flush()
        m.print_segmentation()


if __name__ == "__main__":
    main()
