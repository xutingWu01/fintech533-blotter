import numpy as np
from sklearn.linear_model import Perceptron
from sklearn.preprocessing import StandardScaler
import pandas as pd
import math

# n3 is the lookback window size
def whole_percep(n3):
    ledger = pd.read_csv('ledger_queried.csv')
    features = pd.read_csv('hw4_data.csv')
    # features preprocessing
    # Dates,IVV US Equity,IVV AU Equity,ECRPUS 1Y Index,SPXSFRCS Index,FDTRFTRL Index,USCRWTIC Index,XAU Curncy,JPYUSD Curncy,DXY Curncy,VIX Index
    features.drop(["IVV AU Equity", "USCRWTIC Index", "JPYUSD Curncy", "VIX Index", "ECRPUS 1Y Index"], axis=1, inplace=True)
    features.drop(["DXY Curncy"], axis=1,
                  inplace=True)

    num_rows = len(ledger)
    ledger.insert(len(ledger.columns), "predict_success", "")
    for n in range(n3, num_rows):
        # print("deal with the row: " + str(n))
        date_str = ledger.iloc[n]["dt_enter"]
        pred_str = single_percep(date_str, n3, ledger, features)
        ledger.loc[n, 'predict_success'] = pred_str
    print(ledger)
    ledger.to_csv("predict_ledger_output.csv", index = False)
    return ledger

def single_percep(date_str, lookback_window, ledger, features):
    # the format of the date_str should be like "2021-05-8"
    # build your set of features here.
    # merge them by date to add to this dataframe.
    # ledger = pd.read_csv('ledger_queried.csv')
    # features = pd.read_csv('hw4_data.csv')
    # first tranfer the date to pandas date
    date = pd.to_datetime(date_str)
    # get the previous business date
    prev_date = date - pd.offsets.BDay()
    # find the correspondent row in ledger and feature(previous day)->for model training
    prev_date_str_ledger = prev_date.strftime("%Y-%m-%d")
    prev_date_str_feature = prev_date.strftime("%-m/%-d/%Y")
    row_ledger = ledger.loc[ledger['dt_enter'] == prev_date_str_ledger]
    row_feature = features.loc[features['Dates'] == prev_date_str_feature]
    # print("ledger->" + row_ledger['dt_enter'])
    # print("feature->" + row_feature['Dates'])
    if row_ledger.empty or row_feature.empty:
        # print("didn't find the matched record from data ")
        return ""

    if row_ledger.index[0] == len(ledger) - 1 or row_feature.index[0] == len(features) - 1:
        return ""
    # slice the ledger
    # start_index_l = row_ledger.index[0] - 49
    start_index_l = row_ledger.index[0] - (lookback_window - 1)
    if start_index_l < 0:
        print("not enough data to train the model!")
        return ""
    end_index_l = row_ledger.index[0] + 1
    slice_ledger = ledger.iloc[start_index_l:end_index_l]
    # slice the feature
    # start_index = row_feature.index[0] - 49
    start_index = row_feature.index[0] - (lookback_window - 1)
    if start_index < 0:
        print("not enough data to train the model!")
        return ""
    end_index = row_feature.index[0] + 1
    slice_features = features.iloc[start_index:end_index]
    # print("-----------------------")
    # print(slice_ledger)
    # print("-----------------------")
    # print(slice_features)
    # print("-----------------------")

    # do the training
    X = slice_features.drop(slice_features.columns[[0]], axis=1)
    x_test = features.drop(features.columns[[0]], axis=1).iloc[[end_index]]
    y = np.asarray(slice_ledger.success, dtype="|S6")
    # print(X)
    # print(x_test)
    # print(y)
    sc = StandardScaler()
    sc.fit(X)
    X_std = sc.transform(X)
    X_std = sc.transform(X)
    x_test_std = sc.transform(x_test)
    # print(X_std)

    # do the prediction
    ppn = Perceptron(eta0=0.1)
    try:
        ppn.fit(X_std, y)
    except ValueError:
        # print("fitting n:")
        # print(X_std)
        # print(y)
        return ""

    y_pred = ppn.predict(x_test_std)

    # show results
    # print("Predict trade status for the date: " + date_str + " -> " + str(y_pred))
    # print("Actual trade status for the date: " + date_str + " -> " + str(ledger.iloc[end_index_l].success))
    # print(float(str(y_pred)[3:-2]))
    return str(y_pred)[3:-2]

# a is the upper bound of alpha, which is the input from user
# b is the stop gap, we exit the trade no matter what if it's down by 10%
def hoeffding_cal(n, alpha_dumb, alpha_smart, a, b = -0.1):
    t = float(alpha_dumb) - float(alpha_smart)
    result1 = (float(b) - float(a)) ** 2
    result2 = math.exp(-2 * float(n) * (t ** 2) / result1)
    return str(result2)

# if __name__ == '__main__':
#     whole_percep(5)