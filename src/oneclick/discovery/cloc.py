from oneclick.config import Config
from cast_common.logger import Logger,INFO
from cast_common.util import run_process,check_process,format_table,create_folder
from oneclick.discovery.sourceValidation import SourceValidation 
from time import sleep

from platform import system
from os.path import exists,abspath,getsize
from re import findall
from pandas import DataFrame,ExcelWriter

from string import ascii_uppercase
from win32api import GetLogicalDriveStrings
from win32wnet import WNetOpenEnum,WNetEnumResource
from win32netcon import RESOURCE_REMEMBERED,RESOURCETYPE_DISK

from ctypes import windll, c_int, c_wchar_p

#TODO: Convert total line to formulas (d1-SHP)
#TODO: Format all numbers as integers not text (d1-SHP)
#TODO: Group tabs in pairs (before, after) then by application (d2)

class ClocPreCleanup(SourceValidation):
    writer = None
    
    def __init__(cls, config: Config, log_level:int=INFO, name = None):
        if name is None: 
            name = cls.__class__.__name__

        super().__init__(config,cls.__class__.__name__,log_level)

        cls.config = config
        cls._df = {}
        pass

    @property
    def phase(cls):
        return 'Before'

    @property
    def cloc_base(cls):
        return f'{cls.config.base}\\cloc' 
    @property
    def cloc_project(cls):
        return f'{cls.cloc_base}\\{cls.config.project_name}'

    @property
    def cloc_results(cls):
        return cls._df

    def _get_free_drive(cls):
        drives = set(ascii_uppercase[2:])
        for d in GetLogicalDriveStrings().split(':\\\x00'):
            drives.discard(d)
        # Discard persistent network drives, even if not connected.
        henum = WNetOpenEnum(RESOURCE_REMEMBERED, 
            RESOURCETYPE_DISK, 0, None)
        while True:
            result = WNetEnumResource(henum)
            if not result:
                break
            for r in result:
                if len(r.lpLocalName) == 2 and r.lpLocalName[1] == ':':
                    drives.discard(r.lpLocalName[0])
        if drives:
            return sorted(drives)[-1] + ':'

    def _run_cloc(cls,work_folder:str,cloc_output:str,cloc_output_ignored:str):
        args = [cls.cloc_path,work_folder,"--report-file",cloc_output,"--ignored",cloc_output_ignored,"--quiet"]
        cls._log.info(' '.join(args))
        proc = run_process(args,False)

        sleep(10)
        if proc.poll() is not None and exists(cloc_output):
            return 'DONE'
        else:
            return proc

    def open_excel_writer(cls,config:Config):
        ClocPreCleanup.writer = ExcelWriter(abspath(f'{config.report}/{config.project_name}/{config.project_name}-cloc.xlsx'), engine='xlsxwriter')

    def run(cls,config:Config):
        cls.open_excel_writer(config)
        cls.cloc_path=abspath(f'{config.base}\\scripts\\{cls.config.cloc_version}')
        list_of_tech_file=abspath(f'{config.base}\\scripts\\ListOfTechnologies.csv')
        with open(list_of_tech_file) as f:
            tech_list = f.read().splitlines()
            
        process = {}
        cloc_run=False

        DefineDosDevice = windll.kernel32.DefineDosDeviceW
        DefineDosDevice.argtypes = [ c_int, c_wchar_p, c_wchar_p ]

        project_folder=abspath(f'{config.work}/AIP/{config.project_name}')
        # Create a subst. Check the return for non-zero to mean success
        drive=project_folder
        platform = system()
        if platform == 'Windows':
            drive = cls._get_free_drive()
            if DefineDosDevice(0, drive, project_folder ) == 0:
                raise RuntimeError("Subst failed")

        for appl in config.application:
            cls._log.info(f'Running {config.project_name}/{appl}')
            create_folder(f'{config.report}/{config.project_name}/{appl}')
            cloc_output = abspath(f'{config.report}/{config.project_name}/{appl}/{appl}-cloc-{cls.phase}.txt')
            cloc_output_ignored = abspath(f'{config.report}/{config.project_name}/{appl}/{appl}-cloc-ignored-{cls.phase}.txt')
            if platform == 'Windows':            
                work_folder = abspath(f'{drive}/{appl}')
            else:
                work_folder = abspath(f'{config.work}/AIP/{config.project_name}/{appl}')

            #if the report is already out there - no need to continue
            if exists(cloc_output):
                process[appl]=None
                continue 
            cloc_run=True
            process[appl] = cls._run_cloc(work_folder,cloc_output,cloc_output_ignored)

        #has all cloc processing completed
        all_done=False
        while (not all_done):
            all_done=True
            for p in process:
                if process[p]=='DONE':
                    continue
                all_done=False
                cloc_output = abspath(f'{config.report}/{config.project_name}/{p}/{p}-cloc-{cls.phase}.txt')
                cloc_output_ignored = abspath(f'{config.report}/{config.project_name}/{p}/{p}-cloc-ignored-{cls.phase}.txt')
                if not process[p] is None:
                    cls._log.info(f'Checking results for {config.project_name}/{p}')
                    try:
                        ret,output = check_process(process[p],False)
                        if ret != 0 and not exists(cloc_output) and getsize(cloc_output) == 0:
                            cls._log.error(f'Error running cloc on {cloc_output} ({ret})')
                    except IOError:
                        if not exists(cloc_output) and getsize(cloc_output) == 0:
                            cls._log.error(f'Error running cloc on {cloc_output} ({ret})')

                if exists(cloc_output):
                    process[p]='DONE'
            if cloc_run:
                sleep(60)

        # Delete the subst.
        if platform == 'Windows' and DefineDosDevice(2, drive, project_folder ) == 0:
            raise RuntimeError("Subst failed")

        for appl in config.application:
            #reading cloc_output.txt file
            cloc_output = abspath(f'{config.report}/{config.project_name}/{appl}/{appl}-cloc-{cls.phase}.txt')
            cloc_output_ignored = abspath(f'{config.report}/{config.project_name}/{appl}/{appl}-cloc-ignored-{cls.phase}.txt') 
            cls._log.info(f'Processing {cloc_output}')
            with open(cloc_output, 'r') as f:
                content = f.read()

            #extracting required data from content of cloc_output.txt using python regex
            header=content.split('\n')[2]
            header_list=findall('\w+',header.upper())

            summary='\n'.join(content.split('\n')[4:-4])
            pattern='(.{25})\s{1,}(\d{1,})\s{1,}(\d{1,})\s{1,}(\d{1,})\s{1,}(\d{1,})'
            statistics_list=findall(pattern,summary)
            
            with open(cloc_output_ignored, 'r') as fp:
                lines = len(fp.readlines())
            statistics_list.append(('Unknown Files','0','0','0',str(lines)))
            df = DataFrame(statistics_list,columns=header_list)

            #making technolgy case insensitive
            tech_list = list(map(lambda x: x.lower().strip(), tech_list))
            df['APPLICABLE']=df['LANGUAGE'].str.lower().str.strip().isin(tech_list)

            #converting column values into int from string
            numbers=['FILES','BLANK','COMMENT','CODE']
            total_line=['']
            for name in numbers:
                df[name] = df[name].astype('int')
            tab_name = f'{appl}-{cls.phase}'
            tab_name = (tab_name[:30] + '..') if len(tab_name) > 30 else tab_name
            workbook = format_table(ClocPreCleanup.writer,df,tab_name,total_line=True)
        return True



class ClocPostCleanup(ClocPreCleanup):

    def __init__(cls, config: Config, log_level:int=INFO, name = None):
        super().__init__(config,log_level,cls.__class__.__name__)

    def open_excel_writer(cls,config:Config):
        pass
    
    @property
    def phase(cls):
        return 'After'

    def run(cls,config:Config):
        super().run(config)
        sheet_names = ClocPreCleanup.writer.book.worksheets_objs.sort(key=lambda x: x.name)
        ClocPreCleanup.writer.close()
        pass



        