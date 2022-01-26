import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from pathlib import Path
import glob
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import plot
from astropy.timeseries import LombScargle


ROOT = Path.cwd().parent

def pre_process():
    base_path = ROOT / 'result' / 'test'
    l = glob.glob(str(base_path/'*.npy'))
    path_list = [Path(p) for p in l]
    path_list.sort()
    # path_list = path_list[18:]
    p_l = path_list
    p_l = []
    for p in path_list:
        if not ('range50' in str(p)):
        # if 'range50' in str(p):
            p_l.append(p)

    base_path = ROOT / 'result'

    l = [
        # 'error_0001_2_range10',
        # 'error_0001_2_range50',
        # 'error_0001_3_range10',
        # 'error_0001_3_range50',
        # 'error_0001_4_range10',
        # 'error_0001_4_range50',
        'gw_30_normal_2_range10',
        'gw_30_normal_2_range50',
        'gw_30_normal_3_range10',
        'gw_30_normal_3_range50',
        'gw_30_normal_4_range10',
        'gw_30_normal_4_range50',
        # 'normal_2',
        # 'normal_2_range50',
        # 'normal_3',
        # 'normal_3_range50',
        # 'normal_4',
        # 'normal_4_range50',
        'TCP_Congestion_2_range10',
        'TCP_Congestion_2_range50',
        'TCP_Congestion_3_range10',
        'TCP_Congestion_3_range50',
        'TCP_Congestion_4_range10',
        'TCP_Congestion_4_range50',
        'udp_2_range10',
        'udp_2_range50',
        'udp_3_range10',
        'udp_3_range50',
        'udp_4_range10',
        'udp_4_range50'
    ]

    category = 'range10'
    name_list = []
    for name in l:
        if category in name:
            name_list.append(name)

    p_l = [base_path/name/f'{name}-flw{i}-rtt.data' for name in name_list for i in range(3)]

    name = [p.stem for p in p_l]
    print(name)


    data = []

    # for p in p_l:
    #     l = high_frq(p,r=20)
    #     data.append(l)

    for p in p_l:
        l = Lomb_Scargle(str(p))
        data.append(l)
    
    
    data = np.array(data)
    df = pd.DataFrame(data=data)
    # name = [name[3*i] for i in range(len(name)//3)]
    df['name'] = name
    pred = KMeans(n_clusters=3).fit_predict(data)
    df['pred'] = pred
    df = df.rename(columns={0: 'amplitude'})
    df = df.rename(columns={1: 'frequency'})
    print(df)

def high_frq(path, r=20):
    data = np.load(str(path))
    size_frame = len(data)
    hamming_window = np.hamming(size_frame)
    fft_spec = np.fft.rfft(data * hamming_window)
    ans = np.abs(fft_spec)
    ans = ans[2:]

    # 区間ごとの最大値をとってくる
    # n = len(ans)
    # l = []
    # for i in range(3):
    #     l.append(np.max(ans[i:i+r]))


    l = []
    num = 1
    peaks,_ = find_peaks(ans,prominence=0.1)
    peaks = peaks[np.argsort(ans[peaks])[::-1][:num]]
    for i in range(num):
        l.append(ans[peaks[i]])
        l.append(peaks[i])



    return l

def Lomb_Scargle(path, save_dir=None):
    data = plot.read_data(str(path), 30)
    t = data['sec'].to_list()
    rtt = data['value'].to_list()
    frequency, power = LombScargle(t,rtt).autopower(maximum_frequency=5.0)
    l = []
    num = 2
    # peaks,_ = find_peaks(power,prominence=0.1)
    peaks,_ = find_peaks(power)
    peaks = peaks[np.argsort(power[peaks])[::-1][:num]]
    if len(peaks) != 0:
        for i in range(num):
            l.append(power[peaks[i]])
            l.append(frequency[peaks[i]])
        # plt.scatter(frequency[peaks], power[peaks], color='red')

    # plt.plot(frequency, power)
    # plt.savefig(str(save_dir / f'{path.stem}.png'))
    # plt.clf()
    return l

def check():
    base_path = ROOT / 'result'
    save_dir = base_path / 'LS'
    save_dir.mkdir(exist_ok=True)
    path_list = glob.glob(str(base_path / '*range50*'))
    path_list = [Path(p) for p in path_list]
    print(path_list)
    for p in path_list:
        name = p.stem
        target_path = p / f'{name}-flw0-rtt.data'
        Lomb_Scargle(target_path, save_dir)



if __name__ == '__main__':
    pre_process()
    # check()