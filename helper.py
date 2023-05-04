import pandas as pd
from datetime import datetime
import numpy as np
import os
import eikon as ek
import refinitiv.data as rd

#####################################################
def query_date(start_date_str, end_date_str, asset):
    ek.set_app_key(os.getenv('EIKON_API'))

    # start_date_str = '2023-01-30'
    # end_date_str = '2023-02-08'

    ivv_prc, ivv_prc_err = ek.get_data(
        instruments = [asset],
        fields = [
            'TR.OPENPRICE(Adjusted=0)',
            'TR.HIGHPRICE(Adjusted=0)',
            'TR.LOWPRICE(Adjusted=0)',
            'TR.CLOSEPRICE(Adjusted=0)',
            'TR.PriceCloseDate'
        ],
        parameters = {
            'SDate': start_date_str,
            'EDate': end_date_str,
            'Frq': 'D'
        }
    )

    ivv_prc['Date'] = pd.to_datetime(ivv_prc['Date']).dt.date
    ivv_prc.drop(columns='Instrument', inplace=True)
    return ivv_prc

def get_next_business_day(ivv_prc):
    ##### Get the next business day from Refinitiv!!!!!!!
    rd.open_session()

    next_business_day = rd.dates_and_calendars.add_periods(
        start_date= ivv_prc['Date'].iloc[-1].strftime("%Y-%m-%d"),
        period="1D",
        calendars=["USA"],
        date_moving_convention="NextBusinessDay",
    )

    rd.close_session()

    return next_business_day
######################################################

