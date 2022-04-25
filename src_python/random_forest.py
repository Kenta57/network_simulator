import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import confusion_matrix
from pathlib import Path
import glob
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import plot
from astropy.timeseries import LombScargle
import pprint
from utils import spot_list

from sklearn.model_selection import train_test_split#データ分割用
from sklearn.ensemble import RandomForestClassifier#ランダムフォレスト

pd.set_option('display.max_rows', 150)
# pd.set_option('display.max_columns', 30)
ROOT = Path.cwd().parent

def pre_process(save_path, category, peak_num,index):
    base_path = ROOT / 'data'
    name_list = [Path(p).name for p in glob.glob(str(base_path/f'*{category}*'))]
    NG_list = ['UDP', '00']
    name_list = spot_list(name_list, category, NG_list)
    # Link_Errorの削除
    # name_list = [name for name in name_list if (('Link' not in name) or ('001' in name))]
    # delete_category = '00'
    # name_list = [name for name in name_list if delete_category not in name]
    # delete_category = 'UDP'
    # name_list = [name for name in name_list if delete_category not in name]


    name_list.sort()

    label = [name[0] for name in name_list]

    # X_train, X_test, _, _ = train_test_split(name_list,label, stratify = label, test_size=0.3, random_state=1234)
    X_train, X_test, _, _ = train_test_split(name_list,label, stratify = label, test_size=0.3)
    
    # train_path_list = [base_path/name/f'{name}-flw{i}-rtt.data' for name in X_train for i in range(3)]
    # test_path_list = [base_path/name/f'{name}-flw{i}-rtt.data' for name in X_test for i in range(3)]
    train_path_list = [base_path/name/f'{name}-flw{i}-rtt_estimate.data' for name in X_train for i in range(3)]
    test_path_list = [base_path/name/f'{name}-flw{i}-rtt_estimate.data' for name in X_test for i in range(3)]


    # train用のデータ生成
    X_train, y_train, _ = make_X_y(train_path_list, peak_num)

    # # test用のデータ生成
    X_test, y_test, add_feature = make_X_y(test_path_list, peak_num)
    test_name_list = [p.stem for p in test_path_list]

    clf = RandomForestClassifier(random_state=1234)
    clf.fit(X_train, y_train)

    test = pd.DataFrame(data=X_test)
    test['name'] = test_name_list
    test['label'] = y_test
    test['pred'] = clf.predict(X_test)
    test = test.sort_values('name')

    n = test.shape[1]
    row_label = []
    for i in range(peak_num):
        row_label.append(f'amplitude_{i+1}')
        row_label.append(f'frequency_{i+1}')
    row_label += add_feature
    test.columns = row_label + test.columns[int(len(row_label)):].to_list() 

    file_name = f'{save_path.name}'
    
    test.to_csv(str(save_path / f'{file_name}_{index}.csv'))
    print(test)

    score = clf.score(X_test, y_test)
    print("score=", score)

    fti = clf.feature_importances_   

    print('Feature Importances:')
    for i, feat in enumerate(row_label):
        print('{0:20s},{1:>.6f}'.format(feat, fti[i]))
    # print(fti)

    return score

def make_X_y(path_list, peak_num):
    base_path = ROOT / 'data'
    name_list = [p.stem for p in path_list]
    dup_list = [base_path/name[:-9]/f'{name[:-9]}-DUP_ACK_num.data' for name in name_list]
    flight_list = [base_path/name[:-9]/f'{name[:-9]}-sack-True-flw{i}-inflight.data' for name in name_list for i in range(3)]
    data = []

    add_feature = [
        # 'DUP', 
        # 'Byte'
        ]

    i = 0
    for p,dup_p,f_p in zip(path_list,dup_list, flight_list):
        l = Lomb_Scargle(str(p),peak_num)
        if 'DUP' in add_feature:
            l += [DUP_ACK(dup_p,i)]
        if 'Byte' in add_feature:
            l += [byte_in_flight(str(f_p))]
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
    return X,y, add_feature

def Lomb_Scargle(path, num,save_dir=None):
    data = plot.read_data(str(path), 30)
    t = data['sec'].to_list()
    rtt = data['value'].to_list()
    n = len(t)
    # frequency, power = LombScargle(t[int(n/6):],rtt[int(n/6):]).autopower(maximum_frequency=5.0)
    frequency, power = LombScargle(t,rtt).autopower(maximum_frequency=5.0)
    l = []
    # num = 2
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
    # return int(l[stream_idx])
    return sum

def byte_in_flight(path):
    duration = 30
    data = plot.read_data(str(path), duration)
    return data['value'].max()

