import math
import time
def round_down(num,digits):
    factor = 10.0 ** digits
    return math.floor(num * factor) / factor

class Account:
    def __init__(self,client,settings):
        self.createdAt = time.time()
        self.id = 0
        self.SETTINGS = settings
        self.client = client
        self.startingBalance = self.getStartingBalance()
        self.freeBalance = self.startingBalance
        self.orders = []
        self.closedOrders = []
        self.allClosedOrders = []
    def getStartingBalance(self):
        return 0.5#float(self.client.get_asset_balance(asset='BTC'))

    @property
    def fitness(self):
        return self.totalPercentageChange2/self.avgHODLTime if self.avgHODLTime > 0 else self.totalPercentageChange2/(self.avgHODLTime+1)

    @property
    def avgHODLTime(self):
        v = 0
        i = 0
        for order in self.orders + self.allClosedOrders:
            i += 1
            v += order.HODLTime/900
        return v/i if i > 0 else v/(i+1)

    @property
    def liveTime(self):
        return time.time() - self.createdAt
    @property
    def liveTimeText(self):
        v = time.time() - self.createdAt
      
        
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

    @property
    def BTCBalanceInOrder(self):
        b = 0
        for order in self.orders:
            if order.state in (FOrder.STATE.NEW, FOrder.STATE.FILLED):
                b += order.startingBTCBalance
        return b

    @property
    def currentTotalOrdersBalance(self):
        b = 0
        for order in self.orders:
            b += order.currentBTCBalance
        return b



    @property
    def theroeticalBalance(self):
        return self.freeBalance + self.currentTotalOrdersBalance
    
    @property
    def theoreticalProfit(self):
        return self.currentTotalOrdersBalance

    @property
    def BTCBuyQuantity(self):
        return self.startingBalance/5

    def createOrder(self,kline):
        if self.getOrder(kline):
            return False
            raise Exception(f'Order for {kline["s"]} already exists.')

        BTCBuyQuantity = self.BTCBuyQuantity

        if BTCBuyQuantity < 0.001 or self.freeBalance < BTCBuyQuantity:
            return False
            raise Exception(f'Not enought BTC balance ({self.freeBalance})')
        symbol = kline['s']
        symbolInfo = self.client.get_symbol_info(symbol)
        
        buyQuantity = self.getQuantity(kline,BTCBuyQuantity,symbolInfo)
        BTCFinalBuyQuantity = buyQuantity*kline['c']
        self.freeBalance -= BTCFinalBuyQuantity
        order = FOrder(self,kline,buyQuantity,BTCBuyQuantity)
        self.orders.append(order)
        return True
    def getQuantity(self,kline,BTCqty,info):
        quantity = BTCqty/kline['c']
        stepSize = None
        for item in info['filters']:
            if 'stepSize' in item.keys():
                stepSize = item['stepSize']
                break
        i = 0
        for char in stepSize:
            if char == '.':
                continue
            if char == '1':
                break
            i += 1

        quantity = round_down(quantity,i)
        return quantity

    def updateOrder(self,kline):
        o = self.getOrder(kline)
        if not o:
            return False

        o.update(kline)

    def getOrder(self,kline):
        for o in self.orders:
            if o.symbol == kline['s']:
                return o
        return None

    @property
    def openOrders(self):
        c = 0
        for o in self.orders:
            c += 1
        return c

    @property
    def openOrdersText(self):
        t = ''
        for o in self.orders:
            t += f'[{o.symbol} {round(o.percentageChange,2)}%] '
        return t

    @property
    def closedOrdersProfit(self):
        c = 0
        for order in self.allClosedOrders:
            c += order.profit
        return c 

    @property
    def closedOrdersText(self):
        t = ''
        for o in self.allClosedOrders:
            t += f'[{o.symbol} {round(o.percentageChange,2)}%] '
        return t

    @property
    def totalProfit(self):
        return self.theroeticalBalance - self.startingBalance

    @property
    def totalProfit2(self):
        return self.closedOrdersProfit

    @property
    def totalPercentageChange2(self):
        return ( (self.totalProfit2)/self.startingBalance )*100

    @property
    def totalPercentageChange(self):
        return ( (self.theroeticalBalance - self.startingBalance)/self.startingBalance )*100

    @property
    def text(self):
        t = f'Live time: {self.liveTimeText}\n| Profit: {"%.8f"%self.totalProfit2} BTC ({round(self.totalPercentageChange2,2)}%) (Fit: {self.fitness})\nCurrent BTC Balance: {"%.8f"%self.theroeticalBalance}\nStarting BTC Balance: {self.startingBalance}\n| Theor. Profit: {"%.8f"%(self.totalProfit2+self.theoreticalProfit)} BTC \nFree BTC Balance: {"%.8f"%self.freeBalance}\nBTC balance in order: {"%.8f"%self.BTCBalanceInOrder}\nOpen orders: {self.openOrders}\n{self.openOrdersText}\n\nClosed orders: {len(self.allClosedOrders)}\n{self.closedOrdersText}'
        return t
