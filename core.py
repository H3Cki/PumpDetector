import time
import math
from binance.client import Client
from binance.websockets import BinanceSocketManager
import binance.enums as be
from operator import itemgetter
import threading
from os import system
import json
import os
from win32com.client import Dispatch
import winshell
from Account import Account
import random


filename = 'settings.ini'

SETTINGS = {
'shortInterval':'15m',
'longInterval':'1d',
'minPrice':0.000001,
'maxShortIncrease': 999.0,
'maxLongTolerance': 1.0,
'jumpThresholds':[0.0,2.0,2.5],
'minSellPercentage': 1.0,
'maxLossPercentage': -1.0,
'minTrades': 0,
'stageForListing':1,
'printLimit':8,
'topXHighlighted': 3,
'minPrintInterval': 1.0,
'minSecondaryPrintInterval': 1.0,
'simpleValues': False,
'simpleValuesFormating': False,
'waitForNewKline': False,
'maxKlineTime' : 60,
'skipMenu': False
}

client = Client()
bm = BinanceSocketManager(client)



def floatize(kline):
    for key in kline['k']:
        try:
            kline['k'][key] = float(kline['k'][key])
        except:
            pass
def spacer(symbol,x=6):
        spaces = 6 - len(symbol[:-3])
        return " "*spaces

def customSpacer(short,lng):
    return " "*(len(lng)-len(short))

def loadConfig():
    global SETTINGS
    if os.path.isfile(filename):
        try:
            with open(filename,'r') as f:
                SETTINGS = json.load(f)
        except Exception as e:
            input(f"Loading config FAILED: {str(e)}")
            saveConfig()
    else:
        saveConfig()
    t = f'start cmd.exe /k "python {os.path.realpath(__file__)}"'
    bf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'PumpDetector3.bat')
    with open(bf_path,'w') as bf:
        bf.write(t)

    desktop = winshell.desktop()
    path = os.path.join(desktop, "PumpDetector3.lnk")
    target = bf_path
    wDir = os.path.dirname(os.path.abspath(__file__))
    icon = bf_path

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon
    shortcut.save()

def saveConfig(x=SETTINGS):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),filename),'w') as cf:
            json.dump(x,cf)
    except Exception as e:
        input(f"Saving config FAILED: {str(e)}")
      
loadConfig()





def unzero(n):
    n = f'{"%.8f"%n}'
    e = ['0','.',',']
    x = 0
    while n[0] in e:
        n = n[1:]
        x+=1
    if SETTINGS['simpleValuesFormating']:
        n = (" "*x)+n
    return n



