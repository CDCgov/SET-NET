#!/usr/bin/env python3
"""

"""

import os
import re
import sys
import json
from collections import namedtuple

from . import finder_overlap as overlap

COVID_DIAGNOSIS_FIELDS = [
    'sentence',
    'has_covid',
    'has_pneumonia',
]
CovidDiagnosisTuple = namedtuple('CovidDiagnosisTuple', COVID_DIAGNOSIS_FIELDS)


###############################################################################
_VERSION_MAJOR = 0
_VERSION_MINOR = 2

# set to True to enable debug output
_TRACE = False


# names used for regex capture groups
_GROUP_HIST            = {'hist'}
_GROUP_COVID           = {'covid', 'covid1'}
_GROUP_POS             = {'pos'}
_GROUP_NEG             = {'neg'}
_GROUP_CASE            = {'case'}
_GROUP_TEST            = {'test'}
_GROUP_WORDS           = {'words', 'words1'}
_GROUP_PNEUMONIA       = {'pneu'}
_GROUP_COVID_PNEUMONIA = {'cov_pneu1', 'cov_pneu2'}

_str_history = r'\b(?P<hist>(hx|h/o|hist\.?|history))'

_str_covid = r'\b(?P<{0}>((due to|with|for|from|developed|(because|result) of) )?' \
    r'(covid([- ]?19)?|sars-cov-2|(novel )?coronavirus)' \
    r'( (affecting|status|dx|diagnos(is|ed)|disease|' \
    r'(vir(us|al) )?infection))?(?! exposure))'
_str_case = r'\b(?P<case>(diagnos(is|ed)|dx|infect(ed|ion)|case|affect(ed|ing)))'

# no word boundary
_str_positive = r'(?P<pos>(\+|\(\+\)|\bpos(itive)?))'
_str_negative = r'(?P<neg>(-|\(-\)|\bneg(ative)?|\bdenies|\bno note of ' + _str_positive + r'))'

# test/tested
_str_test = r'\b(?P<test>(test|screen|pcr)(ed)?)'

# nongreedy word captures, includes '/' for abbrevations such as r/t (related to)
_str_word = r'\s?[-a-z/]+\s?'
#_str_word = r'[-a-z ]+?'
#_str_words = r'(' + _str_word + r'){0,5}?'

#_str_five_words  = r'(' + _str_word + r'){5}'
#_str_four_words  = r'(' + _str_word + r'){4}'
_str_three_words = r'(' + _str_word + r'){3}'
_str_two_words   = r'(' + _str_word + r'){2}'
_str_one_word    = r'(' + _str_word + r'){1}'
_str_space       = r'\s?'
#_str_words = r'(' + _str_five_words + r'|' + _str_four_words
_str_words = r'\b(' + _str_three_words + r'|' + _str_two_words + \
    r'|' + _str_one_word + r'|' + _str_space + r')'


###############################################################################
def _make_covid_str(group_name = 'covid'):
    return _str_covid.format(group_name)

#def _make_words_str(group_name = 'words'):
#    return _str_words.format(group_name)

def _key_present(keys, group):
    for s in group:
        if s in keys:
            return True

    return False


# history/test covid positive
_str1 = r'(' + _str_history + r'|' + _str_test + r')' + _str_words + \
    _make_covid_str() + _str_words + _str_positive
_regex1 = re.compile(_str1, re.IGNORECASE)

# history/test positive covid
_str2 = r'(' + _str_history + r'|' + _str_test + r')' + _str_words + \
    _str_positive + _str_words + _make_covid_str()
_regex2 = re.compile(_str2, re.IGNORECASE)

# history of covid
_str3 = _str_history + _str_words + _make_covid_str()
_regex3 = re.compile(_str3, re.IGNORECASE)

# covid/test positive
_str4 = r'(' + _make_covid_str() + r'|' + _str_test + r')' + \
    _str_words + _str_positive
_regex4 = re.compile(_str4, re.IGNORECASE)

# positive covid/test
_str5 = _str_positive + _str_words + \
    r'(' + _make_covid_str() + r'|' + _str_test + r')'
_regex5 = re.compile(_str5, re.IGNORECASE)

# covid symptoms
_str6 = r'(?P<symptoms>(' + _make_covid_str('covid') + r'\ssymptoms' + r'|' +\
    r'\bsymptoms of ' + _make_covid_str('covid1') + r'))'
_regex_covid_symptoms = re.compile(_str6, re.IGNORECASE)

# test
_regex_test = re.compile(_str_test)

# positive and negative
_regex_positive = re.compile(_str_positive)
_regex_negative = re.compile(_str_negative)

# covid
_regex_covid = re.compile(_make_covid_str())

# pneumonia
_str_p1 = r'\b(?P<cov_pneu1>pneumonia)' + _str_words + _make_covid_str('covid')
_str_p2 = _make_covid_str('covid1') + _str_words + r'\b(?P<cov_pneu2>pneumonia)'
_str_pneumonia = r'(?<!suspected )(?<!possible )(' + _str_p1 + r'|' + _str_p2 + r')'
_regex_covid_pneumonia = re.compile(_str_pneumonia, re.IGNORECASE)

