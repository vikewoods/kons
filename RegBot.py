#!/usr/bin/python
# coding: utf8

import sys, getopt, spynner, urllib, os, uuid, time, datetime, re, inspect
from antigate import AntiGate

class Service:

    _st = time.time()

    def eval_time(self, time):
        return str(time-self._st)[0:5]

    def render_js(self, file_name, args):
        content = open(os.path.dirname(__file__)+'/js_templates/'+file_name+'.js','r').read()
        for key in args.keys():
            content = re.sub("{{ "+key+" }}", args[key], content)
        return content

    def file_put_contents(self, file_name, data, p = 'w+'):
        path = file_name.split('/');
        del path[len(path)-1]
        path = '/'.join([str(d) for d in path])
        if not os.path.isdir(path):
            os.makedirs(path)
        put_file = open(file_name, p)
        put_file.write(data)
        put_file.close()

    def log(self, log_type, status, p = "a+"):
        log_type_with_date = ['error']
        if not os.path.isdir(self.work_dir):
            os.makedirs(self.work_dir)
        log_file = open(self.work_dir+'/'+log_type+'_log.log',p)
        if (log_type in log_type_with_date):
            date = datetime.datetime.now()
            log_file.write('['+date.strftime("%Y-%m-%d %H:%M:%S")+']'+status+"\n")
        else:
            log_file.write(status)
        log_file.close()


