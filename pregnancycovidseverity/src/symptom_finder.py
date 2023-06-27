#!/usr/bin/env python3
"""
    Call this from app.py.

    This module assumes that "has fever" means a temp > 38.0C, or 100.4F.
"""

import os
import re
import sys
import json
from collections import namedtuple

from . import finder_overlap as overlap

SYMPTOM_TUPLE_FIELDS = [
    'sentence',
    'has_fever',
    'has_dyspnea',
    'has_cough',
    'is_intubated',
    'is_ventilated',
    'in_icu',
    'has_ards_or_rf',   # ARDS or respiratory failure
    'on_ecmo',
    'has_septic_shock',
    'has_mod',          # multiple organ dysfunction
    'on_remdesivir',
    'on_plasma',        # convalescent plasma
    'on_plaquenil',     # hydroxychloroquine alone
    'on_azithromycin',
    'on_other_drugs',
    'on_dexamethasone',
    #'died_from_covid',  # whether Covid was a cause of death
    
    'has_chills',
    'has_rigors',
    'has_myalgia', 
    'has_runny_nose',
    'has_sore_throat',
    'has_prob_with_taste',
    'has_prob_with_smell',
    'has_fatigue',
    'has_wheezing',
    'has_chest_pain',
    'has_nausea',
    'has_vomiting',
    'has_headache',
    'has_abdominal_pain',
    'has_diarrhea',
    
    'is_asymptomatic',
]
SymptomTuple = namedtuple('SymptomTuple', SYMPTOM_TUPLE_FIELDS)

# # drug fields
# DRUG_FIELDS = {
#     'on_remdesivir', 'on_plasma', 'on_plaquenil', 'on_azithromycin',
#     'on_other_drugs', 'on_dexamethasone'
# }

##############################################################################
def merge_symptoms(obj_list):
    """
    Merge multiple SymptomTuple types into a single result
    """
    
    # ensure all objects are of type sf.SymptomTuple
    for obj in obj_list:
        assert(SymptomTuple == type(obj))
        
    # all fields are Boolean except for 'sentence', which can be ignored
    result = {}
    for k in SYMPTOM_TUPLE_FIELDS:
        result[k] = False
        
    for obj in obj_list:
        for k,v in obj._asdict().items():
            if v:
                result[k] = True
                
    # explicitly construct the result namedtuple to ensure correct key ordering
    obj = SymptomTuple(
        sentence            = '',
        has_fever           = result['has_fever'],
        has_dyspnea         = result['has_dyspnea'],
        has_cough           = result['has_cough'],
        is_intubated        = result['is_intubated'],
        is_ventilated       = result['is_ventilated'],
        in_icu              = result['in_icu'],
        has_ards_or_rf      = result['has_ards_or_rf'],
        on_ecmo             = result['on_ecmo'],
        has_septic_shock    = result['has_septic_shock'],
        has_mod             = result['has_mod'],
        on_remdesivir       = result['on_remdesivir'],
        on_plasma           = result['on_plasma'],
        on_plaquenil        = result['on_plaquenil'],
        on_azithromycin     = result['on_azithromycin'],
        on_other_drugs      = result['on_other_drugs'],
        on_dexamethasone    = result['on_dexamethasone'],
        
        has_chills          = result['has_chills'],
        has_rigors          = result['has_rigors'],
        has_myalgia         = result['has_myalgia'],
        has_runny_nose      = result['has_runny_nose'],
        has_sore_throat     = result['has_sore_throat'],
        has_prob_with_taste = result['has_prob_with_taste'],
        has_prob_with_smell = result['has_prob_with_smell'],
        has_fatigue         = result['has_fatigue'],
        has_wheezing        = result['has_wheezing'],
        has_chest_pain      = result['has_chest_pain'],
        has_nausea          = result['has_nausea'],
        has_vomiting        = result['has_vomiting'],
        has_headache        = result['has_headache'],
        has_abdominal_pain  = result['has_abdominal_pain'],
        has_diarrhea        = result['has_diarrhea'],
        
        is_asymptomatic     = result['is_asymptomatic']
    )
    
    return obj

###############################################################################
_VERSION_MAJOR = 0
_VERSION_MINOR = 8

# set to True to enable debug output
_TRACE = False

# make a negation header, i.e. 'patient denies <symptom>'
_str_neg_words = r'\b(denie(s|d)|without|absence of|unsure of|not (on|taking)|' \
        r'decline(s|d)|neg|not|no|negative)\b(?! date)\b'
_regex_neg_words = re.compile(_str_neg_words, re.IGNORECASE)
def _make_str_neg(group_name):
    return r'(?P<{0}>'.format(group_name) + _str_neg_words + r')'
    #return r'(?P<{0}>\b(denies|without|absence of|not (on|taking)|' \
    #    r'declined|neg|not|no)\b)(?! date)\b'.format(group_name)

# nongreedy word captures, includes '/' for abbrevations such as r/t (related to)
_str_word = r'\s?[-a-z/]+\s?'
_str_seven_words = r'(' + _str_word + r'){7}'
_str_six_words   = r'(' + _str_word + r'){6}'
_str_five_words  = r'(' + _str_word + r'){5}'
_str_four_words  = r'(' + _str_word + r'){4}'
_str_three_words = r'(' + _str_word + r'){3}'
_str_two_words   = r'(' + _str_word + r'){2}'
_str_one_word    = r'(' + _str_word + r'){1}'
_str_space       = r'\s?'
_str_words = r'\b(' + _str_three_words + r'|' + _str_two_words + \
    r'|' + _str_one_word + r'|' + _str_space + r')'

_str_words5 = r'\b(' + _str_five_words + r'|' + _str_four_words + \
    r'|' + _str_three_words + r'|' + _str_two_words + \
    r'|' + _str_one_word + r'|' + _str_space + r')'

_str_words6 = r'\b(' + _str_six_words + r'|' + _str_five_words + \
    r'|' + _str_four_words + r'|' + _str_three_words + r'|' + _str_two_words + \
    r'|' + _str_one_word + r'|' + _str_space + r')'

_str_words7 = r'\b(' + _str_seven_words + r'|' + _str_six_words + \
    r'|' + _str_five_words + r'|' + _str_four_words + r'|' + _str_three_words + \
    r'|' + _str_two_words + r'|' + _str_one_word + r'|' + _str_space + r')'

_str_temp_val = r'(?P<tempval>\d\d\d?(\.\d+)?)'

