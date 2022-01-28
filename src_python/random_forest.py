import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from pathlib import Path
import glob
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import plot
from astropy.timeseries import LombScargle
import pprint

from sklearn.model_selection import train_test_split#データ分割用
from sklearn.ensemble import RandomForestClassifier#ランダムフォレスト

pd.set_option('display.max_rows', 150)
# pd.set_option('display.max_columns', 30)
ROOT = Path.cwd().parent

def pre_process():
    base_path = ROOT / 'data'
    category = 'range50'
    name_list = [Path(p).name for p in glob.glob(str(base_path/f'*{category}*'))]
    # delete_category = 'Link'
    # name_list = [name for name in name_list if delete_category not in name]
    # delete_category = 'Normal'
    # name_list = [name for name in name_list if delete_category not in name]

    name_list.sort()

    label = [name[0] for name in name_list]

    # X_train, X_test, _, _ = train_test_split(name_list,label, stratify = label, test_size=0.3, random_state=1234)
    X_train, X_test, _, _ = train_test_split(name_list,label, stratify = label, test_size=0.3)
    
    train_path_list = [base_path/name/f'{name}-flw{i}-rtt.data' for name in X_train for i in range(3)]
    test_path_list = [base_path/name/f'{name}-flw{i}-rtt.data' for name in X_test for i in range(3)]

    # train用のデータ生成
    X_train, y_train = make_X_y(train_path_list)

    # # test用のデータ生成
    X_test, y_test = make_X_y(test_path_list)
    test_name_list = [p.stem for p in test_path_list]

    clf = RandomForestClassifier(random_state=1234)
    clf.fit(X_train, y_train)

    test = pd.DataFrame(data=X_test)
    test['name'] = test_name_list
    test['label'] = y_test
    test['pred'] = clf.predict(X_test)
    test = test.sort_values('name')
    print(test)

    print("score=", clf.score(X_test, y_test))
    # df = df.rename(columns={0: 'amplitude_1'})
    # df = df.rename(columns={1: 'frequency_1'})
    # df = df.rename(columns={2: 'amplitude_2'})
    # df = df.rename(columns={3: 'frequency_2'})
    # print(df)

def make_X_y(path_list):
    base_path = ROOT / 'data'
    name_list = [p.stem for p in path_list]
    dup_list = [base_path/name[:-9]/f'{name[:-9]}-DUP_ACK_num.data' for name in name_list]
    flight_list = [base_path/name[:-9]/f'{name[:-9]}-sack-True-flw{i}-inflight.data' for name in name_list for i in range(3)]
    data = []

    i = 0
    for p,dup_p,f_p in zip(path_list,dup_list, flight_list):
        l = Lomb_Scargle(str(p))
        l += [byte_in_flight(str(f_p))]
        l += [DUP_ACK(dup_p,i)]
        i += 1
        i %= 3
        data.append(l)

    data = np.array(data)
    df = pd.DataFrame(data=data)
    df['name'] = name_list
    label = [name[0] for name in df['name']]
    df['label'] = label
    # df['label'] = ['T' if w=='U' else w for w in label]
    df = df.drop(["name"], axis=1)

    data = df.drop("label", axis=1)
    y = df["label"].values
    X = data.values
    return X,y

def Lomb_Scargle(path, save_dir=None):
    data = plot.read_data(str(path), 30)
    t = data['sec'].to_list()
    rtt = data['value'].to_list()
    n = len(t)
    # frequency, power = LombScargle(t[int(n/6):],rtt[int(n/6):]).autopower(maximum_frequency=5.0)
    frequency, power = LombScargle(t,rtt).autopower(maximum_frequency=5.0)
    l = []
    num = 3
    # peaks,_ = find_peaks(power,prominence=0.1)
    peaks,_ = find_peaks(power)
    peaks = peaks[np.argsort(power[peaks])[::-1][:num]]
    if len(peaks) != 0:
        for i in range(num):
            l.append(power[peaks[i]])
            l.append(frequency[peaks[i]])

    return l

def DUP_ACK(path, stream_idx):
    with open(str(path)) as f:
        l_strip = [s.strip() for s in f.readlines()]
        l = [elm.split()[1] for elm in l_strip]
    sum = 0
    for i in range(3):
        sum += int(l[i])
    # return [int(l[stream_idx])]
    return sum

def byte_in_flight(path):
    duration = 30
    data = plot.read_data(str(path), duration)
    return data['value'].max()


if __name__ == '__main__':
    pre_process()
    # check()