def ave_score(n=10):
    save_dir = ROOT / 'evaluation_middle'
    save_dir.mkdir(exist_ok=True)

    category = 'range50'
    n_label = 3 # クラス分類の個数
    dir_name = f'peak_label_{n_label}_{category}'
    save_dir = save_dir / dir_name
    save_dir.mkdir(exist_ok=True)

    for peak_num in range(1,4):
        prefix_name = f'peak_{peak_num}_label_{n_label}_{category}'
        save_path = save_dir / prefix_name
        save_path.mkdir(exist_ok=True)

        file_name = f'{prefix_name}_{category}'

        f = open(str(save_path/f'{file_name}.txt'),mode='w')

        score = []
        sum = 0
        for i in range(n):
            score.append(pre_process(save_path,category,peak_num,i))
            sum += score[i]
            print(f'accuracy{i} : {score[i]}')
            f.write(f'accuracy{i} : {score[i]}\n')
        print(f'average_accuracy : {sum/n}')
        f.write(f'average_accuracy : {sum/n}\n')
        f.close()

def plot_acuuracy(name):
    base_path = ROOT / 'evaluation'
    target_path = base_path / name
    path_list = [Path(p) for p in glob.glob(str(target_path/'*'/'*.txt'))]
    path_list.sort()
    # print(path_list)
    scores = []
    for p in path_list:
        with open(str(p)) as f:
            l = f.readlines()
            score = l[-1].split()[2]
            scores.append(float(score))

    x = list(range(1, len(scores)+1))
    plt.title(name)
    plt.legend(name)
    plt.xlabel('peak_num')
    plt.ylabel('average_accuracy')
    plt.plot(x[:5], scores[:5])
    plt.savefig(str(target_path / (target_path.stem+'.png')))
    # plt.clf()

def plot_acuuracy_stack(name_list):
    base_path = ROOT / 'evaluation'
    scores_list = []
    for name in name_list:
        target_path = base_path / name
        path_list = [Path(p) for p in glob.glob(str(target_path/'*'/'*.txt'))]
        path_list.sort()
        # print(path_list)
        scores = []
        for p in path_list:
            with open(str(p)) as f:
                l = f.readlines()
                score = l[-1].split()[2]
                scores.append(float(score))
        scores_list.append(scores)

    fig, ax = plt.subplots()
    ax.set_xlabel('peak_num')  # x軸ラベル
    ax.set_ylabel('mean_accuracy')  # y軸ラベル
    # ax.set_title(r'$\sin(x)$ and $\cos(x)$') # グラフタイトル

    label_name = ['range10', 'range50', 'range100']
    # label_name = ['rate=0.001', 'rate=0.0025', 'rate=0.005', 'rate=0.01']
    for s, name in zip(scores_list, label_name):
        x = list(range(1,len(s)+1))
        ax.plot(x[:5],s[:5], label=name)

    ax.legend()
    # x = list(range(1, len(scores)+1))
    # plt.title(name)
    # plt.legend(name)
    # plt.xlabel('peak_num')
    # plt.ylabel('average_accuracy')
    # plt.plot(x[:5], scores[:5])
    # plt.savefig(str(target_path / (target_path.stem+'.png')))
    plt.savefig('delay.png')

def show_confusion_matrix(target_path):
    path_list = [Path(p) for p in glob.glob(str(target_path/'*.csv'))]
    label = []
    pred = []
    for p in path_list:
        df = pd.read_csv(p)
        label += df['label'].to_list()
        pred += df['pred'].to_list()

    labels = ['N','T','L']
    c_matrix = confusion_matrix(label, pred,labels=labels)
    columns_labels = ["pred_" + str(l) for l in labels]
    index_labels = ["act_" + str(l) for l in labels]
    cm = pd.DataFrame(c_matrix,columns=columns_labels, index=index_labels)

    print(cm)
    return cm
    


if __name__ == '__main__':
    ave_score()
    # pre_process()

    # base_path = ROOT / 'evaluation'
    # name_list = ['peak_label_3_range10_0001', 'peak_label_3_range50', 'peak_label_3_range100']
    # name_list.sort()
    # print(name_list)
    # plot_acuuracy_stack(name_list)

    # name_list.sort()
    # print(name_list)
    # for name in name_list:
    #     plot_acuuracy(name)

    # target_path = ROOT / 'evaluation/peak_label_3_range100/peak_3_label_3_range100'
    # show_confusion_matrix(target_path).to_csv('test.csv')

    # category = 'range50'
    # base_path = ROOT / 'data'
    # name_list = [Path(p).name for p in glob.glob(str(base_path/f'*{category}*'))]
    # NG_list = ['UDP', '00']
    # name_list = spot_list(name_list, category, NG_list)
    # name_list.sort()
    # pprint.pprint(name_list)