# # Parameters:
# alpha1 = -0.01
# n1 = 3
#
def generateOrders(alpha1, n1, alpha2, n2, ivv_prc, asset_id):
    next_business_day = get_next_business_day(ivv_prc)
    # submitted entry orders
    submitted_entry_orders = pd.DataFrame({
        "trade_id": range(1, ivv_prc.shape[0]),
        "date": list(pd.to_datetime(ivv_prc["Date"].iloc[1:]).dt.date),
        #"asset": "IVV",
        "asset": asset_id,
        "trip": 'ENTER',
        "action": "BUY",
        "type": "LMT",
        "price": round(
            ivv_prc['Close Price'].iloc[:-1] * (1 + alpha1),
            2
        ),
        'status': 'SUBMITTED'
    })

    # if the lowest traded price is still higher than the price you bid, then the
    # order never filled and was cancelled.
    with np.errstate(invalid='ignore'):
        cancelled_entry_orders = submitted_entry_orders[
            np.greater(
                ivv_prc['Low Price'].iloc[1:][::-1].rolling(n1).min()[::-1].to_numpy(),
                submitted_entry_orders['price'].to_numpy()
            )
        ].copy()
    cancelled_entry_orders.reset_index(drop=True, inplace=True)
    cancelled_entry_orders['status'] = 'CANCELLED'
    cancelled_entry_orders['date'] = pd.DataFrame(
        {'cancel_date': submitted_entry_orders['date'].iloc[(n1-1):].to_numpy()},
        index=submitted_entry_orders['date'].iloc[:(1-n1)].to_numpy()
    ).loc[cancelled_entry_orders['date']]['cancel_date'].to_list()
    #print(cancelled_entry_orders)

    filled_entry_orders = submitted_entry_orders[
        submitted_entry_orders['trade_id'].isin(
            list(
                set(submitted_entry_orders['trade_id']) - set(
                    cancelled_entry_orders['trade_id']
                )
            )
        )
    ].copy()
    filled_entry_orders.reset_index(drop=True, inplace=True)
    filled_entry_orders['status'] = 'FILLED'
    for i in range(0, len(filled_entry_orders)):

        idx1 = np.flatnonzero(
            ivv_prc['Date'] == filled_entry_orders['date'].iloc[i]
        )[0]

        ivv_slice = ivv_prc.iloc[idx1:(idx1+n1)]['Low Price']

        fill_inds = ivv_slice <= filled_entry_orders['price'].iloc[i]

        if (len(fill_inds) < n1) & (not any(fill_inds)):
            filled_entry_orders.at[i, 'status'] = 'LIVE'
        else:
            filled_entry_orders.at[i, 'date'] = ivv_prc['Date'].iloc[
                fill_inds.idxmax()
            ]

    live_entry_orders = pd.DataFrame({
        "trade_id": ivv_prc.shape[0],
        "date": pd.to_datetime(next_business_day).date(),
        "asset": asset_id,
        "trip": 'ENTER',
        "action": "BUY",
        "type": "LMT",
        "price": round(ivv_prc['Close Price'].iloc[-1] * (1 + alpha1), 2),
        'status': 'LIVE'
    },
        index=[0]
    )

    if any(filled_entry_orders['status'] =='LIVE'):
        live_entry_orders = pd.concat([
            filled_entry_orders[filled_entry_orders['status'] == 'LIVE'],
            live_entry_orders
        ])
        live_entry_orders['date'] = pd.to_datetime(next_business_day).date()

    filled_entry_orders = filled_entry_orders[
        filled_entry_orders['status'] == 'FILLED'
        ]

    entry_orders = pd.concat(
        [
            submitted_entry_orders,
            cancelled_entry_orders,
            filled_entry_orders,
            live_entry_orders
        ]
    ).sort_values(["date", 'trade_id'])


    ##get inital submitted exit orders:
    submitted_exit_orders = filled_entry_orders.copy()
    submitted_exit_orders.reset_index(drop=True, inplace=True)
    ##update the attribute
    submitted_exit_orders["trip"] = "EXIT"
    submitted_exit_orders["action"] = "SELL"
    submitted_exit_orders["status"] = "SUBMITTED"
    ##update price
    submitted_exit_orders["price"] = round(submitted_exit_orders["price"]*(1 + alpha2), 2)
    # print(submitted_exit_orders)
    # print(ivv_prc)
    # print("---------------------------------------------------------------------")
    # ##get all closed  orders，如果可以fill则fill，如果不能fill并且不够n2天则live
    # print(submitted_exit_orders)
    exit_orders = submitted_exit_orders.copy()
    exit_mkt_orders = pd.DataFrame(columns=exit_orders.columns)


    # for i in range(0, len(submitted_exit_orders)):
    #     idx1 = np.flatnonzero(
    #         ivv_prc['Date'] == submitted_exit_orders['date'].iloc[i]
    #     )[0]
    #
    #     # 先跟当天的close price比，如果满足直接FILLED
    #     if ivv_prc.iloc[idx1]["Close Price"] >= submitted_exit_orders['price'].iloc[i]:
    #         exit_orders.at[i, 'status'] = 'FILLED'
    #         continue
    #
    #     ivv_slic = ivv_prc.iloc[idx1+1:idx1+n2]['High Price']
    #
    #     # # test slice
    #     # test_slic = ivv_prc.iloc[idx1:idx1+n2]['Date']
    #     # print("my date is:")
    #     # print(submitted_exit_orders['date'].iloc[i])
    #     # print("compare to date:")
    #     # print(test_slic)
    #
    #     fill_inds = ivv_slic >= submitted_exit_orders['price'].iloc[i]
    #     # 如果不能fill并且不够n2天则live，修改status
    #     # update: 因为状态是live，修改时间为最新时间
    #     if(len(fill_inds) < n2) & (not any(fill_inds)):
    #         exit_orders.at[i, 'status'] = 'LIVE'
    #         exit_orders.at[i, 'date'] = ivv_prc.iloc[-1]['Date']
    #     # 如果可以fill则fill，修改price为卖出的price(update:不修改)，date为卖出的日期，status为FILLED
    #     elif any(fill_inds):
    #         # idxt = fill_inds.idxmax()
    #         idxt = fill_inds.idxmax()
    #         exit_orders.at[i, 'date'] = ivv_prc['Date'].iloc[idxt]
    #         # exit_orders.at[i, 'price'] = ivv_prc['High Price'].iloc[idxt]
    #         exit_orders.at[i, 'status'] = 'FILLED'
    #     # 如果不能fill，修改price为close date的price，date为close date，status为CLOSED
    #     else:
    #         idxt = idx1+n2-1
    #         exit_orders.at[i, 'date'] = ivv_prc['Date'].iloc[idxt]
    #         exit_orders.at[i, 'price'] = ivv_prc['Close Price'].iloc[idxt]
    #         exit_orders.at[i, 'status'] = 'CLOSED'
    # # 合并submitted和live&filled
    # exit_orders = pd.concat(
    #     [
    #         submitted_exit_orders,
    #         exit_orders
    #     ]
    # ).sort_values(['trade_id', "date"])
    # print("final result----------")
    # print(exit_orders)

    for index, exit_order in submitted_exit_orders.iterrows():

        # was it filled the day it was submitted?
        if float(
                ivv_prc.loc[ivv_prc['Date'] == exit_order['date'], 'Close Price']
        ) >= exit_order['price']:
            exit_orders.at[index, 'status'] = 'FILLED'
            continue

        window_prices = ivv_prc[ivv_prc['Date'] > exit_order['date']].head(n2)

        # was it submitted on the very last day for which we have data?
        if window_prices.size == 0:
            exit_orders.at[index, 'date'] = pd.to_datetime(
                next_business_day).date()

            exit_orders.at[index, 'status'] = 'LIVE'
            continue

        filled_ind, *asdf = np.where(
            window_prices['High Price'] >= exit_order['price']
        )

        if filled_ind.size == 0:

            if window_prices.shape[0] < n2:
                exit_orders.at[index, 'date'] = pd.to_datetime(
                    next_business_day).date()

                exit_orders.at[index, 'status'] = 'LIVE'
                continue

            exit_orders.at[index, 'date'] = window_prices['Date'].iloc[
                window_prices.shape[0] - 1
                ]
            exit_orders.at[index, 'status'] = 'CANCELLED'
            exit_mkt_orders = pd.concat([
                exit_mkt_orders,
                pd.DataFrame({
                    'trade_id': exit_order['trade_id'],
                    'date': window_prices['Date'].tail(1),
                    'asset': exit_order['asset'],
                    'trip': exit_order['trip'],
                    'action': exit_order['action'],
                    'type': "MKT",
                    'price': window_prices['Close Price'].tail(1),
                    'status': 'FILLED'
                })
            ])
            continue

        exit_orders.at[index, 'date'] = window_prices['Date'].iloc[
            min(filled_ind)
        ]
        exit_orders.at[index, 'status'] = 'FILLED'

    all_orders = pd.concat(
        [entry_orders,
         submitted_exit_orders, exit_orders, exit_mkt_orders]
    ).sort_values(['trade_id', 'trip', 'date'])

    return all_orders
    #return entry_orders, exit_orders