class Candle:
    baseCandleLen = 57

    def __init__(self,klineObj,lng=False):
        self.parent = klineObj
        self.lng = lng

    @property
    def s(self):
        if self.lng:
            s = '█'
        else:
            s = '■'
        if self.parent.isPositive(day=self.lng) == 0:
                s = '|'
        return s
    @property
    def shadowSymbol(self):
        s = '─'
        if self.lng:
            if self.parent.dayKline['l'] == self.parent.dayKline['h']:
                s = ' '
        else:
            if self.parent.k['l'] == self.parent.k['h']:
                s = ' '
        return s

    @property
    def kline(self):
        if self.lng:
            return self.parent.dayKline
        else:
            return self.parent.k
    @property
    def totalCandleLen(self):
        return self.kline['h'] - self.kline['l']
    @property
    def candleLen(self): 
        candleLen = Candle.baseCandleLen
        if self.lng is False:
            totalDayCandleLen = self.parent.dayKlineCandle.totalCandleLen
            candleLen = int(candleLen * (self.totalCandleLen/totalDayCandleLen))
        return candleLen

    @property
    def bodyCandleSize(self):
        return abs(self.kline['o']-self.kline['c'])
    @property
    def lowerShadowCandleSize(self):
        if self.parent.isPositive(day=self.lng) == 1:
            lowerShadowCandleSize = self.kline['o'] - self.kline['l']
        elif self.parent.isPositive(day=self.lng) == -1:
            lowerShadowCandleSize = self.kline['c'] - self.kline['l']
        else:
            lowerShadowCandleSize = self.kline['c'] - self.kline['l']
        return lowerShadowCandleSize
    @property
    def upperShadowCandleSize(self):
        if self.parent.isPositive(day=self.lng) == 1:
            upperShadowCandleSize = self.kline['h'] - self.kline['c']
        elif self.parent.isPositive(day=self.lng) == -1:
            upperShadowCandleSize = self.kline['h'] - self.kline['o']
        else:
            upperShadowCandleSize = self.kline['h'] - self.kline['o']
        return upperShadowCandleSize



    @property
    def bodyPerc(self):
        return self.bodyCandleSize / self.totalCandleLen
    @property
    def lowerShadowPerc(self):
        return self.lowerShadowCandleSize / self.totalCandleLen
    @property
    def upperShadowPerc(self): 
        return  1 - self.lowerShadowPerc - self.bodyPerc



    @property
    def upperShadowLen(self):
        return math.floor(self.candleLen*self.upperShadowPerc)
    @property
    def lowerShadowLen(self):
        return self.candleLen - self.bodyLen - self.upperShadowLen
    @property
    def bodyLen(self):
        bodyStrLen = math.ceil(self.candleLen*self.bodyPerc)
        if bodyStrLen == 0 or bodyStrLen == 1:
            bodyStrLen = 1
            
        return bodyStrLen
    @property
    def totalLen(self):
        return self.bodyLen + self.lowerShadowLen+ self.upperShadowLen

        
    @property
    def bodyStr(self):
        return self.s*self.bodyLen
    @property
    def lowerShadowStr(self):
        return self.shadowSymbol*self.lowerShadowLen
    @property
    def upperShadowStr(self):
        return self.shadowSymbol*self.upperShadowLen

    @property
    def fullCandle(self):
        if self.totalCandleLen == 0:
            return self.dummyCandle
        t = self.lowerShadowStr + self.bodyStr + self.upperShadowStr

        lc = t[-1]
        while len(t) < self.candleLen:
            t += 'X'#lc
        while len(t) > self.candleLen:
            t = t[:-1]

        if self.lng is False:
            if self.parent.isPositive(day=True) >= 0 and self.parent.isPositive(day=False) >= 0:
                nSpaces = (self.parent.dayKlineCandle.lowerShadowLen + self.parent.dayKlineCandle.bodyLen) - (self.lowerShadowLen + self.bodyLen)
            elif self.parent.isPositive(day=True) < 0 and self.parent.isPositive(day=False) >= 0:
                nSpaces = self.parent.dayKlineCandle.lowerShadowLen - self.lowerShadowLen - self.bodyLen
            elif self.parent.isPositive(day=True) < 0 and self.parent.isPositive(day=False) < 0:
                nSpaces = self.parent.dayKlineCandle.lowerShadowLen - self.lowerShadowLen
            else:
                nSpaces = (self.parent.dayKlineCandle.lowerShadowLen + self.parent.dayKlineCandle.bodyLen) - self.lowerShadowLen
            
            t = " "*nSpaces + t
            postSpaces = Candle.baseCandleLen - len(t)
            t += " "*postSpaces
            
        return self.color + t + '\033[0;0m'

    @property
    def color(self):
        if self.parent.isPositive(day=self.lng) == 1:
            colour = '\033[32m'
            if self.parent.getLUTickChange(day=self.lng) > 0:
                colour = '\033[92m'
            elif self.parent.getLUTickChange(day=self.lng) < 0:
                colour = '\033[33;40m'
        elif self.parent.isPositive(day=self.lng) == -1:
            colour = '\033[31m'
            if self.parent.getLUTickChange(day=self.lng) > 0:
                colour = '\033[1;33;40m'
            elif self.parent.getLUTickChange(day=self.lng) < 0:
                colour = '\033[1;31;40m'
        else:
            colour = ''
        return colour

    @property
    def dummyCandle(self):
        return ' '*Candle.baseCandleLen

