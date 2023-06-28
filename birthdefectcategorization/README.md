# Categorization of Birth Defects with Natural Language Processing

**General disclaimer** This repository was created for use by CDC programs to collaborate on public health related projects in support of the [CDC mission](https://www.cdc.gov/about/organization/mission.htm).  GitHub is not hosted by the CDC, but is a third party website used by CDC and its partners to share information and collaborate on software. CDC use of GitHub does not imply an endorsement of any one particular service, product, or enterprise. 

## Overview 

CDC’s [Surveillance for Emerging Threats to Mothers and Babies Network (SET-NET)](https://www.cdc.gov/ncbddd/set-net/index.html) collects data abstracted from medical records and birth defects registries on pregnant people and their infants to understand outcomes associated with prenatal exposures. We developed an automated process to categorize birth defects for COVID-19, hepatitis C, and syphilis surveillance. By employing keyword searches, natural language processing, and machine learning, we aimed to decrease the time between data reporting and utilization. 

### ICD-10 Look-up Table  
SET-NET captures ICD-10-CM codes and free text describing birth defects at birth hospitalization, otherwise known as Q codes. In order to synthesize and categorize SET-NET birth defect data, Q codes are mapped to one of 14 birth defect categories using the clinician-developed ICD-10-CM code look-up table. This look-up table was developed using guidelines from National Birth Defects Prevention Network (NBDPN), Metropolitan Atlanta Congenital Defects Program (MACDP), and clinical subject matter expertise (SME) on birth defects which may be associated with the pathogens collected in SET-NET. 

Since this look-up table was developed especially for this project, the categories included are intended to address project objectives and may not be applicable to every research question. 

The categories in the look-up table include the standard ICD-10-CM blocks (Congenital malformations of the nervous system, Congenital malformations of eye, ear, face and neck, Congenital malformations of the circulatory system, Congenital malformations of the respiratory system, Cleft lip and cleft palate, Other congenital malformations of the digestive system, Congenital malformations of genital organs, Congenital malformations of the urinary system, Congenital malformations and deformations of the musculoskeletal system, Other congenital malformations, Chromosomal abnormalities, not elsewhere classified) in addition to three created categories (Only for infant follow-up, Not a birth defect of interest/unable to classify, Not a birth defect).  

## Code Roadmap 

### Keyword Searches 
For data that are unable to be directly mapped to a birth defect category, we first clean the free text fields in Python and used keyword searches for common terms such as “cleft lip and palate” and “atrioventricular septal defect” to assign appropriate Q codes. 

### Fuzzy Matching 
Next, we employ the fuzzywuzzy package to determine how similar the text was to the ICD-10-CM code description (i.e., fuzzy matching). This outputs a match score, with 100% indicating a perfect match. SET-NET's clinical subject matter expert reviewed these matches and set a match score cut-off of 90% or above indicating a true match for our purposes.   

### Natural Language Processing and Machine Learning 
To categorize the remaining uncategorized text below the 90% cut-off, we employed natural language processing (NLP) and machine learning (ML). This predictive modeling approach can categorize the vast majority of the remaining uncategorized birth defects. 

## Installation Instructions 

The SET-NET NLP code has been implemented in the python language and therefore requires a python runtime environment. We recommend the use of Anaconda environments (command name conda) for python development. Python has a standard package manager called pip, but conda is able to resolve dependencies and package version conflicts much better than pip. Conda also provides a conda-compatible replacement for pip. 

There are two Anaconda distributions: conda, a full-featured numerical computing, machine learning, and statistical software stack; and miniconda, a “lite” version of the full Anaconda installation. Only one of these distributions should be installed at a time, and they both use the conda command for configuration. The following instructions assume the use of miniconda. 

This software requires python version 3.7 or greater. 

### Install the Miniconda Python Distribution 

#### For a Windows installation: 
1. Download the latest miniconda installer from https://docs.conda.io/en/latest/miniconda.html. Scroll through the list of packages and find a recent version for python 3.7 or greater. 

2. Run the installer and accept the defaults unless you have specific reasons for changing them. 

3. From the Start menu, find the Anaconda entry and run the item called “Anaconda Prompt (miniconda3)”. 

4. Update the miniconda installation: 

		conda update conda 

#### For a Linux or Mac installation: 

1. Download the latest miniconda package:  

		wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh 

2. Install miniconda: 

		bash Miniconda3-latest-Linux-x86_64.sh
<Accept the default install location and answer yes to all questions.>

4. Activate the installer’s modifications to your .bash_profile file by closing the terminal window and starting a new terminal window. 

5. Test the installation by listing the installed conda packages: 

		conda list 

6. If your system cannot find the conda executable, then something went wrong with the modifications to your PATH environment variable. Either edit the path by hand or consult the Anaconda documentation for further instructions. 

7. Update the installation: 

		conda update conda 

### Create a Conda Environment 

A dedicated conda “environment” will be created for running the code. Conda environments are isolated from each other, can be activated and deactivated easily, and can be configured and updated independently from other environments. The isolation helps prevent incompatible software upgrades and other problems caused by shared system library folders. 
The environment will be called setnet and must be explicitly activated to run the code. 

From either a command terminal on Mac or Linux, or the miniconda prompt on Windows, run this command and accept the defaults when prompted: 

	conda create –-name setnet 

### Install Required Packages 

The next step is to activate the setnet environment and download and install the required python packages into it: 

conda activate setnet 
	conda install -c anaconda jupyter 
	conda install -c anaconda fuzzywuzzy 
	conda install -c anaconda sklearn 
	conda install -c anaconda squalchemy 

### Download the SET-NET NLP Code for Birth Defect Categorization

The code is housed in a Github repository, which can be downloaded to a local hard drive. Open a command terminal (or Miniconda prompt on Windows) and browse to a disk location where the SET-NET code should be downloaded. Clone the git repository with this command: 

	git clone https://github.com/CDCgov/SET-NET/tree/master/birthdefectcategorization 

### Run the Code 

Change directories to the location of the cloned repo on your system. 

	cd <path> 

Activate the setnet environment and launch Jupyter with this command: 

	conda activate setnet 
	jupyter notebook 

From the main Jupyter window, open the Jupyter notebook file SetNet_NLP _BirthDefects.ipynb.  

When running the code for the first time, set the path to the input file and output folder appropriate for your system. 

Run the notebook by selecting Restart & Clear Output from the Kernel menu, then Run All from the Cell menu. The notebook should run to completion. 

### Sample Data  

A dataset with 1000 rows of synthetic data is provided. These observations are simulated and should not be treated as real data.   

### Synthetic Data Codebook 

\# | Variable  | Type	| Values | Label
------ | --------- | ------ | ------ | -------
1 | ID  |  Int  | 1-1000 | Synthetic ID number |
2 | bg_icd    | Char  | Text  | ICD-10 or modified ICD-9 codes  |
3 | bg_icd_sp | Char  | Text  | Birth defect verbatim description  |

# Notices 

## Public Domain Standard Notice 
This repository constitutes a work of the United States Government and is not subject to domestic copyright protection under 17 USC § 105. This repository is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/). All contributions to this repository will be released under the CC0 dedication. By submitting a pull request you are agreeing to comply with this waiver of copyright interest. 

## License Standard Notice 
The repository utilizes code licensed under the terms of the Apache Software License and therefore is licensed under ASL v2 or later. 

This source code in this repository is free: you can redistribute it and/or modify it under the terms of the Apache Software License version 2, or (at your option) any later version. 

This source code in this repository is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the Apache Software License for more details. 

You should have received a copy of the Apache Software License along with this program. If not, see [http://www.apache.org/licenses/LICENSE-2.0.html](http://www.apache.org/licenses/LICENSE-2.0.html)

The source code forked from other open source projects will inherit its license. 

## Privacy Standard Notice 
This repository contains only non-sensitive, publicly available data and information. All material and community participation is covered by the [Disclaimer](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md) and [Code of Conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md). For more information about CDC's privacy policy, please visit [http://www.cdc.gov/other/privacy.html](https://www.cdc.gov/other/privacy.html).

## Contributing Standard Notice 

Anyone is encouraged to contribute to the repository by [forking](https://help.github.com/articles/fork-a-repo) and submitting a pull request. (If you are new to GitHub, you might start with a [basic tutorial](https://help.github.com/articles/set-up-git).) By contributing to this project, you grant a world-wide, royalty-free, perpetual, irrevocable, non-exclusive, transferable license to all users under the terms of the [Apache Software License v2](http://www.apache.org/licenses/LICENSE-2.0.html). 

All comments, messages, pull requests, and other submissions received through CDC including this GitHub page may be subject to applicable federal law, including but not limited to the Federal Records Act, and may be archived. Learn more at [http://www.cdc.gov/other/privacy.html](http://www.cdc.gov/other/privacy.html).

## Records Management Standard Notice 
This repository is not a source of government records, but is a copy to increase
collaboration and collaborative potential. All government records will be
published through the [CDC web site](http://www.cdc.gov).

## Additional Standard Notices 
Please refer to [CDC's Template Repository](https://github.com/CDCgov/template)
for more information about [contributing to this repository](https://github.com/CDCgov/template/blob/master/CONTRIBUTING.md),
[public domain notices and disclaimers](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md),
and [code of conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md).