# capture group names
_GROUP_FEVER             = 'fever'
_GROUP_TEMP              = 'temp'
_GROUP_TEMPVAL           = 'tempval'
_GROUP_DYSPNEA           = 'dyspnea'
_GROUP_COUGH             = 'cough'
_GROUP_INTUBATED         = 'intubated'
_GROUP_NEG_FEVER         = 'neg_fever'
_GROUP_NEG_DYSP          = 'neg_dysp'
_GROUP_NEG_COUGH         = 'neg_cough'
_GROUP_NEG_INTUBATED     = 'neg_intubated'
_GROUP_VENT              = 'vent'
_GROUP_NEG_VENT          = 'neg_vent'
_GROUP_ICU               = 'icu'
_GROUP_NEG_ICU           = 'neg_icu'
_GROUP_ARDS              = 'ards' # also used for respiratory failure
_GROUP_NEG_ARDS          = 'neg_ards'
_GROUP_ECMO              = 'ecmo'
_GROUP_NEG_ECMO          = 'neg_ecmo'
_GROUP_SHOCK             = 'septic_shock'
_GROUP_NEG_SHOCK         = 'neg_septic_shock'
_GROUP_MOD               = 'mod' # multiple organ dysfunction
_GROUP_NEG_MOD           = 'neg_mod'
_GROUP_REMDESIVIR        = 'remdesivir'
_GROUP_NEG_REMDESIVIR    = 'neg_remdesivir'
_GROUP_PLASMA            = 'plasma' # convalescent plasma
_GROUP_NEG_PLASMA        = 'neg_plasma'
_GROUP_PLAQUENIL         = 'plaquenil'
_GROUP_NEG_PLAQUENIL     = 'neg_plaquenil'
_GROUP_AZITHROMYCIN      = 'azithromycin'
_GROUP_NEG_AZITHROMYCIN  = 'neg_azithromycin'
_GROUP_OTHER_DRUGS       = 'other_drugs'
_GROUP_NEG_OTHER_DRUGS   = 'neg_other_drugs'
_GROUP_DEXAMETHASONE     = 'dexamethasone'
_GROUP_NEG_DEXAMETHASONE = 'neg_dexamethasone'
#_GROUP_COVID            = 'covid'
_GROUP_CHILLS            = 'chills'
_GROUP_NEG_CHILLS        = 'neg_chills'
_GROUP_RIGORS            = 'rigors'
_GROUP_NEG_RIGORS        = 'neg_rigors'
_GROUP_MYALGIA           = 'myalgia'
_GROUP_NEG_MYALGIA       = 'neg_myalgia'
_GROUP_RUNNY_NOSE        = 'runny_nose'
_GROUP_NEG_RUNNY_NOSE    = 'neg_runny_nose'
_GROUP_SORE_THROAT       = 'sore_throat'
_GROUP_NEG_SORE_THROAT   = 'neg_sore_throat'
_GROUP_TASTE             = 'taste'
_GROUP_NEG_TASTE         = 'neg_taste'
_GROUP_SMELL             = 'smell'
_GROUP_NEG_SMELL         = 'neg_smell'
_GROUP_FATIGUE           = 'fatigue'
_GROUP_NEG_FATIGUE       = 'neg_fatigue'
_GROUP_WHEEZING          = 'wheezing'
_GROUP_NEG_WHEEZING      = 'neg_wheezing'
_GROUP_CHEST_PAIN        = 'chest_pain'
_GROUP_NEG_CHEST_PAIN    = 'neg_chest_pain'
_GROUP_NAUSEA            = 'nausea'
_GROUP_NEG_NAUSEA        = 'neg_nausea'
_GROUP_VOMITING          = 'vomiting'
_GROUP_NEG_VOMITING      = 'neg_vomiting'
_GROUP_HEADACHE          = 'headache'
_GROUP_NEG_HEADACHE      = 'neg_headache'
_GROUP_ABD_PAIN          = 'abdominal_pain'
_GROUP_NEG_ABD_PAIN      = 'neg_abdominal_pain'
_GROUP_DIARRHEA          = 'diarrhea'
_GROUP_NEG_DIARRHEA      = 'neg_diarrhea'
_GROUP_ASYMPTOMATIC      = 'asymptomatic'

_str_fever_header = r'\b((low|high) grade|for|had|with|reports|' \
    r'develop(ed|ing)|iclud(ed|ing)|seen|and|worsening|elevated|' \
    r'diagnos(is|ed))\b'

_str_fever = r'\b(?<!spotted )(?P<fever>(fever(ish)?|febrile|temp\.?(erature)?))\b'
_regex_fever = re.compile(_str_fever, re.IGNORECASE)

_str_fever0 = _str_fever_header + _str_words + _str_fever
_regex_fever0 = re.compile(_str_fever0, re.IGNORECASE)

_str_fever1 = _str_fever_header + _str_words + _str_fever + \
    _str_words + _str_temp_val
_regex_fever1 = re.compile(_str_fever1, re.IGNORECASE)

_str_fever2 = _str_fever + _str_words + _str_temp_val
_regex_fever2 = re.compile(_str_fever2, re.IGNORECASE)

_str_temp = r'\b(?P<temp>temp\.?(erature)?)( of)?'

_str_fever3 = _str_temp + _str_words + _str_temp_val
_regex_fever3 = re.compile(_str_fever3, re.IGNORECASE)

_str_fever4 = _str_temp_val + _str_words + _str_temp
_regex_fever4 = re.compile(_str_fever4, re.IGNORECASE)

_str_neg_fever = _make_str_neg(_GROUP_NEG_FEVER) + _str_words5 + _str_fever
_regex_neg_fever = re.compile(_str_neg_fever, re.IGNORECASE)

# dyspnea
_str_dyspnea = r'\b(?P<dyspnea>(dyspnea|short(ness)? of breath|' \
    r'labored breathing|sob|increased work of breathing|' \
    r'breathing (difficulty?|trouble)|(difficulty?|trouble) breathing|' \
    r'(difficulty|trouble) (catching( a)?|taking( a)?)( full)? breath|' \
    r'respiration labored|labored respiration|hung(er|ry for) air|' \
    r'gasping|breathlessness|out of breath|breath shortness|' \
    r'air hunger|resp\.?(iratory)? distress))\b'
_regex_dyspnea = re.compile(_str_dyspnea, re.IGNORECASE)

_str_neg_dyspnea = _make_str_neg(_GROUP_NEG_DYSP) + _str_words5 + _str_dyspnea
_regex_neg_dyspnea = re.compile(_str_neg_dyspnea, re.IGNORECASE)

