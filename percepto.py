import numpy as np
from sklearn.linear_model import Perceptron
from sklearn.preprocessing import StandardScaler
import pandas as pd

def percep():
    ledger = pd.read_csv('ledger_queried.csv')
    # build your set of features here.
    # merge them by date to add to this dataframe.
    features = pd.read_csv('hw4_data.csv')
    print(features)

    # Make a training set and let's try it out on two upcoming trades.
    # Choose a subset of data:

    # df = df.drop(columns=['column_nameA', 'column_nameB'])
    # df = df.drop(df.columns[[0, 1, 3]], axis=1)  # df.columns is zero-based pd.Index

    # X = features.drop('Date', axis=1).head(50)
    X = features.drop(features.columns[[0]], axis=1)[266:316]
    # x_test = features.drop('Date', axis=1).iloc[[51, 52]]
    x_test = features.drop(features.columns[[0]], axis=1).iloc[[317, 318]]
    y = np.asarray(ledger.success.head(50), dtype="|S6")

    print(X)
    print(x_test)
    print(y)
    sc = StandardScaler()

    sc.fit(X)
    X_std = sc.transform(X)
    X_std = sc.transform(X)
    x_test_std = sc.transform(x_test)

    print(X_std)
    ppn = Perceptron(eta0=0.1)
    ppn.fit(X_std, y)

    y_pred = ppn.predict(x_test_std)
    print(y_pred)
    print(ledger.iloc[[51, 52]])