class Kline:
    class Stage:
        colors = ['','\033[1;33;40m','\033[1;36;40m']
        def __init__(self,kline):
            self.kline = kline
            self.stage = 0
            self.jumpThresholds = SETTINGS['jumpThresholds']
            self.listJumpsReq = SETTINGS['stageForListing']
            self.minPrice = SETTINGS['minPrice']
            self.jumps = [0 for _ in range(len(self.jumpThresholds))]
            self.maxStage = len(self.jumpThresholds)
            self.listed = False
            self.prices = [0 for _ in range(len(self.jumpThresholds))]
            self.message = ''
            self.constMessage = ''
            self.checkConditions()
            

        @property
        def jumpText(self):
            js = [f'+{round(j,2)}%' for j in self.jumps if j > 0]
            t = f'{self.getColor()}[Jumps: {", ".join(js)}]\033[0;0m'
            return t

        def jumpSum(self):
            x = 0
            for jump in self.jumps:
                x += jump
            return x
        def checkConditions(self):
            stage = 0
          

            if self.kline.k['c'] < SETTINGS['minPrice'] or self.kline.dayKline is None:
                self.listed = False
                return
            
            currentJump = round(self.kline.getOpenClosePercent(),2)

            i = 0
            accnr = 0
            for jt,j in zip(SETTINGS['jumpThresholds'],self.jumps):

                if j == 0:
                    if i == 0:
                        if currentJump > jt and self.kline.getTickChange() > 0:
                            self.jumps[i] = currentJump
                            stage += 1
                            self.message = ''
                        break
                    else:
                        if currentJump > jt and self.kline.getTickChange() > 0 and currentJump > self.jumps[i-1]:
                            self.jumps[i] = currentJump
                            stage += 1
                            break #?????????????????
                
                elif j > 0 :
                    self.message = ''
                    stage += 1
                
                i += 1

            if stage == len(SETTINGS['jumpThresholds']):
            
                b = True
                if self.kline.getClosePercent24h() > self.kline.getOpenClosePercent()+SETTINGS['maxLongTolerance']:
                    #self.message = f'> ! LONG TOO HIGH TO BUY ! <'
                    b = False
                if self.kline.getOpenClosePercent() > SETTINGS['maxShortIncrease']:
                    #self.message = f'> ! SHORT TOO HIGH TO BUY! <'
                    b = False
                if self.kline.getTradesN() < SETTINGS['minTrades']:
                    #self.message = f'> ! NOT ENOUGH TRADES ! <'
                    b = False
                '''
                if b:
                    #try:
                    account.createOrder(self.kline.k)#:
                        #self.constMessage += f" {self.getColor()}PURCHASED AT {self.kline.close}\033[0;0m"
                        #self.jumps = []
                    #except Exception as e:
                        #print(e)
                if accnr == 0:
                    self.stage = stage
                accnr = 
                '''
                
                
                

               
            self.stage = stage
            #self.stage = stage           
        
            if self.stage >= self.listJumpsReq:
                self.listed = True
            else:
                self.listed = False
                
        def text(self):
            return f'{self.stage}/{self.maxStage}'
        def getColor(self):
            cols = [37,33,32]
            final = 36
            if self.stage <= self.listJumpsReq:
                return ''
            if self.stage == self.maxStage:
                return f'\033[1;{final};40m'
            return f'\033[1;{cols[int(len(cols)*(self.stage/self.maxStage))-1]};40m'



    klines = {}
    t = ''
    lastPrint = 0
    lng = []
    srt = []
    @classmethod
    def printAll(cls,force=False):
        keys = list(cls.klines.keys())
        if keys == []:
            return
        if (not len(keys) or Kline.lastPrintDelta() < SETTINGS['minPrintInterval']) and force != True:
            return
        cls.lastPrint = time.time()
        k = keys[0]
        t = f'[Pump Detector 3.0] {cls.klines[k].getRemainingKlineTime(_str=True)}\n\n'


        c = 0
        lst = sorted(cls.klines.values(), key=lambda x: (x.stage.stage,x.getOpenClosePercent(),x.getTradesN()),reverse=True)
        x = SETTINGS['printLimit']
        if x:
            if len(lst) < 6:
                x = len(lst)
            wls = lst[:x]
        else:
            wls = lst
        i = 0

        ################################################################
        for k in wls:
            if cls.klines == {}:
                cls.lastPrint = 0
                return
            if k.stage.listed:
                if i < k.no:
                    up = 1
                elif i == k.no:
                    up = 0
                else:
                    up = -1
                k.no = i
                t += k.print(i,up=up)
                if i+1 == SETTINGS['topXHighlighted'] and SETTINGS['topXHighlighted']:
                    t+= f'\033[1;30;40mTOP {SETTINGS["topXHighlighted"]} ============================================================= TOP {SETTINGS["topXHighlighted"]} ============================================================= TOP {SETTINGS["topXHighlighted"]}\033[0;0m\n\n'
                k.luk = k.k
                if k.dayKline:
                    k.dluk = k.dayKline
                i+=1

        t += '\n'# + Detector.accountsText()
        #t += '\n' + f'{len(Detector.accounts)} Accounts.'
        cls.lastPrint = time.time()
        if t != '[Pump Detector 3.0]\n\n':
            system('cls')
            print(t)
        elif force:
            pass
            #system('cls')
            #print("NO JUMPS")
    
    @classmethod
    def lastPrintDelta(cls):
        return time.time() - Kline.lastPrint

    @classmethod
    def getKline(cls,symbol=None):
        return cls.klines.get(symbol)

    @property
    def low(self):
        if SETTINGS['simpleValues']:
            return unzero(self.k["l"])
        else:
            return f'{"%.8f"%self.k["l"]}'

    @property
    def high(self):
        if SETTINGS['simpleValues']:
            return unzero(self.k["h"])
        else:
            return f'{"%.8f"%self.k["h"]}'

    @property
    def close(self):
        if SETTINGS['simpleValues']:
            return unzero(self.k["c"])
        else:
            return f'{"%.8f"%self.k["c"]}'

    @property
    def open(self):
        if SETTINGS['simpleValues']:
            return unzero(self.k["o"])
        else:
            return f'{"%.8f"%self.k["o"]}'

    



    @property
    def dlow(self):
        if SETTINGS['simpleValues']:
            return unzero(self.dayKline["l"])
        else:
            return f'{"%.8f"%self.dayKline["l"]}'

    @property
    def dhigh(self):
        if SETTINGS['simpleValues']:
            return unzero(self.dayKline["h"])
        else:
            return f'{"%.8f"%self.dayKline["h"]}'

    @property
    def dclose(self):
        if SETTINGS['simpleValues']:
            return unzero(self.dayKline["c"])
        else:
            return f'{"%.8f"%self.dayKline["c"]}'

    @property
    def dopen(self):
        if SETTINGS['simpleValues']:
            return unzero(self.dayKline["o"])
        else:
            return f'{"%.8f"%self.dayKline["o"]}'



    def __init__(self,kline):
        self.no = 999
        self.dayKline = None
        self.symbol = kline['s']
        self.k = kline['k']
        self.pk = kline['k']
        self.dayKlineCandle = Candle(self,True)
        self.Candle = Candle(self)
        if Detector.wfnk and SETTINGS['waitForNewKline']:
            if self.getKlineTime() > SETTINGS['maxKlineTime']:
                Detector._wfnk = True
                t = self.getRemainingKlineTime()
                x = 0
                while x < int(t):
                    system('cls')
                    print(f'Waiting {self.getRemainingKlineTime(_str=True)} for new candle.')
                    time.sleep(1)
                    #if input('skip...') or 1:
                        #system("cls")
                        #print("Waiting for price action...")
                        #break
 

            Detector._wfnk = False
            Detector.wfnk = False
        self.stage = Kline.Stage(self)

        self.ready = False
        self.luk = self.k
        self.dluk = self.k
        self.dayKlineUpdated = False
        self.klineUpdated = False
        Kline.klines[self.symbol] = self

    @classmethod
    def create(cls,kline):
        floatize(kline)
        _k = Kline.getKline(kline['s'])
        if _k:
            _k.update(kline)
            return _k
        else:
            _k = Kline(kline)
        return _k

    def update(self,kline=None,day=False):
        if self.getRemainingKlineTime() <= 0:
            Kline.klines = {}
        


        if day:
            self.update24h(kline)
        elif kline:
            self.pk = self.k
            self.k = kline['k']
            self.klineUpdated = True
            if self.updatesDone:
                self.stage.checkConditions()
                if self.stage.listed:
                    Kline.printAll()
                    self.dayKlineUpdated = False
                    self.klineUpdated = False
    @property
    def updatesDone(self):
        if self.dayKlineUpdated == True and self.klineUpdated == True:
            return True
        return False
    def update24h(self,kline):
        self.dayKline = kline['k']
        self.dayKlineUpdated = True
    def getKlineTime(self):
        return (time.time()*1000 - self.k['t'])/1000
    def getRemainingKlineTime(self,_str=False):
        v = (self.k['T'] - time.time()*1000)/1000
        if _str:
          
            hours = math.floor(v/3600)
            minutes = math.floor((v - hours*3600)/60)
            secs = int(v - minutes*60 - hours*3600)
            t = ''
            if hours:
                t += f'{hours}h '
            if minutes:
                t += f'{minutes}m '
            if secs:
                t += f'{secs}s'    
            return t
        
        return v

    def getTickChange(self,day=False):
        if day:
            return self.dayKline['c'] - self.pk['c']
        else:
            return self.k['c'] - self.pk['c']

    def getLUTickChange(self,day=False):
        if day:
            return self.dayKline['c'] - self.dluk['c']
        else:
            return self.k['c'] - self.luk['c']

    def dummycandle(self,len):
        x = '─'
        return x*len
    
    def newHigh(self):
        if self.k['h'] > self.pk['h']:
            return True
        return

    def getVol(self,string=False):
        if not self.dayKline:
            return '???'
        v = float(self.dayKline["q"])
        if string:
            v = str(int(v))
        return v

    def getTradesN(self,string=False):
        if not self.dayKline:
            if string:
                return '???'
            else:
                return 0
        v = int(self.k["n"])
        if string:
            v = str(v)
        return v

    def getLUColor(self):
        if self.getLUTickChange() > 0:
            return '\033[92m'
        elif self.getLUTickChange() < 0:
            return '\033[1;31;40m'
        return ''

    def print(self,i=None,up=0):


        candle = self.Candle.fullCandle#self.getCandleText()
        candle24 = self.dayKlineCandle.fullCandle#self.getCandleText(day=True)
        pp = self.getOpenClosePercent()
        ppp = ' '
        if pp > 0:
            ppp = '+'
        elif pp < 0:
            ppp = ''

        ph = self.getOpenHighPercent()
        pph = ''
        if ph > 0:
            pph = '+'
        elif ph < 0:
            pph = ''

        

        dayx = self.getClosePercent24h(string=True)
        dayx2 =  self.getOpenHighPercent24h(string=True)
        if dayx2 != "???":
            dayx2 += f" ({self.dayKline['i']})"

        


        idx = ''
        upt = '-'
        uptn = '-'
        if up or i is not None:
            idx = f'[{str(i+1)}]'
        if self.getLUTickChange() > 0:
            upt = '\033[92m▲'
            uptn = '▲'
        elif self.getLUTickChange() < 0:
            upt = '\033[1;31;40m▼'
            uptn = '▼'

        header_t = f'{self.getLUColor()}{idx}{upt}[\033[1;36;40m{self.symbol}\033[0;0m{self.getLUColor()}]\033[0;0m {spacer(self.symbol)}{self.stage.getColor()}[{self.stage.text()}]\033[0;0m {self.getLUColor()}|{uptn}|\033[0;0m  {self.stage.jumpText} {self.getLUColor()}|{uptn}|\033[0;0m Price: {self.getLUColor()}{"%.8f"%self.k["c"]}\033[0;0m ({self.getLUColor()}{ppp}{"%.2f"%pp}%\033[0;0m) {self.stage.constMessage} {self.stage.message}\n'
        
        if self.dayKline:
            candle_td = f'       L: {self.dlow} \033[1;37;40m[O: {self.dopen}]\033[0;0m {candle24} \033[1;37;40m[C: {self.dclose}]\033[0;0m H: {self.dhigh} | \033[1;37;40m{dayx} / {dayx2}\033[0;0m\n'
        else:
            candle_td = ''

        candle_t = f'       L: {self.low} \033[1;35;40m[O: {self.open}]\033[0;0m {candle} \033[1;35;40m[C: {self.close}]\033[0;0m H: {self.high} | \033[1;35;40m{ppp}{"%.2f"%pp}% / {pph}{"%.2f"%ph}% ({self.k["i"]})\033[0;0m  {self.stage.getColor()}[{self.symbol}]\033[0;0m\n'
        footer_t = f'       {self.getLUColor()}[?] Vol. {self.getVol()} | Trades. {self.getTradesN()} | {self.getRemainingKlineTime(_str=True)}\033[0;0m\n\n'
        
        if up == 1:
            text = header_t  + '\033[92m▲\033[0;0m'+ candle_t[1:] + '\033[92m│\033[0;0m' + candle_td[1:] + '\033[92m│\033[0;0m'+ footer_t[1:]
        elif up == -1:
            text = header_t  + candle_t + '\033[1;31;40m│\033[0;0m'+candle_td[1:] +  '\033[1;31;40m▼\033[0;0m' +footer_t[1:]
        else:
            text = header_t  + candle_t + candle_td + footer_t
        return text

    def getHighlight(self):
        highlight = ''
        if self.getOpenClosePercent() > 1:
            highlight = '\033[6;30;47m'
        if self.newHigh():
            highlight = '\033[6;30;42m'
        return highlight

    def getOpenClosePercent(self):
        return ((self.k['c']-self.k['o'])/self.k['o'])*100
    def getOpenHighPercent(self,day=False):
        if day:
            return ((self.dayKline['h']-self.dayKline['o'])/self.dayKline['o'])*100 
        else:
            return ((self.k['h']-self.k['o'])/self.k['o'])*100  

    def getOpenHighPercent24h(self,string=False):
        if self.dayKline is None:
            if string:
                return "???"
            else:
                return -1

        v = ((self.dayKline['h']-self.dayKline['o'])/self.dayKline['o'])*100 
        if string:
            
            xppp = ' '
            if v > 0:
                xppp = '+'
            elif v < 0:
                xppp = ''
            v = f'{xppp}{"%.2f"%v}%'
        return v


    def getClosePercent24h(self,string=False):
        if self.dayKline is None:
            if string:
                return "???"
            else:
                return -1

        v = ((self.dayKline['c']-self.dayKline['o'])/self.dayKline['o'])*100 
        if string:
            
            xppp = ' '
            if v > 0:
                xppp = '+'
            elif v < 0:
                xppp = ''
            v = f'{xppp}{"%.2f"%v}%'
        return v

    def isPositive(self,day=False):
        if day:
            kline = self.dayKline
        else:
            kline = self.k

        if kline['c'] > kline['o']:
            return 1
        elif kline['c'] < kline['o']:
            return -1
        return 0