# cough
_str_cough = r'\b(?P<cough>(cough(ed|ing)?)(?! medicine))\b'
_regex_cough = re.compile(_str_cough, re.IGNORECASE)

_str_neg_cough = _make_str_neg(_GROUP_NEG_COUGH) + _str_words5 + _str_cough
_regex_neg_cough = re.compile(_str_neg_cough, re.IGNORECASE)

# intubated
_str_intubated = r'\b(?P<intubated>(re\-?)?(intubat(ed?|ion)|intub\.?))\b'
_regex_intubated = re.compile(_str_intubated, re.IGNORECASE)

_str_neg_intubated = _make_str_neg(_GROUP_NEG_INTUBATED) + _str_words5 + _str_intubated
_regex_neg_intubated = re.compile(_str_neg_intubated, re.IGNORECASE)

# ventilation
_str_vent = r'\b(?<!husband on )(?P<vent>(vent\.?(ilator|ilation)?))\b'
_regex_vent = re.compile(_str_vent, re.IGNORECASE)

_str_vent0 = r'\b(mechanical|mech\.?)' + _str_words + _str_vent
_regex_vent0 = re.compile(_str_vent0, re.IGNORECASE)

_str_vent1 = r'\b((patient|pt|mother) )?on' + _str_words + _str_vent
_regex_vent1 = re.compile(_str_vent1, re.IGNORECASE)

_str_neg_vent = _make_str_neg(_GROUP_NEG_VENT) + _str_words + _str_vent
_regex_neg_vent = re.compile(_str_neg_vent, re.IGNORECASE)

# # icu
# # micu == maternal icu, sicu == surgical icu, 
# _str_icu = r'\b(?P<icu>(micu|sicu|icu))\b'
# _regex_icu = re.compile(_str_icu, re.IGNORECASE)

# _str_icu0 = r'\b(admitted|transferred|delivery|intubated|went|was|tx) (in|to)\b' + \
#     _str_words + _str_icu
# _regex_icu0 = re.compile(_str_icu0, re.IGNORECASE)

# _str_icu1 = _str_icu + r'\b(admission|admit)\b' + _str_words + r'\b(for|on|at)?\b'
# _regex_icu1 = re.compile(_str_icu1, re.IGNORECASE)

# _str_icu2 = _str_icu + r'\bfor\b'
# _regex_icu2 = re.compile(_str_icu2, re.IGNORECASE)

# _str_neg_icu = r'\b(?P<neg_icu>(discharged|d/c|dc|transferred|trans\.?|tx) (from|out of)' +\
#     _str_words + _str_icu + r')'
# _regex_neg_icu = re.compile(_str_neg_icu, re.IGNORECASE)

# MICU == maternal ICU, SICU == surgical ICU
_str_icu = r'\b[ms]?icu\b'

_str_admitted1 = r'\badmitted( (to|through))?' + _str_words + _str_icu  + _str_words +\
    r'\b(with|for|presented)\b' + _str_words + \
    r'\b((ards|covid[-19 ]+|pneumonia|treatment|respiratory|failure|intubated|delivery)\s?)+\b'
_regex_admitted1 = re.compile(_str_admitted1, re.IGNORECASE)

_str_admitted2 = r'\badmitted( (to|through))?' + _str_words + _str_icu + r'\s?\Z'
_regex_admitted2 = re.compile(_str_admitted2, re.IGNORECASE)

_str_admitted3 = _str_icu + r' admission for' + _str_words + \
    r'\b((covid|respiratory|failure|pneumonia|ards|infection)\s?)+'
_regex_admitted3 = re.compile(_str_admitted3, re.IGNORECASE)

_str_in_icu = r'\bin ' + _str_icu + _str_words + \
    r'\b(at (onset|time) of|on|due to|still|while|when|during) ' + \
    r'((cpap|high|flow|nasal|cannula|vent|illness|infection|covid|pneumonia|intubated)\s?)+'
_regex_in_icu = re.compile(_str_in_icu, re.IGNORECASE)

_str_intubated_in_icu = r'\bintubated' + _str_words + r'\b((sent|transferred|tx) to)' + _str_words + _str_icu
_regex_intubated_in_icu = re.compile(_str_intubated_in_icu, re.IGNORECASE)

_str_intubated_in_icu2 = r'\bintubated in' + _str_words + _str_icu + _str_words + r'\d+ (hours|days|weeks)\b'
_regex_intubated_in_icu2 = re.compile(_str_intubated_in_icu2, re.IGNORECASE)

_str_tx_to_icu = r'\b(transferred|tx) to\b' + _str_words + _str_icu
_regex_tx_to_icu = re.compile(_str_tx_to_icu, re.IGNORECASE)

_str_duration_in_icu = r'\b(number of (days|weeks|months)|duration|(length of )?time( spent)?) in ' + _str_icu
_regex_duration_in_icu = re.compile(_str_duration_in_icu, re.IGNORECASE)

_str_icu_course = r'\b(during|throughout)(?! (prior|former|previous))\b' + _str_words + \
    _str_icu + r'( (course|stay|admission))?'
_regex_icu_course = re.compile(_str_icu_course, re.IGNORECASE)


# ARDS, respiratory failure
_str_ards = r'\b(?P<{0}>(acute respiratory distress syndrome|(severe )?ards|' \
    r'acute (hypoxemic|hypoxic) respiratory failure|(acute )?respiratory failure|' \
    r'acute respiratory disease))'.format(_GROUP_ARDS)
_regex_ards = re.compile(_str_ards, re.IGNORECASE)

_str_neg_ards = _make_str_neg(_GROUP_NEG_ARDS) + _str_words + _str_ards
_regex_neg_ards = re.compile(_str_neg_ards, re.IGNORECASE)

# ECMO
_str_ecmo = r'\b(?P<{0}>(extra[- ]?corporeal membrane oxygenation|ecmo))\b'.format(_GROUP_ECMO)
_regex_ecmo = re.compile(_str_ecmo, re.IGNORECASE)

_str_neg_ecmo = _make_str_neg(_GROUP_NEG_ECMO) + _str_words + _str_ecmo
_regex_neg_ecmo = re.compile(_str_neg_ecmo, re.IGNORECASE)

# septic shock
_str_septic_shock = r'\b(?P<{0}>(refractory septic|refractory|septic) shock)\b'.format(_GROUP_SHOCK)
_regex_septic_shock = re.compile(_str_septic_shock, re.IGNORECASE)

