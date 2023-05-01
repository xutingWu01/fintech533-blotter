import numpy as np
from sklearn.linear_model import Perceptron
from sklearn.preprocessing import StandardScaler
import pandas as pd

def percep(date_str = "2021-05-8"):
    # build your set of features here.
    # merge them by date to add to this dataframe.
    ledger = pd.read_csv('ledger_queried.csv')
    features = pd.read_csv('hw4_data.csv')
    # first tranfer the date to pandas date
    date = pd.to_datetime(date_str)
    # get the previous business date
    prev_date = date - pd.offsets.BDay()
    # find the correspondent row in ledger and feature(previous day)->for model training
    prev_date_str_ledger = prev_date.strftime("%Y-%m-%d")
    prev_date_str_feature = prev_date.strftime("%-m/%-d/%Y")
    row_ledger = ledger.loc[ledger['dt_enter'] == prev_date_str_ledger]
    row_feature = features.loc[features['Dates'] == prev_date_str_feature]

    if row_ledger.empty or row_feature.empty:
        print("didn't find the matched record from data ")
        predict_data = [[date_str, "Cannot Predict"]]
        actual_data = [[date_str, "Cannot Find Actual Data"]]
        predict_df = pd.DataFrame(predict_data, columns=['Date', 'Success'])
        actual_df = pd.DataFrame(actual_data, columns=['Date', 'Success'])
        return predict_df, actual_df

    # slice the ledger
    start_index_l = row_ledger.index[0] - 49
    if start_index_l < 0:
        print("not enough data to train the model!")
    end_index_l = row_ledger.index[0] + 1
    slice_ledger = ledger.iloc[start_index_l:end_index_l]
    # slice the feature
    start_index = row_feature.index[0] - 49
    if start_index < 0:
        print("not enough data to train the model!")
    end_index = row_feature.index[0] + 1
    slice_features = features.iloc[start_index:end_index]
    print("-----------------------")
    print(slice_ledger)
    print("-----------------------")
    print(slice_features)
    print("-----------------------")

    # do the training
    X = slice_features.drop(slice_features.columns[[0]], axis=1)
    x_test = features.drop(features.columns[[0]], axis=1).iloc[[end_index]]
    y = np.asarray(slice_ledger.success, dtype="|S6")
    print(X)
    print(x_test)
    print(y)
    sc = StandardScaler()
    sc.fit(X)
    X_std = sc.transform(X)
    X_std = sc.transform(X)
    x_test_std = sc.transform(x_test)
    print(X_std)

    # do the prediction
    ppn = Perceptron(eta0=0.1)
    ppn.fit(X_std, y)
    y_pred = ppn.predict(x_test_std)

    # show results
    print("Predict trade status for the date: " + date_str + " -> " + y_pred[0].decode('utf-8'))
    print("Actual trade status for the date: " + date_str + " -> " + str(ledger.iloc[end_index_l].success))


    # generate return result
    predict_data = [[date_str, y_pred[0].decode('utf-8')]]
    actual_data = [[date_str, str(ledger.iloc[end_index_l].success)]]
    predict_df = pd.DataFrame(predict_data, columns=['Date', 'Success'])
    actual_df = pd.DataFrame(actual_data, columns=['Date', 'Success'])
    print("return result: ")
    print(predict_df)
    return predict_df, actual_df



if __name__ == '__main__':
    percep()