def generateLedger(blotter):
    ledger = pd.DataFrame(columns=['trade_id', 'asset', 'dt_enter', 'dt_exit', 'success', 'n', 'rtn'])

    # TODO sort blotter by trade id
    blotter.sort_values(by='trade_id')

    # get min trade id and max trade id
    trade_id_min = blotter.iloc[0, 0]
    trade_id_max = blotter.iloc[-1, 0]

    # print("min trade id is: " + str(trade_id_min))
    # print("max trade id is: " + str(trade_id_max))

    # group data in blotter by trade id
    blotter_group = blotter.groupby('trade_id')

    # loop over the blotter from trade id 1 to max
    for idx in range(trade_id_min, trade_id_max + 1):
        current_group = blotter_group.get_group(idx)

        trade_id = current_group.iloc[0]['trade_id']  # also index
        asset = current_group.iloc[0]['asset']

        # get enter date
        # have enter date when enter order is submitted or live
        dt_enter_query = current_group.query('trip == "ENTER" & action == "BUY" & status == "SUBMITTED"')
        if dt_enter_query.empty:
            dt_enter_query = current_group.query('trip == "ENTER" & action == "BUY" & status == "LIVE"')
        if dt_enter_query.empty:
            dt_enter = ""
        else:
            dt_enter = dt_enter_query.iloc[0]['date']
        # print("enter date is: " + str(dt_enter))

        # get exit date
        dt_exit_query = current_group.query(
            'trip == "EXIT" & action == "SELL" & status == "FILLED"')  # regardless of market order or limit order
        if dt_exit_query.empty:
            dt_exit = ""
        else:
            dt_exit = dt_exit_query.iloc[0]['date']
        # print("exit date is: " + str(dt_exit))

        # get last open date
        if current_group.tail(1).iloc[-1]['status'] == "LIVE":
            last_day = ""
        else:
            last_day = current_group.tail(1).iloc[-1]['date']

        n = count_bdays(dt_enter, last_day)
        # print("business days between "+ dt_enter + "->" + last_day+ ": " +n)

        # generate success
        # success = 0 if entry order was submitted but cancelled
        success = ""
        if_enter_cancelled = current_group.query('trip == "ENTER" & action == "BUY" & status == "CANCELLED"')
        if_enter_filled = current_group.query('trip == "ENTER" & action == "BUY" & status == "FILLED"')
        if_limit_exit_cancelled = current_group.query(
            'trip == "EXIT" & action == "SELL" & type == "LMT" & status == "CANCELLED"')
        if_limit_exit_filled = current_group.query(
            'trip == "EXIT" & action == "SELL" & type == "LMT" & status == "FILLED"')
        if_order_live = current_group.query('status == "LIVE"')

        if if_order_live.empty:
            # success = 1 if entry order and exit order was filled
            if not if_enter_filled.empty and not if_limit_exit_filled.empty:
                success = "1"

            # success = -1 if entry order filled but exit order was cancelled ???
            elif not if_enter_filled.empty and not if_limit_exit_cancelled.empty:
                success = "-1"

            else:
                success = "0"

        # print("success is " + str(success))

        # generate n

        # put everything into data frame

        # generate rtn
        rtn_str = ""
        if dt_enter != "" and dt_exit != "":
            enter = current_group.query('trip == "ENTER" & action == "BUY" & status == "FILLED"')
            enter_price = enter.iloc[0]['price']
            exit = current_group.query('trip == "EXIT" & action == "SELL" & status == "FILLED"')
            exit_price = exit.iloc[0]['price']
            rtn = np.log(float(exit_price) / float(enter_price)) / int(n)
            rtn_str = '{:.3%}'.format(rtn)
        # print("rtn is: " + rtn_str)

        data = {"trade_id": trade_id, "asset": asset, "dt_enter": dt_enter, "dt_exit": dt_exit, "success": success,
                "n": n, "rtn": rtn_str}

        # ledger = ledger.append(data, ignore_index=True)
        ledger.loc[len(ledger)] = data
        # print(data)
        # print("=======================")
    # print(ledger)
    ledger.to_csv('ledger_queried.csv')
    return ledger


# count business days between two date
def count_bdays(dt_enter, last_day):
    if dt_enter != "" and last_day != "":
        return str(len(pd.bdate_range(dt_enter, last_day)))
    return ""
# return np.busday_count(date1, date2)