_str_septic_shock0 = r'\b(with|has|diagnosis of)' + _str_words + _str_septic_shock
_regex_septic_shock0 = re.compile(_str_septic_shock0, re.IGNORECASE)

_str_neg_septic_shock = _make_str_neg(_GROUP_NEG_SHOCK) + _str_words + _str_septic_shock
_regex_neg_septic_shock = re.compile(_str_neg_septic_shock, re.IGNORECASE)

# multiple organ dysfunction
_str_mod = r'\b(?P<{0}>(multiple|multi[\- ]?|acute)\s?organ (dysfunction|failure|fail))'.format(_GROUP_MOD)
_regex_mod = re.compile(_str_mod, re.IGNORECASE)

_str_neg_mod = _make_str_neg(_GROUP_NEG_MOD) + _str_words + _str_mod
_regex_neg_mod = re.compile(_str_neg_mod, re.IGNORECASE)

_str_drug_header = r'\b(received|(began|started)( on| treatment with)?|units?( of)?|given)\b'

# remdesivir
_str_remdesivir = r'\b(?P<{0}>(remdesivir|veklury))\b'.format(_GROUP_REMDESIVIR)
_regex_remdesivir = re.compile(_str_remdesivir, re.IGNORECASE)

_str_remdesivir0 = r'(' + _str_drug_header + _str_words + r')?' + _str_remdesivir
_regex_remdesivir0 = re.compile(_str_remdesivir0, re.IGNORECASE)

_str_neg_remdesivir = _make_str_neg(_GROUP_NEG_REMDESIVIR) + _str_words + _str_remdesivir
_regex_neg_remdesivir = re.compile(_str_neg_remdesivir, re.IGNORECASE)

# convalescent plasma
_str_plasma = r'\b(?P<plasma>((con[a-z]+?ent|conv\.?) plasm[ea]|plasm[ea])\s?(transfusion|therapy)?)\b'
_regex_plasma = re.compile(_str_plasma, re.IGNORECASE)

_str_plasma0 = r'(' + _str_drug_header + _str_words + r')?' + _str_plasma
_regex_plasma0 = re.compile(_str_plasma0, re.IGNORECASE)

_str_neg_plasma = _make_str_neg(_GROUP_NEG_PLASMA) + _str_words + _str_plasma
_regex_neg_plasma = re.compile(_str_neg_plasma, re.IGNORECASE)

# plaquenil (hydroxychloroquine); include some misspellings seen in the data
_str_plaquenil = r'\b(?P<{0}>(hydroxychloroquine|hydroxychl|plaquenil|' \
    r'plaqurnil|palquenil))'.format(_GROUP_PLAQUENIL)
_regex_plaquenil = re.compile(_str_plaquenil, re.IGNORECASE)

_str_plaquenil0 = r'(' + _str_drug_header + _str_words + r')?' + _str_plaquenil + \
    r'(' + _str_words + r'(2|4|6|8)00\s?mg' + r')?'
_regex_plaquenil0 = re.compile(_str_plaquenil0, re.IGNORECASE)

_str_neg_plaquenil = _make_str_neg(_GROUP_NEG_PLAQUENIL) + _str_words + _str_plaquenil
_regex_neg_plaquenil = re.compile(_str_neg_plaquenil, re.IGNORECASE)

# azithromycin
_str_azithromycin = r'\b(?P<{0}>(azithromycin|a?zithro|zpack|zpak))'.format(_GROUP_AZITHROMYCIN)
_regex_azithromycin = re.compile(_str_azithromycin, re.IGNORECASE)

_str_neg_azithromycin = _make_str_neg(_GROUP_NEG_AZITHROMYCIN) + _str_words + _str_azithromycin
_regex_neg_azithromycin = re.compile(_str_neg_azithromycin, re.IGNORECASE)

# other drugs
_str_other_drugs = r'\b(?P<{0}>(humira|adalimumab|kaletra|lopinavir|ritonavir|' \
    r'regeneron|monoclonal antibod(y|ies)|monoclonals|tocilizumab|actemra|' \
    r'casirivimab|sotrovimab|bamlanivimab|etesevimab|imdevimab|sarilumab|' \
    r'baricitinib|olumiant|veklury|sarilumab|tofacitinib))'.format(_GROUP_OTHER_DRUGS)
_regex_other_drugs = re.compile(_str_other_drugs, re.IGNORECASE)
_str_neg_other_drugs = _make_str_neg(_GROUP_NEG_OTHER_DRUGS) + _str_words + _str_other_drugs
_regex_neg_other_drugs = re.compile(_str_neg_other_drugs, re.IGNORECASE)

# dexamethasone
_str_dex = r'\b(?P<{0}>(dexamethasone|decadron|baycadron|dexpak|zemapak|zodex))'.format(_GROUP_DEXAMETHASONE)
_regex_dex = re.compile(_str_dex, re.IGNORECASE)
_str_neg_dex = _make_str_neg(_GROUP_NEG_DEXAMETHASONE) + _str_words + _str_dex
_regex_neg_dex = re.compile(_str_neg_dex, re.IGNORECASE)

# # death from covid
# _str_covid = r'\b(?P<{0}>(covid([- ]?19)?|sars[- ]?cov[- ]?2|(novel )?coronavirus))\b'.format(_GROUP_COVID)
# _regex_covid = re.compile(_str_covid, re.IGNORECASE)

# chills
_str_chills = r'\b(?P<{0}>(chill(s|ed)?|(felt|feeling) cold))\b'.format(_GROUP_CHILLS)
_str_neg_chills = _make_str_neg(_GROUP_NEG_CHILLS) + _str_words6 + _str_chills
_regex_chills = re.compile(_str_chills, re.IGNORECASE)
_regex_neg_chills = re.compile(_str_neg_chills, re.IGNORECASE)

# rigors
_str_rigors = r'\b(?P<{0}>(rigor(s|ed|ing)?|shiver(s|ed|ing)?|shak(es|ing)?))\b'.format(_GROUP_RIGORS)
_str_neg_rigors = _make_str_neg(_GROUP_NEG_RIGORS) + _str_words6 + _str_rigors
_regex_rigors = re.compile(_str_rigors, re.IGNORECASE)
_regex_neg_rigors = re.compile(_str_neg_rigors, re.IGNORECASE)

