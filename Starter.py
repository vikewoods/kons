#!/usr/bin/python
# coding: utf8

import sys, os, uuid, time, datetime, re, inspect, json, subprocess, threading

class Main:

    logs = 'logs'

    threads = {}
    subprocess = {}
    process_tree = {}

    def __init__(self):
        echo() # clear log file
        self.profile_mappings = self.getProfilesMapping();
        if (self.profile_mappings == False):
            echo('['+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] Could not start. No profiles.', 'ERROR')
            sys.exit(2)
        for mapping in self.profile_mappings:
            self.run_threads(mapping)

    def run_threads(self, mapping, parent = None):
        alias = str(uuid.uuid4())
        self._process_tree(mapping,alias,parent)
        self.threads[alias] = threading.Thread(target=self.run_subprocess, args = (alias, mapping))
        self.threads[alias].start()

    def run_subprocess(self, alias, mapping):
        command_line = 'python RegBot.py'
        command_line += ' -c '+mapping['city']+' -m '+mapping['mainType'];
        if 'vizaType' in mapping: command_line += ' -t '+mapping['vizaType'];
        if 'date' in mapping: command_line += ' -d \''+mapping['date']+'\'';
        command_line += ' -a '+mapping['profile']+' -s '+alias;
        self.subprocess[alias] = subprocess.Popen(command_line, shell = True, stdout = subprocess.PIPE)
        echo('['+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] Start bot: '+alias+' with PID '+str(self.subprocess[alias].pid+1), 'SUCCESS')
        echo('> '+command_line, 'INFO')
        self.sub_checker(alias, mapping)

    def sub_checker(self, alias, mapping):
        self.waitForLogs(alias)
        status_log = self.logs+'/'+alias+'/status_log.log'
        error_log = self.logs+'/'+alias+'/error_log.log'
        date_list = self.logs+'/'+alias+'/date_list.dat'
        date_list_exist = False
        execute_status = 'True'
        while execute_status == 'True':
            execute_status = re.sub('\n','',open(status_log,'r').read())
            if (os.path.isfile(date_list) and date_list_exist == False):
                mappings = self.getProfilesForChildrens(mapping)
                dateList = open(date_list,'r').read().split('\n')
                if (len(mappings) > 0):
                    echo('['+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] Bot '+alias+' returned list of dates.', 'SUCCESS')
                    c = len(dateList) if (dateList<mappings) else len(mappings)
                    for i in range(c):
                        mappings[i]['date'] = dateList[i]
                        self.run_threads(mappings[i], alias)
                else:
                    echo('['+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] Bot '+alias+' returned list of dates. Not enough profiles.', 'WARNING')
                date_list_exist = True
            time.sleep(1)
        if (execute_status == 'False'):
            errors = open(error_log,'r').readlines()
            error = errors[len(errors)-2]
            echo('['+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] Bot stoped with crash.', 'WARNING')
            echo(re.sub('\n','',error), 'ERROR')
        if (execute_status == 'Done' and date_list_exist == False):
            echo('['+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] Bot '+alias+' do not return list of dates.', 'WARNING')
        self.subprocess[alias].kill()
        echo('['+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] Stop bot: '+alias+' with PID '+str(self.subprocess[alias].pid+1), 'WARNING')

    def getProfilesMapping(self):
        mappings = []
        if not os.path.isdir("profiles"):
            return False
        for (p,d,files) in os.walk("profiles"):
            if (len(files) > 0):
                mapping = {}
                for b in re.sub('profiles\/*','',p).split('/'):
                    arg = b.split("-")
                    if 'c' in arg: mapping['city'] = arg[1];
                    elif 'm' in arg: mapping['mainType'] = arg[1];
                    elif 't' in arg: mapping['vizaType'] = arg[1];
                mapping['profile'] = files[0]
                mappings += [mapping]
        if (len(mappings) > 0):
            return mappings
        else:
            return False

    def getProfilesForChildrens(self, mapping):
        mappings = []
        profilePath = 'profiles/c-'+mapping['city']+'/m-'+mapping['mainType']
        if ('vizaType' in mapping): profilePath += '/t-'+mapping['vizaType'];
        profilesList = os.listdir(profilePath)
        if (mapping['profile'] in profilesList and len(profilesList) > 1):
            del profilesList[profilesList.index(mapping['profile'])]
            for profile in profilesList:
                mapping['profile'] = profile
                mappings += [mapping]
            return mappings
        else:
            return None

    def waitForLogs(self, alias):
        status = True
        while status:
            if os.path.isdir(self.logs+'/'+alias):
                status = False
            time.sleep(1)

    def _process_tree(self,mapping,alias,parent = None):
        if (parent == None):
            self.process_tree[str(alias)] = {'mapping': mapping.copy(), 'childrens': []}
        else:
            self.process_tree[str(parent)]['childrens'] += {'alias': str(alias), 'mapping': mapping.copy()}

        open('process_tree.json','w+').write(json.dumps(self.process_tree))



class echo:

    HEADER = '\033[1m'+'\033[47m'+'\033[90m'
    INFO = '\033[94m'
    SUCCESS = '\033[92m'
    ERROR = '\033[37m'+'\033[41m'
    WARNING = '\033[93m'
    SHADOW = '\033[90m'
    _END = '\033[0m'

    def __init__(self, strLine = None, type = None):
        if (strLine == None):
            log = open('starter.log','w+')
            log.close()
        else:
            log = open('starter.log','a+')
            log.write(strLine+'\n')
            log.close()
            if (type != None and hasattr(self, type)):
                strLine = getattr(self,type)+strLine+self._END
            elif (not hasattr(self, type)):
                print [arg for arg in dir(self) if not arg.startswith('_')]
            print (strLine)

if __name__ == "__main__":
   Main()