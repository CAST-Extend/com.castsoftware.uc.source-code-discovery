from logger import Logger
from config import Config

from analysis.analysis import Analysis
from unzip import Unzip
from prep import Prepare
from cloc import ClocPreCleanup,ClocPostCleanup
from cleanup import cleanUpAIP,cleanUpHL
from sqlDiscovery import SQLDiscovery
from analysis.highlight import Highlight
from logger import INFO
from argparse import ArgumentParser
from os.path import isfile,isdir
from pandas import ExcelWriter

#from discovery import Unzip,Prepare


from sourceValidation import SourceValidation 

__author__ = "Nevin Kaplan"
__email__ = "n.kaplan@castsoftware.com"
__copyright__ = "Copyright 2022, CAST Software"



if __name__ == '__main__':

    #printing some inital messages to the user
    log_level = INFO
    log = Logger("main")

    print('\nCAST automated cloc output, source dicovery and intial analysis')
    print('Copyright (c) 2022 CAST Software Inc.\n')
    print('If you need assistance, please contact Nevin Kaplan (NKA) from the CAST IN PS team\n')

    parser = ArgumentParser(description='One Click')
    parser.add_argument('-b','--baseFolder', required=True, help='Base Folder Location')
    parser.add_argument('-p','--projectName', required=True, help='Name of the project')
    parser.add_argument('-r','--reset', required=False,help='Cleanup all work and start over')
    parser.add_argument('-s','--start', required=False, help='Start from specific step')


    parser.add_argument('--hlURL', required=False, help='Highlight URL')
    parser.add_argument('--hlUser', required=False, help='Highlight User')
    parser.add_argument('--hlPassword', required=False, help='Highlight Password')
    parser.add_argument('-i','--hlInstance', required=True, help='Highlight Instance Id')
    
    args = parser.parse_args()

    config=Config()
    config.project=args.projectName    
    config.base=args.baseFolder
    config.reset=args.reset    

    if args.hlURL is not None: 
        config.hl_url=args.hlURL
    if args.hlUser is not None: 
        config.hl_user=args.hlUser
    if args.hlPassword is not None: 
        config.hl_password=args.hlPassword
    if args.hlInstance is not None: 
        config.hl_instance=args.hlInstance

    cloc_pre_cleanup = ClocPreCleanup(config,log_level)
    cloc_post_cleanup = ClocPostCleanup(config,log_level)
    workbook_name = f'{cloc_pre_cleanup.cloc_project}\\cloc-{config.project}.xlsx'
    writer = ExcelWriter(workbook_name, engine='xlsxwriter')

    process = [
        Prepare(log_level),
        Unzip(log_level),
        cloc_pre_cleanup,
        cleanUpAIP(log_level),
        cleanUpHL(log_level),
        cloc_post_cleanup,
        SQLDiscovery(log_level),
        Highlight(log_level)
    ]

    step = 1
    for p in process:
        log.info(f'Step {step} - {p.__class__.__name__}')
        if issubclass(type(p), SourceValidation) or issubclass(type(p), Analysis) :
            status = p.run(config)
        
        #generate the cloc exell file 
        if issubclass(type(p), ClocPreCleanup):
            p.format_table(writer)
            p.save_xlsx(writer)

        step += 1