# myalgia (muscle aches)
_str_myalgias = r'\b(?P<{0}>(myalgias?|myodynias?|'          \
    r'muscles? (aching|cramping|soreness|pains?|cramps?|ache(s|d)?)|' \
    r'(aching|sore|(pain|cramp)s? in( the)?) muscles?))\b'.format(_GROUP_MYALGIA)
_regex_myalgias = re.compile(_str_myalgias, re.IGNORECASE)
_str_neg_myalgias = _make_str_neg(_GROUP_NEG_MYALGIA) + _str_words6 + _str_myalgias
_regex_neg_myalgias = re.compile(_str_neg_myalgias, re.IGNORECASE)

# runny nose
_str_runny_nose = r'\b(?P<{0}>((runny|running|dripping) nose|nasal drip|rhinorrhea))\b'.format(_GROUP_RUNNY_NOSE)
_regex_runny_nose = re.compile(_str_runny_nose, re.IGNORECASE)
_str_neg_runny_nose = _make_str_neg(_GROUP_NEG_RUNNY_NOSE) + _str_words5 + _str_runny_nose
_regex_neg_runny_nose = re.compile(_str_neg_runny_nose, re.IGNORECASE)

# sore throat
_str_sore_throat = r'\b(?P<{0}>(sore throat|pharyngitis|throat (pain|soreness|hurts)))\b'.format(_GROUP_SORE_THROAT)
_regex_sore_throat = re.compile(_str_sore_throat, re.IGNORECASE)
_str_neg_sore_throat = _make_str_neg(_GROUP_NEG_SORE_THROAT) + _str_words5 + _str_sore_throat
_regex_neg_sore_throat = re.compile(_str_neg_sore_throat, re.IGNORECASE)

# problems with sense of taste
_str_taste = r'\b(taste|ageusia|aguesia|tasting)\b'
_str_smell = r'\b(smell|anosmia|smelling)\b'

_str_taste_and_smell = r'\b(taste and smell|smell and taste|taste/smell|smell/taste|' \
    r'anosmia and (ageusia|aguesia)|(ageusia|aguesia) and anosmia|sense of taste and smell|' \
    r'sense of smell and taste)\b'

_str_problems_with = r'\b(problems? with|problems?|decreased sense of|decreased|' \
    r'lost sense of|loss of|lost)\b'

_str_taste = r'(' + _str_problems_with + _str_words + r')?' + \
    r'(?P<{0}>('.format(_GROUP_TASTE) + _str_taste_and_smell + r'|' + _str_taste + r'))'
_regex_taste = re.compile(_str_taste, re.IGNORECASE)

_str_smell = r'(' + _str_problems_with + _str_words + r')?' + \
    r'(?P<{0}>('.format(_GROUP_SMELL) + _str_taste_and_smell + r'|' + _str_smell + r'))'
_regex_smell = re.compile(_str_smell, re.IGNORECASE)

_str_neg_taste = _make_str_neg(_GROUP_NEG_TASTE) + _str_words + r'(ageusia|aguesia)'
_regex_neg_taste = re.compile(_str_neg_taste, re.IGNORECASE)

_str_neg_smell = _make_str_neg(_GROUP_NEG_SMELL) + _str_words + r'anosmia'
_regex_neg_smell = re.compile(_str_neg_smell, re.IGNORECASE)

# fatigue
_str_fatigue = r'\b(fatigued?|lethargy/malaise|malaise/lethargy|letharg(ic|y)|' \
    r'exhaust(ion|ed)|wear(iness|y)|tired(ness)?|enervat(ion|ed)|' \
    r'exhaust(ed|ion)|lack of energy|no energy)\b'
_str_has_fatigue = r'\b((feels?|feeling|has|had|having|' \
    r'experienced|experiencing)' + _str_words + r')?' + \
    r'(?P<{0}>'.format(_GROUP_FATIGUE) + _str_fatigue + r')'
_regex_fatigue = re.compile(_str_has_fatigue, re.IGNORECASE)
_str_neg_fatigue = _make_str_neg(_GROUP_NEG_FATIGUE) + _str_words5 + _str_fatigue
_regex_neg_fatigue = re.compile(_str_neg_fatigue, re.IGNORECASE)

# wheezing
_str_wheezing = r'\b(?P<{0}>(wheezing|wheezed?))\b'.format(_GROUP_WHEEZING)
_regex_wheezing = re.compile(_str_wheezing, re.IGNORECASE)
_str_neg_wheezing = _make_str_neg(_GROUP_NEG_WHEEZING) + _str_words + _str_wheezing
_regex_neg_wheezing = re.compile(_str_neg_wheezing, re.IGNORECASE)

# chest pain
_str_chest_pain = r'\b(?P<{0}>(chest pains?|pains? in (the )?chest|angina))\b'.format(_GROUP_CHEST_PAIN)
_regex_chest_pain = re.compile(_str_chest_pain, re.IGNORECASE)
_str_neg_chest_pain = _make_str_neg(_GROUP_NEG_CHEST_PAIN) + _str_words + _str_chest_pain
_regex_neg_chest_pain = re.compile(_str_neg_chest_pain, re.IGNORECASE)

# nausea and vomiting
_str_nausea = r'\b(nauseous|nausea(ted)?)'
_str_vomiting = r'\b(vomiting|vomit(ed)?|(hemat|hyper)?eme(sis|tic))'
_str_nv = r'\b(nausea and vomiting|vomiting and nausea|nausea/vomiting|vomiting/nausea|n/v|nv)\b'

_str_nausea = r'(?P<{0}>('.format(_GROUP_NAUSEA) + _str_nv + r'|' + _str_nausea + r'))'
_regex_nausea = re.compile(_str_nausea, re.IGNORECASE)
_str_neg_nausea = _make_str_neg(_GROUP_NEG_NAUSEA) + _str_words + _str_nausea
_regex_neg_nausea = re.compile(_str_neg_nausea, re.IGNORECASE)

_str_vomiting = r'(?P<{0}>('.format(_GROUP_VOMITING) + _str_nv + r'|' + _str_vomiting + r'))'
_regex_vomiting = re.compile(_str_vomiting, re.IGNORECASE)
_str_neg_vomiting = _make_str_neg(_GROUP_NEG_VOMITING) + _str_words + _str_vomiting
_regex_neg_vomiting = re.compile(_str_neg_vomiting, re.IGNORECASE)