class Main(Service):

    _ag  = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.22 (KHTML, like Gecko) Ubuntu Chromium/25.0.1364.160 Chrome/25.0.1364.160 Safari/537.22"
    _br  = spynner.Browser(user_agent=_ag)
    _ak  = "2e73e6eb4ecc471e007cd0e3bdb848e7" # this is api key for antigate.com
    _url = "https://by.e-konsulat.gov.pl/Uslugi/RejestracjaTerminu.aspx?IDUSLUGI=%s&IDPlacowki=%s"
    _rp = os.path.dirname(__file__)
    
    params = {
        'localeSelect': 'ctl00$ddlWersjeJezykowe',      #name   
        'captchaField': 'cp_KomponentObrazkowy_VerificationID',     #id/name
        'captchaSubmit': 'ctl00$cp$btnDalej',           #name   
        'serviceTypeSelect': 'ctl00$cp$cbRodzajUslugi', #name   
        'dateSelect': 'ctl00$cp$cbDzien',               #name   
        'dateSubmit': 'ctl00$cp$btnRezerwuj',           #name   
        'noDateHint': 'ctl00_cp_lblBrakTerminow'        #id     
    }

    def __init__(self, argv):
        try:
            opts, args = getopt.getopt(argv,"hc:m:t:a:d:p:s:",["--city","--maintype","--profile","--vizatype","--date","--proxy","--sid","--help"])
            argv = {str(opt):arg for opt, arg in opts}
            self._set_arguments(argv)
        except getopt.GetoptError:
            echo('RegBot -c <city> -m <maintype> -a <profile> -t <vizatype> -d <date> -p <proxy> -s <sid>','ERROR')
            echo('Try to use -h for help.','WARNING')
            sys.exit(2)
        if (hasattr(self, 'sid')):
            self.work_dir = self._rp+'/logs/'+self.sid
        else:
            self.work_dir = self._rp+'/logs'
        self.log('status', 'True', 'w+')
        if (hasattr(self, 'maintype') and hasattr(self, 'city')):
            self._url = self._url % (self.maintype, self.city)
        else:
            echo('[E] No arguments -c and -m. Try to use -h for help.','ERROR', self.work_dir)
            self.log('status', 'False', 'w+')
            self.log('error', inspect.stack()[0][3]+': [FATAL] No arguments -c and -m.\n')
            sys.exit(2)
        self.run()

    def _set_arguments(self, argv):
        if "-h" in argv: self._help();
        if "-c" in argv: self.city = argv["-c"];
        if "-m" in argv: self.maintype = argv["-m"];
        if "-t" in argv: self.vizatype = argv["-t"];
        if "-a" in argv: self.profile = argv["-a"];
        if "-d" in argv: self.date = argv["-d"];
        if "-p" in argv: self.proxy = argv["-p"];
        if "-s" in argv: self.sid = argv["-s"];

    def run(self):
        self.connect()
        self.passCaptcha()
        if (hasattr(self, 'vizatype')):
            self.serviceType(self.vizatype)
        if (hasattr(self, 'date')):
             status = self.choiceDate(self.date)
        else:
            status = self.choiceDate()
        if (status == True):
            if (hasattr(self, 'profile')):
                if (self.fillingProfile(self.profile)):
                    self.log('status', 'Done', 'w+')
                sys.exit()
            else:
                echo('[E] Unknown profile file.','ERROR', self.work_dir)
                self.log('status', 'False', 'w+')
                self.log('error', inspect.stack()[0][3]+': [FATAL] Unknown profile file.\n')
                sys.exit(2)
        else:
            self.run()

    def connect(self):
        if (hasattr(self, 'proxy')):
            self._br.set_proxy(self.proxy)
            echo('['+self.eval_time(time.time())+'] Set proxy ('+self.proxy+') is successfully.','SUCCESS', self.work_dir)
        else:
            echo('['+self.eval_time(time.time())+'] Proxy is not set.','WARNING', self.work_dir)
        try:
            status = self._br.load(self._url, load_timeout=15)
        except Exception, e:
            self.log('error', inspect.stack()[0][3]+': '+str(e)+'\n');
            echo(str(e).replace('Errno ', 'E-')+' Try connect to by.e-konsulat.gov.pl again.','ERROR', self.work_dir)
            self.run()
        else:
            if (status):
                echo('['+self.eval_time(time.time())+'] Connected successfully.','SUCCESS', self.work_dir)
                return True
            else:
                self.log('error', inspect.stack()[0][3]+': [FATAL] Connection refused.\n')
                echo('[E] Connection refused.','ERROR', self.work_dir)
                self.log('status', 'False', 'w+')
                sys.exit(2)

    def passCaptcha(self, show_browser = False):
        captchaCode = self._decodeCaptchaFile()
        self._br.runjs('document.querySelector(\'input[name="'+str(self.params.get('captchaField'))+'"]\').value="'+str(captchaCode)+'"')
        self._br.runjs('document.querySelector(\'input[name="'+str(self.params.get('captchaSubmit'))+'"]\').click()', True)
        self._br.wait(1)
        if (show_browser == True):
            self._br.browse()
        return True

    def serviceType(self, typeID, show_browser = False):
        self._br.runjs('var a=document.getElementsByName("'+str(self.params.get('serviceTypeSelect'))+'")[0].options;for(i in a){if(a[i].value=='+str(typeID)+')a[i].selected=true}')
        self._br.runjs(self.render_js('asp_ajax_send', {'selectName':str(self.params.get('serviceTypeSelect'))}))
        echo('['+self.eval_time(time.time())+'] Service type is selected: '+str(typeID),'SUCCESS', self.work_dir)
        self._br.wait(1)
        if (show_browser == True):
            self._br.browse()
        return True

    def choiceDate(self, date = None, show_browser = False):
        if (date == None):
            dateIndex = str(1)
            dateList = self._br.runjs(self.render_js('select_date', {
                'dateSelect': str(self.params.get('dateSelect')),
                'date': dateIndex
            })).toString()
            if (dateList == 'false'):
                # date = filter(lambda x:x.isdigit() or x==':' or x==' ',self._br.runjs('document.getElementById("'+str(self.params.get('noDateHint'))+'").innerHTML;').toString())
                date = self._br.runjs('document.getElementById("'+str(self.params.get('noDateHint'))+'").innerHTML;').toString().split(' ')
                echo('['+self.eval_time(time.time())+'] No available dates to '+date[len(date)-1]+'. Run "RegBot" again.','WARNING', self.work_dir)
                return False
            elif (dateList != 'true' and len(dateList) > 0):
                fileName = self.work_dir+'/date_list.log';
                self.file_put_contents(fileName, dateList);
                echo('['+self.eval_time(time.time())+'] Date list is saved in file: '+fileName,'SUCCESS', self.work_dir)
            dateValue = self._br.runjs('document.getElementsByName("'+str(self.params.get('dateSelect'))+'")[0].children['+dateIndex+'].text;').toString()
            echo('['+self.eval_time(time.time())+'] Date is selected: '+dateValue,'SUCCESS', self.work_dir)
        else:
            result = self._br.runjs(self.render_js('select_date', {
                'dateSelect': str(self.params.get('dateSelect')),
                'date': '"'+str(date)+'"'
            }))
            if (result == 'false'):
                echo('[E] Select of date is not found.', 'ERROR', self.work_dir)
                self.log('error', inspect.stack()[0][3]+': [FATAL] Select of date is not found.')
                self.log('status', 'False', 'w+')
                sys.exit(2)
            echo('['+self.eval_time(time.time())+'] Date is selected: '+str(date),'SUCCESS', self.work_dir)
        self._br.runjs('document.getElementsByName("'+str(self.params.get('dateSubmit'))+'")[0].removeAttribute("disabled");')
        self._br.wk_click('input[name="'+str(self.params.get('dateSubmit'))+'"]')
        self._br.wait(1)
        if (show_browser == True):
            self._br.browse()
        return True

    def fillingProfile(self, dataFile, show_browser = False):
        self._br.wait_a_little(1)
        echo('['+self.eval_time(time.time())+'] Yippee! current url: '+self._br.url,'SUCCESS', self.work_dir)
        if (show_browser == True):
            self._br.browse()
        return True

    def _decodeCaptchaFile(self):
        captchaImage = self._getCaptchaFile()
        try:
            captchaCode = AntiGate(self._ak, captchaImage, grab_config = {'connect_timeout':30,'timeout':60})
        except Exception, e:
            echo(str(e).replace('Errno ', 'E-')+' Try decode captcha again.','ERROR', self.work_dir)
            self.log('error', inspect.stack()[0][3]+': '+str(e));
            self.run()
        else:
            if (captchaCode):
                echo('['+self.eval_time(time.time())+'] Captcha code: '+str(captchaCode),'SUCCESS', self.work_dir)
                return captchaCode
            else:
                echo('[E] Error decode captcha file!','ERROR', self.work_dir)
                self.run()

    def _getCaptchaFile(self):
        imgUrl = self._br.runjs('document.getElementById("cp_KomponentObrazkowy_CaptchaImageID").getAttribute("src");').toString()
	imgUrl = imgUrl.trimmed('..')
	imgUrl = 'https://secure.e-konsulat.gov.pl' + imgUrl
        if (imgUrl == ''):
            self._setLocale()
            imgUrl = self._br.runjs('document.getElementById("cp_KomponentObrazkowy_CaptchaImageID").getAttribute("src");').toString()
        if (imgUrl):
            if not os.path.isdir(self.work_dir+'/captcha'):
                os.makedirs(self.work_dir+'/captcha')
            captchaName = str(uuid.uuid4())+'.png'
            imgName, imgRes = urllib.urlretrieve(str(imgUrl),self.work_dir+'/captcha/'+captchaName)
            echo('['+self.eval_time(time.time())+'] Captcha file saved: '+str(imgName),'SUCCESS', self.work_dir)
            return (imgName)
        else:
            echo('[E] Link to the captcha was not found!','ERROR', self.work_dir)
            self.log('error', inspect.stack()[0][3]+': [FATAL] Link to the captcha was not found!')
            self.log('status', 'False', 'w+')
            sys.exit(2)

    def _setLocale(self):
        self._br.runjs('document.getElementsByName("'+str(self.params.get('localeSelect'))+'")[0].options[2].selected = true')
        self._br.runjs(self.render_js('asp_ajax_send', {'selectName':str(self.params.get('localeSelect'))}))
        self._br.wait(1)

    def _help(self):
        echo('RegBot - python bot(script) for registration profiles on viza.','INFO')
        echo('Arguments (args with * is required):', 'INFO')
        echo('\t-c <city>* \t- city ​​to register (93-Brest, 94-Minsk, 95-Grodno)', 'INFO')
        echo('\t-m <maintype>* \t- main type registrations (1-Poland card, 7-National, 8-Shengen)', 'INFO')
        echo('\t-a <profile>* \t- file with profile data', 'INFO')
        echo('\t-t <vizatype> \t- type of visa (value from select)', 'INFO')
        echo('\t-d <date> \t- date for register. Can be null, then there bot is parents', 'INFO')
        echo('\t-p <proxy> \t- proxy server', 'INFO')
        echo('\t-s <sid> \t- alias for current bot','INFO')
        self.log('status', 'False','w+')
        self.log('error', inspect.stack()[0][3]+': [HELP] Was called help.\n')
        sys.exit()

class echo:

    HEADER = '\033[1m'+'\033[47m'+'\033[90m'
    INFO = '\033[94m'
    SUCCESS = '\033[92m'
    ERROR = '\033[37m'+'\033[41m'
    WARNING = '\033[93m'
    SHADOW = '\033[90m'
    _END = '\033[0m'

    def __init__(self, strLine, type = None, log_path = None):
        if (log_path != None):
            Service().file_put_contents(log_path+'/console_log.log', strLine+"\n",'a+');
        if (type != None and hasattr(self, type)):
            strLine = getattr(self,type)+strLine+self._END
        elif (not hasattr(self, type)):
            print [arg for arg in dir(self) if not arg.startswith('_')]
        print (strLine)

if __name__ == "__main__":
   Main(sys.argv[1:])