_regex_pneumonia = re.compile(r'\b(?P<pneu>pneumonia)')

_REGEXES = [
    _regex1,
    _regex2,
    _regex3,
    _regex4,
    _regex5,
    _regex_test,
    _regex_covid,    
    _regex_positive,
    _regex_negative,
    _regex_covid_symptoms,
    _regex_covid_pneumonia,
    _regex_pneumonia,
]


###############################################################################
def enable_debug():

    global _TRACE
    _TRACE = True
    

###############################################################################
def get_version():
    path, module_name = os.path.split(__file__)
    return '{0} {1}.{2}'.format(module_name, _VERSION_MAJOR, _VERSION_MINOR)


###############################################################################
def _cleanup(sentence):
    """
    """

    # remove 'est' as in 'at est 3 wks gestation'
    sentence = re.sub(r'\best\.?\b', ' ', sentence)

    # replace commas with with a single space
    sentence = re.sub(r',', ' ', sentence)

    # collapse repeated whitespace
    sentence = re.sub(r'\s+', ' ', sentence)

    if _TRACE:
        print('Cleaned sentence: "{0}"'.format(sentence))
    
    return sentence


###############################################################################
def _regex_match(sentence, regex_list):
    """
    """

    candidates = []
    for i, regex in enumerate(regex_list):
        match = regex.search(sentence)
        if match:
            match_text = match.group().strip()
            #print('*** MATCH: "{0}"'.format(match.group()))
            start = match.start()
            end = start + len(match_text)
            candidates.append(overlap.Candidate(start, end, match_text, regex,
                                                other=match))
            

            if _TRACE:
                print('[{0:2}]: [{1:3}, {2:3})\tMATCH TEXT: ->{3}<-'.
                      format(i, start, end, match_text))
                print('\tmatch.groupdict entries: ')
                for k,v in match.groupdict().items():
                    print('\t\t{0} => {1}'.format(k,v))
    

    if 0 == len(candidates):
        return []

    # sort candidates in descending order of length, for overlap resolution
    candidates = sorted(candidates, key=lambda x: x.end-x.start, reverse=True)

    if _TRACE:
        print('\tCandidate matches: ')
        index = 0
        for c in candidates:
            print('\t[{0:2}]\t[{1},{2}): {3}'.
                  format(index, c.start, c.end, c.match_text, c.regex))
            index += 1
        print()

    candidates = sorted(candidates, key=lambda x: x.end-x.start, reverse=True)
    pruned_candidates = overlap.remove_overlap(candidates,
                                               _TRACE,
                                               keep_longest=True)
    pruned_candidates = sorted(pruned_candidates, key=lambda x: x.start)
        
    return pruned_candidates


###############################################################################
def run(sentence):
    """
    """

    results = []
    
    cleaned_sentence = _cleanup(sentence)
    candidates = _regex_match(cleaned_sentence, _REGEXES)

    keys = set()    
    for c in candidates:
        # get matching groups and add matching group names to 'keys'
        for k,v in c.other.groupdict().items():
            if v is not None:
                keys.add(k)

        # check matching text against covid regex to find if _str_words
        # captured the word 'covid' or something that the covid regex matches
        match = _regex_covid.search(c.match_text)
        if match:
            keys.add('covid')

        if _TRACE:
            print('\t  text : {0}'.format(c.match_text))
            print('\tgroups : {0}'.format(keys))
        

    # need to check for negation... TBD

    has_hist      = _key_present(keys, _GROUP_HIST)
    has_covid     = _key_present(keys, _GROUP_COVID)
    has_pos       = _key_present(keys, _GROUP_POS)
    has_neg       = _key_present(keys, _GROUP_NEG)
    has_test      = _key_present(keys, _GROUP_TEST)
    has_words     = _key_present(keys, _GROUP_WORDS)
    has_covid_pneumonia = _key_present(keys, _GROUP_COVID_PNEUMONIA)
    has_pneumonia = has_covid_pneumonia or _key_present(keys, _GROUP_PNEUMONIA)

    is_covid_positive = False
    if has_hist and has_covid and has_pos and not has_neg:
        is_covid_positive = True
    elif has_test and has_covid and has_pos and not has_neg:
        is_covid_positive = True
    elif has_hist and has_covid and not has_neg:
        is_covid_positive = True
    elif has_covid and has_pos and not has_neg:
        is_covid_positive = True
    elif has_covid and not has_neg:
        is_covid_positive = True

    if 0 == len(candidates):
        cleaned_sentence = ''        

    # result object
    obj = CovidDiagnosisTuple(
        sentence = cleaned_sentence,
        has_covid = is_covid_positive,
        has_pneumonia = has_pneumonia,
    )
    
    results.append(obj)
    
    # sort results?

    return json.dumps([obj._asdict() for obj in results], indent=4)