# headache (exclude migraines)
_str_headache = r'\b(?P<{0}>(headaches?|cephalalgia|h/a|ha))\b'.format(_GROUP_HEADACHE)
_regex_headache = re.compile(_str_headache, re.IGNORECASE)
_str_neg_headache = _make_str_neg(_GROUP_NEG_HEADACHE) + _str_words + _str_headache
_regex_neg_headache = re.compile(_str_neg_headache, re.IGNORECASE)

# abdominal pain
_str_abdominal = r'\b(abdominal|abd\.?|flank|(mid)?epigastric|pelvic|liver)\b'
_str_pain = r'\bpains?\b'
_str_abd_pain = r'(?P<{0}>('.format(_GROUP_ABD_PAIN) + _str_abdominal + _str_words + _str_pain + r'))'
_regex_abd_pain = re.compile(_str_abd_pain, re.IGNORECASE)
_str_neg_abd_pain = _make_str_neg(_GROUP_NEG_ABD_PAIN) + _str_words5 + _str_abd_pain
_regex_neg_abd_pain = re.compile(_str_neg_abd_pain, re.IGNORECASE)

# diarrhea
_str_diarrhea = r'\b(?P<{0}>(diarrhea|(loose|watery) (stool|bowel)s?))\b'.format(_GROUP_DIARRHEA)
_regex_diarrhea = re.compile(_str_diarrhea, re.IGNORECASE)
_str_neg_diarrhea = _make_str_neg(_GROUP_NEG_DIARRHEA) + _str_words5 + _str_diarrhea
_regex_neg_diarrhea = re.compile(_str_neg_diarrhea, re.IGNORECASE)

# asymptomatic
_str_asymptomatic = r'\b(?P<{0}>asymptomatic(?! bacteriuria))'.format(_GROUP_ASYMPTOMATIC)
_regex_asymptomatic = re.compile(_str_asymptomatic, re.IGNORECASE)

_FEVER_REGEXES = [
    _regex_fever0,
    _regex_fever1,
    _regex_fever2,
    _regex_fever3,
    _regex_fever4,
    _regex_fever,
    _regex_neg_fever,
]

_DYSPNEA_REGEXES = [
    _regex_dyspnea,
    _regex_neg_dyspnea,
]

_COUGH_REGEXES = [
    _regex_cough,
    _regex_neg_cough,    
]

_INTUBATED_REGEXES = [
    _regex_intubated,
    _regex_neg_intubated
]

_VENTILATION_REGEXES = [
    _regex_vent0,
    _regex_vent1,
    _regex_vent,
    _regex_neg_vent,
]

# _ICU_REGEXES = [
#     _regex_icu0,
#     _regex_icu1,
#     _regex_icu2,
#     _regex_icu,
#     _regex_neg_icu,
# ]

_ICU_REGEXES = [
    _regex_admitted1,
    _regex_admitted2,
    _regex_admitted3,
    _regex_in_icu,
    _regex_intubated_in_icu,
    _regex_intubated_in_icu2,
    _regex_tx_to_icu,
    _regex_duration_in_icu,
    _regex_icu_course
]

_ARDS_REGEXES = [
    _regex_ards,
    _regex_neg_ards,
]

_ECMO_REGEXES = [
    _regex_ecmo,
    _regex_neg_ecmo
]

_SEPTIC_SHOCK_REGEXES = [
    _regex_septic_shock0,
    _regex_septic_shock,
    _regex_neg_septic_shock
]

_MOD_REGEXES = [
    _regex_mod,
    _regex_neg_mod,
]

_REMDESIVIR_REGEXES = [
    _regex_remdesivir,
    _regex_remdesivir0,
    _regex_neg_remdesivir
]

_PLASMA_REGEXES = [
    _regex_plasma,
    _regex_plasma0,
    _regex_neg_plasma
]

_PLAQUENIL_REGEXES = [
    _regex_plaquenil,
    _regex_plaquenil0,
    _regex_neg_plaquenil,
]

_AZITHROMYCIN_REGEXES = [
    _regex_azithromycin,
    _regex_neg_azithromycin
]

_OTHER_DRUGS_REGEXES = [
    _regex_other_drugs,
    _regex_neg_other_drugs,
]

_DEX_REGEXES = [
    _regex_dex,
    _regex_neg_dex,
]

# _COVID_REGEXES = [
#     _regex_covid,
# ]

_CHILLS_REGEXES = [
    _regex_chills,
    _regex_neg_chills,
]

_RIGORS_REGEXES = [
    _regex_rigors,
    _regex_neg_rigors,
]

_MYALGIAS_REGEXES = [
    _regex_myalgias,
    _regex_neg_myalgias,
]

_RUNNY_NOSE_REGEXES = [
    _regex_runny_nose,
    _regex_neg_runny_nose,
]

_SORE_THROAT_REGEXES = [
    _regex_sore_throat,
    _regex_neg_sore_throat,
]

_TASTE_REGEXES = [
    _regex_taste,
    _regex_neg_taste,
]

_SMELL_REGEXES = [
    _regex_smell,
    _regex_neg_smell,
]

_FATIGUE_REGEXES = [
    _regex_fatigue,
    _regex_neg_fatigue,
]

_WHEEZING_REGEXES = [
    _regex_wheezing,
    _regex_neg_wheezing,
]

_CHEST_PAIN_REGEXES = [
    _regex_chest_pain,
    _regex_neg_chest_pain,
]

_NAUSEA_REGEXES = [
    _regex_nausea,
    _regex_neg_nausea,
]

_VOMITING_REGEXES = [
    _regex_vomiting,
    _regex_neg_vomiting,
]

_HEADACHE_REGEXES = [
    _regex_headache,
    _regex_neg_headache
]

_ABD_PAIN_REGEXES = [
    _regex_abd_pain,
    _regex_neg_abd_pain,
]

_DIARRHEA_REGEXES = [
    _regex_diarrhea,
    _regex_neg_diarrhea
]

_ASYMPTOMATIC_REGEXES = [
    _regex_asymptomatic,
]

_FEVER_C = 38.0
_FEVER_F = 100.4


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

    # replace some chars with with a single space
    sentence = re.sub(r'[,()]', ' ', sentence)
    
    # replace '&' symbols with text
    sentence = re.sub(r'&', ' and ', sentence)

    # correct some spelling errors
    sentence = re.sub(r'\bffor\b', 'for', sentence)
    sentence = re.sub(r'\bplasme\b', 'plasma', sentence)
    sentence = re.sub(r'\bvomitting\b', 'vomiting', sentence)
    
    # collapse repeated whitespace
    sentence = re.sub(r'\s+', ' ', sentence)

    if _TRACE:
        print('Cleaned sentence: "{0}"'.format(sentence))
    
    return sentence


