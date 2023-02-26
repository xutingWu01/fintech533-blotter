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
def generateOrders(alpha1, n1, alpha2, n2, ivv_prc):
    next_business_day = get_next_business_day(ivv_prc)
    # submitted entry orders
    submitted_entry_orders = pd.DataFrame({
        "trade_id": range(1, ivv_prc.shape[0]),
        "date": list(pd.to_datetime(ivv_prc["Date"].iloc[1:]).dt.date),
        "asset": "IVV",
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
    print(cancelled_entry_orders)

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
        "asset": "IVV",
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

    print("submitted_entry_orders:")
    print(submitted_entry_orders)

    print("cancelled_entry_orders:")
    print(cancelled_entry_orders)

    print("filled_entry_orders:")
    print(filled_entry_orders)

    print("live_entry_orders:")
    print(live_entry_orders)

    print("entry_orders:")
    print(entry_orders)



    print("---------------------------------------------------")
    # for exit orders
    ##Parameters:
    # alpha2 = 0.01
    # n2 = 5

    ##get inital submitted exit orders:
    submitted_exit_orders = filled_entry_orders.copy()
    print("submitted_exit_orders:")
    print(submitted_exit_orders)
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    submitted_exit_orders.reset_index(drop=True, inplace=True)
    ##update the attribute
    submitted_exit_orders["trip"] = "EXIT"
    submitted_exit_orders["action"] = "SELL"
    submitted_exit_orders["status"] = "SUBMITTED"
    ##update price
    submitted_exit_orders["price"] = round(submitted_exit_orders["price"]*(1 + alpha2), 2)
    print(submitted_exit_orders)
    print(ivv_prc)
    print("---------------------------------------------------------------------")
    ##get all closed  orders，如果可以fill则fill，如果不能fill并且不够n2天则live
    print(submitted_exit_orders)
    exit_orders = submitted_exit_orders.copy()
    for i in range(0, len(submitted_exit_orders)):
        idx1 = np.flatnonzero(
            ivv_prc['Date'] == submitted_exit_orders['date'].iloc[i]
        )[0]

        # 先跟当天的close price比，如果满足直接FILLED
        if ivv_prc.iloc[idx1]["Close Price"] >= submitted_exit_orders['price'].iloc[i]:
            exit_orders.at[i, 'status'] = 'FILLED'
            continue

        ivv_slic = ivv_prc.iloc[idx1+1:idx1+n2]['High Price']

        # # test slice
        # test_slic = ivv_prc.iloc[idx1:idx1+n2]['Date']
        # print("my date is:")
        # print(submitted_exit_orders['date'].iloc[i])
        # print("compare to date:")
        # print(test_slic)

        fill_inds = ivv_slic >= submitted_exit_orders['price'].iloc[i]
        # 如果不能fill并且不够n2天则live，修改status
        # update: 因为状态是live，修改时间为最新时间
        if(len(fill_inds) < n2) & (not any(fill_inds)):
            exit_orders.at[i, 'status'] = 'LIVE'
            exit_orders.at[i, 'date'] = ivv_prc.iloc[-1]['Date']
        # 如果可以fill则fill，修改price为卖出的price(update:不修改)，date为卖出的日期，status为FILLED
        elif any(fill_inds):
            # idxt = fill_inds.idxmax()
            idxt = fill_inds.idxmax()
            exit_orders.at[i, 'date'] = ivv_prc['Date'].iloc[idxt]
            # exit_orders.at[i, 'price'] = ivv_prc['High Price'].iloc[idxt]
            exit_orders.at[i, 'status'] = 'FILLED'
        # 如果不能fill，修改price为close date的price，date为close date，status为CLOSED
        else:
            idxt = idx1+n2-1
            exit_orders.at[i, 'date'] = ivv_prc['Date'].iloc[idxt]
            exit_orders.at[i, 'price'] = ivv_prc['Close Price'].iloc[idxt]
            exit_orders.at[i, 'status'] = 'CLOSED'
    # 合并submitted和live&filled
    exit_orders = pd.concat(
        [
            submitted_exit_orders,
            exit_orders
        ]
    ).sort_values(['trade_id', "date"])
    print("final result----------")
    print(exit_orders)


    return entry_orders, exit_orders