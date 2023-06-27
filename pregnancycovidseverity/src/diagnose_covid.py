#!/usr/bin/env python3
"""
Diagnoses the severity of a Covid-19 infection according to the surveillance case definition.
"""

import os
import re
import sys
import json
import datetime
from collections import namedtuple

from . import o2sat_finder as o2f
from . import symptom_finder as sf
from . import covid_diagnosis_finder as cf

# all symptoms required to diagnose Covid severity
PATIENT_DATA_FIELDS = [
    
    # from covid_finder
    'has_pneumonia',
    
    # from symptom finder
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
    
    # whether the patient died from covid
    'died_from_covid', 

    # from o2sat finder
    'o2_flow_rate_list',  # L/min
    'o2_device_list',
    'needs_o2_list',
    
    # radio-button boolean indicating whether symptoms were present
    'has_symptoms',
    'has_other_symptoms',
    
    # mainly for debugging, all text fields for this patient
    'text_list',
    
    # dates of covid diagnosis and icu admission, not necessarily in this order
    'datetime1',
    'datetime2'
]

PatientData = namedtuple('PatientData', PATIENT_DATA_FIELDS)

# diagnoses
DIAG_CRITICAL = 4   # critical Covid-19
DIAG_SEVERE   = 3   # severe Covid-19
DIAG_MILD     = 2   # mild Covid-19
DIAG_ASYMP    = 1   # asymptomatic Covid-19
DIAG_UNKNOWN  = 0   # not enough info

# map of diagnosis code to diagnosis text
DIAGNOSIS_CODE_TO_TEXT = {
    DIAG_CRITICAL: 'critical',
    DIAG_SEVERE:   'severe',
    DIAG_MILD:     'mild',
    DIAG_ASYMP:    'asymptomatic',
    DIAG_UNKNOWN : 'unknown',
}

# these fields are not treated as being symptoms in the diagnosis algorithm
NON_SYMPTOM_FIELDS = {
    'sentence', 'text_list', 'has_symptoms', 'has_other_symptoms',
    'on_remdesivir', 'on_plasma', 'on_plaquenil', 'on_azithromycin',
    'on_other_drugs','on_dexamethasone',
    'is_asymptomatic', 'died_from_covid',
    'datetime1', 'datetime2'
}


###############################################################################
_VERSION_MAJOR = 0
_VERSION_MINOR = 8

# regexes to recognize high-flow devices

# nasal cannula
_str_nc = r'(O2\s)?'                                                  +\
    r'(?<!HEENT:)(?<!HEENT :)(?<!HEENT: )(?<!HEENT : )'               +\
    r'(n\.?[cp]\.?|n/c|(nas[ae]l[-\s]?)?(cannula|prongs?))(?![a-z])'
_str_device_nc = r'(?P<nc>' + _str_nc + r')'
_str_device_hfnc = r'(?P<hfnc>(O2\s)?(h\.?f\.?|h/f|high[- ]?flow)\s?' +\
    _str_nc + r')'

_str_high_flow_device = _str_device_hfnc
_regex_high_flow_device = re.compile(_str_high_flow_device, re.IGNORECASE)

###############################################################################
def get_version():
    path, module_name = os.path.split(__file__)
    return '{0} {1}.{2}'.format(module_name, _VERSION_MAJOR, _VERSION_MINOR)


###############################################################################
def diagnose_covid_severity(patient_data_obj):
    """
    Using the symptoms present in 'patient_data_obj', diagnose the severity
    of the Covid-19 infection. The algorithm is derived from the surveillance
    case definition.
    
    All patients are *assumed* to have a positive Covid diagnosis.
    """
    
    # shorthand
    obj = patient_data_obj

    # Check dates of icu admission and covid diagnosis. If dates differ by
    # 14 days or less, set dates_in_range to True. Could be a critical case.
    dates_in_range = False
    if obj.datetime1 is not None and obj.datetime2 is not None:
        if obj.datetime1 >= obj.datetime2:
            delta = obj.datetime1 - obj.datetime2
        else:
            delta = obj.datetime2 - obj.datetime1
        if delta.days <= 14:
            dates_in_range = True
    
    has_critical_covid = False
    has_severe_covid   = False
    has_mild_covid     = False
    is_asymptomatic    = False
    is_unknown         = False
    
    # critical if patient died from Covid
    if obj.died_from_covid:
        has_critical_covid = True
    
    # critical if intubated or on ventilation
    elif obj.is_intubated or obj.is_ventilated:
        has_critical_covid = True

    # critical if ecmo or icu admission
    elif obj.on_ecmo or obj.in_icu:
        has_critical_covid = True

    # critical covid if ARDS, respiratory failure, or septic shock
    elif obj.has_ards_or_rf or obj.has_septic_shock:
        has_critical_covid = True

    # critical if multi-organ dysfunction
    elif obj.has_mod:
        has_critical_covid = True
        
    # patient does not have critical covid, so now check for severe covid

    if not has_critical_covid:
        # severe covid if dyspnea AND (fever or cough)
        if obj.has_dyspnea and (obj.has_fever or obj.has_cough):
            has_severe_covid = True

        # severe covid if pneumonia
        elif obj.has_pneumonia:
            has_severe_covid = True

        # severe covid if being treated with various drugs
        elif obj.on_remdesivir or obj.on_plasma or obj.on_plaquenil or obj.on_other_drugs:
            # no need to check the (plaquenil AND azithromycin) combo, since taking
            # plaquenil will satisfy the on_plaquenil condition alone
            has_severe_covid = True

        # severe covid if receiving O2 by nasal cannula or high-flow O2 device
        n = len(obj.o2_flow_rate_list)
        assert len(obj.o2_device_list) == n
        assert len(obj.needs_o2_list)  == n
        for k in range(n):
            device = obj.o2_device_list[k]
            if device is not None and len(device) > 0:
                match = _regex_high_flow_device.search(device)
                if match:
                    # this is a high-flow device
                    has_severe_covid = True
                    break

        # check flow rates; anything > 15 l/min is 'high flow' per CDC
        for flow_rate in obj.o2_flow_rate_list:
            if flow_rate is not None and flow_rate > 15:
                has_severe_covid = True
                break

    if not has_critical_covid and not has_severe_covid:
        # Check for absence of symptoms. A patient has
        # no symptoms if all symptom fields in "obj" are False.
        # Assume all are false, then examine each key-value pair to check.
        all_false = True

        for k,v in obj._asdict().items():
            if k in NON_SYMPTOM_FIELDS:
                # ignore these fields, these aren't symptoms
                continue
            else:
                assert v is not None
                if list == type(v):
                    if len(v) > 0:
                        # found an Oxygen device, or a flow rate,
                        # or a statement about the patient needing
                        # supplemental Oxygen; hence the patient has
                        # difficulty breathing, a covid-relevant symptom
                        all_false = False
                        break
                elif v:
                    # the patient actually has symptom k
                    all_false = False
                    break

        if not all_false:
            # at least one Covid-relevant or other symptom present
            has_mild_covid = True
        else:
            # no symptoms were found
            if obj.is_asymptomatic:
                # the mv_sx Boolean was explicitly zero
                is_asymptomatic = True
            else:
                is_unknown = True
                
    if has_critical_covid:
        return DIAG_CRITICAL
    elif (has_severe_covid or has_mild_covid) and dates_in_range:
        return DIAG_CRITICAL
    elif has_severe_covid:
        return DIAG_SEVERE
    elif has_mild_covid:
        return DIAG_MILD
    elif is_asymptomatic:
        return DIAG_ASYMP
    else:
        return DIAG_UNKNOWN