###############################################################################
def _regex_match(sentence, regex_list):
    """
    """

    if _TRACE:
        print('Calling _regex_match: ')
        print('\tsentence: {0}'.format(sentence))

    candidates = []
    for i, regex in enumerate(regex_list):
        match = regex.search(sentence)
        if match:
            match_text = match.group().strip()
            if 0 == len(match_text) or match_text.isspace():
                continue
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
def _has_symptom(cleaned_sentence, regexes, group, neg_group):

    candidates = _regex_match(cleaned_sentence, regexes)

    has_symptom = False

    for i,c in enumerate(candidates):
        keys = set()
        for k,v in c.other.groupdict().items():
            if v is not None:
                keys.add(k)

        if _TRACE:
            print('CANDIDATE {0}'.format(i))
            print(c)
            print('\t  text : {0}'.format(c.match_text))
            print('\tgroups : {0}'.format(keys))

        symptom_present = group in keys

        neg_symptom_present = False
        if neg_group is not None:
            neg_symptom_present = neg_group in keys

            if not neg_symptom_present:
                # check to see if one of the <words> matches includes the
                # negation words, in which case it is actually a negation
                match = _regex_neg_words.search(c.match_text)
                if match:
                    print('\t*** negation override ***')
                    neg_symptom_present = True

        if symptom_present and not neg_symptom_present:
            has_symptom = True

    return has_symptom
    

###############################################################################
def _strip_dates(sentence):
    """
    """

    # date formats: 4/10, 04/18, 4/19/20, 10/2/20, 7/20/20, 12/21/2020
    # from 5/16-5/23, 9/12-10/8, 10/15/20, 9/2/20

    _str_date = r'(\bon )?(?<!\d)[0-1]?[0-9]/[0-3]?[0-9](/\d{2,4})?'
    _str_date_range = r'(\bfrom )?' + _str_date + r'\s?\-\s?' + _str_date

    _str_all_dates = r'(' + _str_date_range + r')|(' + _str_date + r')'
    _regex_all_dates = re.compile(_str_all_dates, re.IGNORECASE)

    iterator = _regex_all_dates.finditer(sentence)
    for match in iterator:
        p1 = sentence[:match.start()]
        p2 = ' '*(match.end() - match.start())
        p3 = sentence[match.end():]
        sentence = p1 + p2 + p3

    # collapse repeated whitespace
    sentence = re.sub(r'\s+', ' ', sentence)
    return sentence
    

###############################################################################
def _is_in_icu(cleaned_sentence):
    """
    Special handling for ICU admission. Only accept ICU admission if it is
    for Covid or a related symptom (intubation, ventilation, etc.).
    """
    
    stripped = _strip_dates(cleaned_sentence)
    stripped = re.sub(r'\b(and|prior to)\b', ' ', stripped)
    stripped = re.sub(r'\s+', ' ', stripped)

    found_match1 = False
    for regex in _ICU_REGEXES:
        match = regex.search(stripped)
        if match:
            found_match1 = True

    found_match2 = False
    if not found_match1:
        # strip out time periods and try to match again
        stripped2 = re.sub(r'\b(at|for) \d+ (weeks|days)\b', ' ', stripped)
        stripped2 = re.sub(r'\s+', ' ', stripped2)
        for regex in _ICU_REGEXES:
            match = regex.search(stripped2)
            if match:
                found_match2 = True
                    
    return found_match1 or found_match2
    
    
###############################################################################
def _has_fever(cleaned_sentence):
    """
    Special handling for fever.
    """

    fever_candidates = _regex_match(cleaned_sentence, _FEVER_REGEXES)

    has_fever = False
    
    for i,c in enumerate(fever_candidates):
        keys = set()
        for k,v in c.other.groupdict().items():
            if v is not None:
                keys.add(k)

        if _TRACE:
            print('FEVER CANDIDATE {0}'.format(i))
            print(c)
            print('\t  text : {0}'.format(c.match_text))
            print('\tgroups : {0}'.format(keys))

        fever_present = _GROUP_FEVER in keys
        temp_present  = _GROUP_TEMP in keys
        val_present   = _GROUP_TEMPVAL in keys
        neg_fever     = _GROUP_NEG_FEVER in keys        

        if not neg_fever:
            # check to see if one of the <words> matches includes the
            # negation words, in which case it is actually a negation
            match = _regex_neg_words.search(c.match_text)
            if match:
                # print('\t*** found neg_fever match ***')
                neg_fever = True
        
        # check temp val
        if (fever_present or temp_present) and val_present and not neg_fever:
            val = float(c.other.groupdict()[_GROUP_TEMPVAL])
            #print('\t\ttemperature value: {0}'.format(val))
            if val < 45.0:
                # assume celsius
                has_fever = val > _FEVER_C
            else:
                has_fever = val > _FEVER_F
        elif fever_present and not neg_fever:
            has_fever = True
        
    return has_fever