class Detector:
    accounts = []
    exchangeInfo = None
    symbols = []
    update = False
    wthread = None
    fuckup = False
    wfnk = SETTINGS['waitForNewKline']
    _wfnk = False
    @classmethod
    def getExchangeInfo(cls):
        cls.exchangeInfo = client.get_exchange_info()

    @classmethod
    def getAllSymbols(cls):
        if cls.exchangeInfo is None:
            cls.getExchangeInfo()
        
        cls.symbols = []
        cls.symbolOrders = {}
        for symbol in cls.exchangeInfo['symbols']:
            if symbol['quoteAsset'] == 'BTC':# and symbol['baseAsset'] == 'FTM':
                cls.symbols.append(symbol['symbol'])

            
    @staticmethod
    def handleKlineResponse(kline):
        if kline['e'] == 'error':
            print(kline['m'])
            return
        

        x = Kline.create(kline)
        
    @staticmethod
    def waitForKline(*kline):
        kline = kline[0]

        if kline['s'] not in Kline.lng:
            Kline.lng.append(kline['s'])
        
        floatize(kline)
        
        klin = Kline.getKline(kline['s'])
        while not klin:
            klin = Kline.getKline(kline['s'])
            time.sleep(0.1)

        if klin:
            klin.update(kline,day=True)
            
        return    

    @staticmethod
    def handle24hKlineResponse(kline):
        if kline['e'] == 'error':
            print(kline['m'])
            return

        Detector.wthread = threading.Thread(target=Detector.waitForKline, args=(kline,))
        Detector.wthread.start()
        
    @classmethod
    def updateorders(cls,*kline):
        kline = kline[0]
        for account in Detector.accounts:
            account.updateOrder(kline['k'])

    @staticmethod
    def handleKlineResponseMulti(kline):
        if Detector._wfnk:
            return
        if kline['e'] == 'error':
            print(kline['m'])
        else:
            if kline['k']['i'] == SETTINGS['longInterval']:
                Detector.handle24hKlineResponse(kline)
            else:
                Detector.handleKlineResponse(kline)
                #threading.Thread(target=Detector.updateorders,args=(kline,))
                

    @classmethod
    def startKlineSockets(cls):
        cls.connKeys = {}
        args = []
        for symbol in cls.symbols:
            cls.connKeys[symbol] = []
            c1 = bm.start_kline_socket(symbol, Detector.handleKlineResponseMulti,interval=SETTINGS['shortInterval'])
            c2 = bm.start_kline_socket(symbol, Detector.handleKlineResponseMulti,interval=SETTINGS['longInterval'])
            cls.connKeys[symbol].append(c1)
            cls.connKeys[symbol].append(c1)
        bm.start()
    
    @classmethod
    def getTopAcc(cls):
        cls.accounts = sorted(cls.accounts, key=lambda x: x.fitness,reverse=True)
        
        return cls.accounts[0]

    @classmethod
    def accountsText(cls):
        t = ''
        cls.getTopAcc()
        for x in range(0,2):
            t += f'\n\n[Acc {cls.accounts[x].id}]\n' + cls.accounts[x].text + f"\n{cls.accounts[x].SETTINGS}" 
        t += f'\n\n[Acc {cls.accounts[-1].id}]\n' + cls.accounts[-1].text + f"\n{cls.accounts[-1].SETTINGS}" 
        return t

    @classmethod
    def s(cls):
        while True:
            if Kline.klines != {}:
                if Kline.lastPrintDelta() >= SETTINGS['minSecondaryPrintInterval'] or Kline.lastPrint == 0:
                    for key,kline in list(Kline.klines.items()):
                        if Kline.klines == {}:
                            break
                        kline.update()
                    Kline.printAll(force=True)
                cls.accounts = sorted(cls.accounts,key=lambda x: x.fitness, reverse=True)
            time.sleep(0.25)
        return

    @classmethod
    def s2(cls):
        global ACCIDX
        while True:
            time.sleep(3600)
            n = 0
            
            half = int(len(cls.accounts)/10)
            cut = len(cls.accounts) - half
      
            cls.accounts = cls.accounts[:half]
  

            print(f'removed {cut} accounts')
            for setting in generateRandomSettings(cut):
                
                acc = Account(client,setting)
                acc.id = ACCIDX
                cls.accounts.append(acc)
               
                ACCIDX += 1
        return
    @classmethod
    def run(cls):
        global ACCIDX
        print('Initializing settings...')
        print("Getting exchange info...")
        cls.getExchangeInfo()
        print("Getting all symbols...")
        cls.getAllSymbols()
        print("Starting sockets...")
        cls.startKlineSockets()
        print("Starting loop...")
        threading.Thread(target=cls.s).start()
        threading.Thread(target=cls.s2).start()
        print("Waiting for socket events...")


