# -*- coding: utf-8 -*-

import datetime
import pandas as pd

import MetaTrader5 as mt5
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler


def loginmt5():
    """登录mt5返回实例"""
    # display data on the MetaTrader 5 package
    print("MetaTrader5 package author: ", mt5.__author__)
    print("MetaTrader5 package version: ", mt5.__version__)

    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return None

    # now connect to another trading account specifying the password
    account = 41138506
    authorized = mt5.login(account, password="dhq2fgox", server="MetaQuotes-Demo")
    if authorized:
        # display trading account data 'as is'
        print(mt5.account_info())
        # display trading account data in the form of a list
        print("Show account_info()._asdict():")
        account_info_dict = mt5.account_info()._asdict()
        print(account_info_dict)
        # for prop in account_info_dict:
        #     print("  {}={}".format(prop, account_info_dict[prop]))
        return mt5
    else:
        print("failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))
        return None


# shut down connection to the MetaTrader 5 terminal

mymt5 = loginmt5()


class fuckmt5:
    """
    在一分钟内寻找点差最小的点进行交易
    """

    def __init__(self, mt5=None, symbol=None, maxdiancha=3, lot=0.01, devitation=3):
        self.mt5 = mt5
        self.symbol = symbol
        self.maxdiancha = maxdiancha
        self.lot = lot
        self.winnum = 0
        self.baselot = 0.01
        self.deviation = devitation

    def get_history(self, period=None, num=3):
        # 获取过去的bar从当前开始
        mt5 = self.mt5
        period = period or mt5.TIMEFRAME_M1
        rates = mt5.copy_rates_from_pos(self.symbol, period, 0, num)  # 从当前到过去10条记录

        newlist = [{"开盘": i[1], "收盘": i[4], "差价": round((i[4] - i[1]) * 1000, len(str(i[1])) - 4)} for i in rates]
        print("过去的记录:", newlist)
        return newlist

    def get_direct(self):
        history = self.get_history()
        close = history[1]['收盘']
        is_win = (history[1]['差价'] > 0 and history[0]['差价'] > 0) or (history[1]['差价'] < 0 and history[0]['差价'] < 0)

        if history[1]["差价"] > 0:
            return ["buy", close, is_win]
        elif history[1]['差价'] < 0:
            return ["sell", close, is_win]
        elif history[0]['差价'] > 0:
            return ["buy", close, is_win]
        else:
            return ["sell", close, is_win]

    def buy(self):
        """
        市价买入函数，注意计算点差，点差太大不进行交易
        symbol:交易的品种 价格
        lots: 手数 0.01为迷你手
        deviation 买入允许最大价差
        """
        # 根据每个周期进行开仓平仓 统计价格
        mt5 = self.mt5
        symbol = self.symbol
        lot = self.lot
        deviation = self.deviation
        diancha = abs(mt5.symbol_info_tick(symbol).ask - mt5.symbol_info_tick(symbol).bid)
        if diancha < self.maxdiancha:
            """在固定点差范围内才进行买入 每秒钟检查一遍"""
            # point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).ask
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                # "sl": price - 100 * point,  # 止损
                # "tp": price + 100 * point,  # 止盈
                "deviation": deviation,  # 开单价格波动
                "magic": 234000,  # 标识码
                "comment": "开仓买入！！",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }

            # send a trading request
            result = mt5.order_send(request)
            # check the execution result
            print("1. 买入订单(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("2. 买入失败, retcode={}".format(result.retcode))
                # request the result as a dictionary and display it element by element
                result_dict = result._asdict()
                print(result_dict)
                if result.comment == 'Requote':
                    self.buy()
                # for field in result_dict.keys():
                #     print("   {}={}".format(field, result_dict[field]))
                #     # if this is a trading request structure, display it element by element as well
                #     if field == "request":
                #         traderequest_dict = result_dict[field]._asdict()
                #         for tradereq_filed in traderequest_dict:
                #             print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
                return None

            print("2. 买入成功, ", result)
            return result
        return None

    def sell(self):
        """
        市价卖出函数，注意计算点差，点差太大不进行交易
        symbol:交易的品种 价格
        lots: 手数 0.01为迷你手
        deviation 买入允许最大价差
        """
        # 根据每个周期进行开仓平仓 统计价格
        mt5 = self.mt5
        symbol = self.symbol
        lot = self.lot
        deviation = self.deviation
        diancha = abs(mt5.symbol_info_tick(symbol).ask - mt5.symbol_info_tick(symbol).bid)

        if diancha < self.maxdiancha:
            # point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).bid  # ask卖方的出价 bid买方出价
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                # "sl": price - 100 * point,  # 止损
                # "tp": price + 100 * point,  # 止盈
                "deviation": deviation,  # 开单价格波动
                "magic": 234000,  # 标识码
                "comment": "开仓卖出！！",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }

            # send a trading request
            result = mt5.order_send(request)
            # check the execution result
            print("1. 卖出订单(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("2. 卖出失败, retcode={}".format(result.retcode))
                # request the result as a dictionary and display it element by element
                result_dict = result._asdict()
                print(result_dict)
                if result.comment == 'Requote':
                    self.sell()
                # for field in result_dict.keys():
                #     print("   {}={}".format(field, result_dict[field]))
                #     # if this is a trading request structure, display it element by element as well
                #     if field == "request":
                #         traderequest_dict = result_dict[field]._asdict()
                #         for tradereq_filed in traderequest_dict:
                #             print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
                return None

            print("2. 卖出成功, ", result)
            return result
        return None

    def fill(self, result=None, lot=0.01):  # 这里应该是平掉所有的仓
        """
        平仓函数，注意计算点差，点差太大不进行交易
        symbol:交易的品种 价格
        lots: 手数 0.01为迷你手
        deviation 买入允许最大价差
        """
        # 根据每个周期进行开仓平仓 统计价格
        mt5 = self.mt5
        symbol = self.symbol
        deviation = self.deviation
        diancha = abs(mt5.symbol_info_tick(symbol).ask - mt5.symbol_info_tick(symbol).bid)
        # if diancha < self.maxdiancha:
        if result.request.type == mt5.ORDER_TYPE_BUY:
            deal_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            deal_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask

        position_id = result.order

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": deal_type,
            "position": position_id,
            "price": price,
            "deviation": deviation,
            "magic": 234000,
            "comment": "关闭订单！",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        # send a trading request
        result2 = mt5.order_send(request)
        # check the execution result
        print("1. 平仓订单(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
        if result2.retcode != mt5.TRADE_RETCODE_DONE:
            print("2. 平仓订单失败, retcode={}".format(result2.retcode))
            # request the result as a dictionary and display it element by element
            result_dict = result2._asdict()
            print(result_dict)
            if result2.comment == 'Requote':
                self.fill(result,lot)
            # for field in result_dict.keys():
            #     print("   {}={}".format(field, result_dict[field]))
            #     # if this is a trading request structure, display it element by element as well
            #     if field == "request":
            #         traderequest_dict = result_dict[field]._asdict()
            #         for tradereq_filed in traderequest_dict:
            #             print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
            return None

        print("2. 平仓订单成功, ", result2)
        return result2

    def open(self):
        """开新仓 平旧仓函数"""
        predict = self.get_direct()
        is_win = predict[2]
        if is_win:
            if self.winnum == 3:
                self.winnum = 0
                self.lot = (2 ** self.winnum) * self.baselot
            else:
                self.winnum += 1
                self.lot = (2 ** self.winnum) * self.baselot
        else:
            self.winnum = 0
            self.lot = (2 ** self.winnum) * self.baselot
        # 根据winnum判断是否加仓
        if predict[0] == "buy":
            result = self.buy()
            run_date = datetime.datetime.now() + datetime.timedelta(seconds=59)
            if result:
                print("开始平仓。。。。。")
                scheduler = BackgroundScheduler()
                scheduler.add_job(self.fill, 'date', run_date=run_date, args=[result, self.lot])
                scheduler.start()
        elif predict[0] == "sell":
            result = self.sell()
            run_date = datetime.datetime.now() + datetime.timedelta(seconds=59)
            if result:
                print("开始平仓。。。。。")
                scheduler = BackgroundScheduler()
                scheduler.add_job(self.fill, 'date', run_date=run_date, args=[result, self.lot])
                scheduler.start()

    def start(self):  # 定时器函数
        scheduler = BlockingScheduler()
        scheduler.add_job(self.open, 'cron', day_of_week='*', hour='*', minute="*", second=1, )
        scheduler.start()


# fuckmt5(mt5=mymt5,symbol="EURUSD").buy()
fuckmt5(mt5=mymt5, symbol="EURUSD").start()

# 获取未平仓的商品的价格
# biaodi = "EURUSD"
#
# positions = mt5.positions_get(symbol=biaodi)
# if not positions:
#     print("No positions on USDCHF, error code={}".format(mt5.last_error()))
# else:
#     print("Total positions on USDCHF =", len(positions))
#     # display all open positions
#     print("usdchf结果",positions)
#     # for position in positions:
#     #     print(position)


# request 1000 ticks from EURAUD
# euraud_ticks = mt5.copy_ticks_from("EURAUD", datetime(2020, 1, 28, 13), 1000, mt5.COPY_TICKS_ALL)
# # request ticks from AUDUSD within 2019.04.01 13:00 - 2019.04.02 13:00
# audusd_ticks = mt5.copy_ticks_range("AUDUSD", datetime(2020, 1, 27, 13), datetime(2020, 1, 28, 13), mt5.COPY_TICKS_ALL)
#
# # get bars from different symbols in a number of ways
# eurusd_rates = mt5.copy_rates_from("EURUSD", mt5.TIMEFRAME_M1, datetime(2020, 1, 28, 13), 1000)
# eurgbp_rates = mt5.copy_rates_from_pos("EURGBP", mt5.TIMEFRAME_M1, 0, 1000)
# eurcad_rates = mt5.copy_rates_range("EURCAD", mt5.TIMEFRAME_M1, datetime(2020, 1, 27, 13), datetime(2020, 1, 28, 13))
#
# # shut down connection to MetaTrader 5
# mt5.shutdown()
#
# # DATA
# print('euraud_ticks(', len(euraud_ticks), ')')
# for val in euraud_ticks[:10]: print(val)
#
# print('audusd_ticks(', len(audusd_ticks), ')')
# for val in audusd_ticks[:10]: print(val)
#
# print('eurusd_rates(', len(eurusd_rates), ')')
# for val in eurusd_rates[:10]: print(val)
#
# print('eurgbp_rates(', len(eurgbp_rates), ')')
# for val in eurgbp_rates[:10]: print(val)
#
# print('eurcad_rates(', len(eurcad_rates), ')')
# for val in eurcad_rates[:10]: print(val)
#
# # PLOT
# # create DataFrame out of the obtained data
# ticks_frame = pd.DataFrame(euraud_ticks)
# # convert time in seconds into the datetime format
# ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
# # display ticks on the chart
# plt.plot(ticks_frame['time'], ticks_frame['ask'], 'r-', label='ask')
# plt.plot(ticks_frame['time'], ticks_frame['bid'], 'b-', label='bid')
#
# # display the legends
# plt.legend(loc='upper left')
#
# # add the header
# plt.title('EURAUD ticks')
#
# # display the chart
# plt.show()


# 获取某个品种的详情
# display EURJPY symbol properties
# symbol_info = mt5.symbol_info("EURUSD")
# if symbol_info != None:
#     # display the terminal data 'as is'
#     print(symbol_info)
#     print("EURUSD: spread =", symbol_info.spread, "  digits =", symbol_info.digits)
#     # display symbol properties as a list
#     print("Show symbol_info(\"EURUSD\")._asdict():")
#     symbol_info_dict = mt5.symbol_info("EURUSD")._asdict()
#     print(symbol_info_dict)
#     # for prop in symbol_info_dict:
#     #     print("  {}={}".format(prop, symbol_info_dict[prop]))


# symbol = "EURUSD"
# symbol_info = mt5.symbol_info(symbol)
# if symbol_info is None:
#     print(symbol, "not found, can not call order_check()")
#     mt5.shutdown()
#     quit()
#
# # if the symbol is unavailable in MarketWatch, add it
# if not symbol_info.visible:
#     print(symbol, "is not visible, trying to switch on")
#     if not mt5.symbol_select(symbol, True):
#         print("symbol_select({}}) failed, exit", symbol)
#         mt5.shutdown()
#         quit()