###############################################################################
def run(sentence, ignore_common=False):
    """
    """

    results = []

    cleaned_sentence = _cleanup(sentence)
    
    has_fever           = _has_fever(cleaned_sentence)
    has_dyspnea         = _has_symptom(cleaned_sentence, _DYSPNEA_REGEXES, _GROUP_DYSPNEA, _GROUP_NEG_DYSP)
    has_cough           = _has_symptom(cleaned_sentence, _COUGH_REGEXES, _GROUP_COUGH, _GROUP_NEG_COUGH)
    is_intubated        = _has_symptom(cleaned_sentence, _INTUBATED_REGEXES,
                                       _GROUP_INTUBATED, _GROUP_NEG_INTUBATED)
    is_ventilated       = _has_symptom(cleaned_sentence, _VENTILATION_REGEXES, _GROUP_VENT, _GROUP_NEG_VENT)
    #in_icu              = _has_symptom(cleaned_sentence, _ICU_REGEXES, _GROUP_ICU, _GROUP_NEG_ICU)
    in_icu              = _is_in_icu(cleaned_sentence)    
    has_ards_or_rf      = _has_symptom(cleaned_sentence, _ARDS_REGEXES, _GROUP_ARDS, _GROUP_NEG_ARDS)
    on_ecmo             = _has_symptom(cleaned_sentence, _ECMO_REGEXES, _GROUP_ECMO, _GROUP_NEG_ECMO)
    has_septic_shock    = _has_symptom(cleaned_sentence, _SEPTIC_SHOCK_REGEXES, _GROUP_SHOCK, _GROUP_NEG_SHOCK)
    has_mod             = _has_symptom(cleaned_sentence, _MOD_REGEXES, _GROUP_MOD, _GROUP_NEG_MOD)
    on_remdesivir       = _has_symptom(cleaned_sentence, _REMDESIVIR_REGEXES,
                                       _GROUP_REMDESIVIR, _GROUP_NEG_REMDESIVIR)
    on_plasma           = _has_symptom(cleaned_sentence, _PLASMA_REGEXES, _GROUP_PLASMA, _GROUP_NEG_PLASMA)
    on_plaquenil        = _has_symptom(cleaned_sentence, _PLAQUENIL_REGEXES,
                                       _GROUP_PLAQUENIL, _GROUP_NEG_PLAQUENIL)
    on_azithromycin     = _has_symptom(cleaned_sentence, _AZITHROMYCIN_REGEXES,
                                       _GROUP_AZITHROMYCIN, _GROUP_NEG_AZITHROMYCIN)
    on_other_drugs      = _has_symptom(cleaned_sentence, _OTHER_DRUGS_REGEXES,
                                       _GROUP_OTHER_DRUGS, _GROUP_NEG_OTHER_DRUGS)
    on_dexamethasone    = _has_symptom(cleaned_sentence, _DEX_REGEXES,
                                       _GROUP_DEXAMETHASONE, _GROUP_NEG_DEXAMETHASONE)
    #died_from_covid  = _has_symptom(cleaned_sentence, _COVID_REGEXES, _GROUP_COVID, None)
    has_chills          = _has_symptom(cleaned_sentence, _CHILLS_REGEXES, _GROUP_CHILLS, _GROUP_NEG_CHILLS)
    has_rigors          = _has_symptom(cleaned_sentence, _RIGORS_REGEXES, _GROUP_RIGORS, _GROUP_NEG_RIGORS)
    has_myalgia         = _has_symptom(cleaned_sentence, _MYALGIAS_REGEXES, _GROUP_MYALGIA, _GROUP_NEG_MYALGIA)
    has_runny_nose      = _has_symptom(cleaned_sentence, _RUNNY_NOSE_REGEXES,
                                       _GROUP_RUNNY_NOSE, _GROUP_NEG_RUNNY_NOSE)
    has_sore_throat     = _has_symptom(cleaned_sentence, _SORE_THROAT_REGEXES,
                                       _GROUP_SORE_THROAT,_GROUP_NEG_SORE_THROAT)
    has_prob_with_taste = _has_symptom(cleaned_sentence, _TASTE_REGEXES,
                                       _GROUP_TASTE, _GROUP_NEG_TASTE)
    has_prob_with_smell = _has_symptom(cleaned_sentence, _SMELL_REGEXES,
                                       _GROUP_SMELL, _GROUP_NEG_SMELL)
    has_fatigue         = _has_symptom(cleaned_sentence, _FATIGUE_REGEXES,
                                       _GROUP_FATIGUE, _GROUP_NEG_FATIGUE)
    has_wheezing        = _has_symptom(cleaned_sentence, _WHEEZING_REGEXES,
                                      _GROUP_WHEEZING, _GROUP_NEG_WHEEZING)
    has_chest_pain      = _has_symptom(cleaned_sentence, _CHEST_PAIN_REGEXES,
                                       _GROUP_CHEST_PAIN, _GROUP_NEG_CHEST_PAIN)
    has_nausea          = _has_symptom(cleaned_sentence, _NAUSEA_REGEXES,
                                       _GROUP_NAUSEA, _GROUP_NEG_NAUSEA)
    has_vomiting        = _has_symptom(cleaned_sentence, _VOMITING_REGEXES,
                                       _GROUP_VOMITING, _GROUP_NEG_VOMITING)
    has_headache        = _has_symptom(cleaned_sentence, _HEADACHE_REGEXES,
                                       _GROUP_HEADACHE, _GROUP_NEG_HEADACHE)
    has_abdominal_pain  = _has_symptom(cleaned_sentence, _ABD_PAIN_REGEXES,
                                       _GROUP_ABD_PAIN, _GROUP_NEG_ABD_PAIN)
    has_diarrhea        = _has_symptom(cleaned_sentence, _DIARRHEA_REGEXES,
                                       _GROUP_DIARRHEA, _GROUP_NEG_DIARRHEA)
    is_asymptomatic     = _has_symptom(cleaned_sentence, _ASYMPTOMATIC_REGEXES,
                                       _GROUP_ASYMPTOMATIC, None)
    
    # automatically have dyspnea if have ards
    if has_ards_or_rf:
        has_dyspnea = True
        
    # if ignore_common flag is set, ignore these symptoms:
    #     vomiting, nausea, abdominal pain
    if ignore_common:
        has_vomiting = False
        has_nausea   = False
        has_abdominal_pain = False
        
    obj = SymptomTuple(
        sentence = cleaned_sentence,
        has_fever = has_fever,
        has_dyspnea = has_dyspnea,
        has_cough = has_cough,
        is_intubated = is_intubated,
        is_ventilated = is_ventilated,
        in_icu = in_icu,
        has_ards_or_rf = has_ards_or_rf,
        on_ecmo = on_ecmo,
        has_septic_shock = has_septic_shock,
        has_mod = has_mod,
        on_remdesivir = on_remdesivir,
        on_plasma = on_plasma,
        on_plaquenil = on_plaquenil,
        on_azithromycin = on_azithromycin,
        on_other_drugs = on_other_drugs,
        on_dexamethasone = on_dexamethasone,
        #died_from_covid = died_from_covid
        has_chills = has_chills,
        has_rigors = has_rigors,
        has_myalgia = has_myalgia,
        has_runny_nose = has_runny_nose,
        has_sore_throat = has_sore_throat,
        has_prob_with_taste = has_prob_with_taste,
        has_prob_with_smell = has_prob_with_smell,
        has_fatigue = has_fatigue,
        has_wheezing = has_wheezing,
        has_chest_pain = has_chest_pain,
        has_nausea = has_nausea,
        has_vomiting = has_vomiting,
        has_headache = has_headache,
        has_abdominal_pain = has_abdominal_pain,
        has_diarrhea = has_diarrhea,
        
        is_asymptomatic = is_asymptomatic
    )

    results.append(obj)

    return json.dumps([obj._asdict() for obj in results], indent=4)