def getIntervals():
    ivs = []
    for k in vars(be).keys():
        if 'INTERVAL' in k:
            ivs.append(vars(be)[k])
    return ', '.join(ivs)


if SETTINGS['skipMenu'] is False:
    x = int(input('1. RUN\n2. HELP\n3. SETTINGS\n') or 1)
    while x != 1:
        if x == 2:
            system('cls')
            print('[PUMP DETECTOR 3.0 made by H3Ck1]')
            print('\nProgram śledzi wyłącznie kryptowaluty z parą do BTC, odświeżenie każdej z nich odbywa się po otrzymaniu informacji o zmianie ceny. \nParametry programu:\n')
            print(f'\n- "shortInterval"             - interwał górnej świeczki (krótszej)')
            print(f'\n- "longInterval"              - interwał dolnej świeczki (dłuższej)')
            print(f'\n- "minPrice"                  - najnizsza cena danej waluty, która pozwala na przejscie do listy obserwowanych')
            print(f'\n- "minsellPercentage"         - minimalny przelicznik ceny, za którą zostanie sprzedana dana waluta (wartość 1.5 oznacza sprzedanie za cenę równą 101.5% ceny zakupu)')
            print(f'\n- "minTrades"                 - minimalna ilość trejdów w czasie krótkiej świeczki, która pozwoli na zakup waluty.')    
            print(f'\n- "maxLossPercentage"         - maksymalna strata w procentach, która spowoduje sprzedaż.')    

            print(f'\n- "maxShortIncrease"          - maksymany przyrost (w procentach) krótkiej świeczki, który pozwala na zakup waluty')
            print(f'\n- "maxLongTolerance"          - maksymalne odchylenie (w procentach) dłuższej świeczki od krótszej, które pozwala na zakup waluty (wartość 1.0 oznacza, że dłuższa świeczka moze być maksymalnie o 1% wyżej od krótszej, jeśli różnica jest większa nie dojdzie do zakupu')
            print(f'\n- "jumpThresholds"            - progi kolejnych etapów życia waluty (w procentach), każdy kolejny skok musi spełnić kolejny warunek na liście (dla przykładu mamy progi [0.0,2.0,2.5], jeśli waluta wzrośnie o więcej niż 0.0 będzie na etapie 1/3, jeśli następnie przyrost procentowy przekroczy 2.0 etap wzrośnie do 2/3 itd. Przyrost jest liczony od początku świeczki, nie od momentu uruchomienia programu')
            print(f'\n- "stageForListing"           - etap świeczki, od którego jest wyświetlana na liście obserwowanych')
            print(f'\n- "printLimit"                - maksymalna ilość wyświetlanych walut z listy obserwowanych')
            print(f'\n- "minPrintInterval"          - minimalny odstęp czasowy między odświeżeniami listy (krótsze odstępy mogą powodować miganie konsoli i szybki zanik efektów pojawiających się po skokach cen)')
            print(f'\n- "minSecondaryPrintInterval" - minimalny odstęp czasowy między odświeżeniami, kiedy waluty z listy obserwowanych stoją w miejscu (aktualizuje czas do końca świeczki)')
            print(f'\n- "simpleValues"              - usuwa zera z początku ceny kryptowaluty')
            print(f'\n- "simpleValuesFormating"     - zastępuje usunięte zera spacjami, aby zachować układ')
            print(f'\n- "waitForNewKline"           - po uruchomieniu program czeka na zakończenie obecnej świeczki')
            print(f'\n- "maxKlineTime"              - maksymalny dopuszczalny czas istnienia obecnej świeczki (w sekundach), który pomija czekanie na nową (jeśli jest włączona opcja waitForNewKline)')
            print(f'\n- "skipMenu"                  - wyłącza menu po starcie programu')
            input('\ncontinue...')
        if x == 3:
            system('cls')
            print(f'SETTINGS: [enter - pominięcie opcji]\nDostępne interwały: {getIntervals()}')
            for s in SETTINGS.items():
                if type(s[1]) in (int,float,str):
                    SETTINGS[s[0]] = type(s[1])(input(f'{s[0]} ({s[1]}): ') or s[1])
                elif type(s[1]) == list:
                    ipt = (input(f'{s[0]} ({s[1]}): ') or s[1])
                    if not isinstance(ipt,list):
                        items = ipt.replace(' ','')
                        items = ipt.replace(']','')
                        items = ipt.replace('[','')
                        for item in items:
                            if item == '':
                                items.remove(item)
                        try:
                            items = list(map(float,items.split(',')))
                        except:
                            input('ILLEGAL SYMBOL FOUND')
                            break
                    else:
                        items = ipt
                    SETTINGS[s[0]] = items
                elif type(s[1]) == bool:
                    SETTINGS[s[0]] = type(s[1])(int((input(f'{s[0]} ({int(s[1])}): ') or s[1])))
            print(f'\n[SELECTED SETTINGS]\n')    
            for s in SETTINGS.items():
                print(f'{s[0]} : {s[1]}')
            input('\nsave...')
            saveConfig(SETTINGS)
        system('cls')
        x = int(input('1. RUN\n2. HELP\n3. SETTINGS\n') or 1)


Detector.run()




