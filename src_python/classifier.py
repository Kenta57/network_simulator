import pandas as pd
import numpy as np
from pyrsistent import m
from sklearn.cluster import KMeans
from pathlib import Path
import glob
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import plot
from astropy.timeseries import LombScargle
import pprint
import utils

pd.set_option('display.max_rows', 150)
ROOT = Path.cwd().parent

def pre_process():
    base_path = ROOT / 'data'
    category = 'range10'
    name_list = [Path(p).name for p in glob.glob(str(base_path/f'*{category}*'))]
    name_list.sort()

    path_list = [base_path/name/f'{name}-flw{i}-rtt.data' for name in name_list for i in range(3)]

    name = [p.stem for p in path_list]

    data = []
    
    i = 0
    # for p, p_dup in zip(p_l, DUP_l):
    for p in path_list:
        l = Lomb_Scargle(str(p))
        # l += DUP_ACK(str(p_dup), i)
        i += 1
        i %= 3
        data.append(l)
    
    
    data = np.array(data)
    df = pd.DataFrame(data=data)
    # name = [name[3*i] for i in range(len(name)//3)]
    df['name'] = name
    pred = KMeans(n_clusters=4).fit_predict(data)
    df['pred'] = pred
    df = df.rename(columns={0: 'amplitude_1'})
    df = df.rename(columns={1: 'frequency_1'})
    df = df.rename(columns={2: 'amplitude_2'})
    df = df.rename(columns={3: 'frequency_2'})
    print(df)

# def high_frq(path, r=20):
#     data = np.load(str(path))
#     size_frame = len(data)
#     hamming_window = np.hamming(size_frame)
#     fft_spec = np.fft.rfft(data * hamming_window)
#     ans = np.abs(fft_spec)
#     ans = ans[2:]

#     # 区間ごとの最大値をとってくる
#     # n = len(ans)
#     # l = []
#     # for i in range(3):
#     #     l.append(np.max(ans[i:i+r]))


#     l = []
#     num = 1
#     peaks,_ = find_peaks(ans,prominence=0.1)
#     peaks = peaks[np.argsort(ans[peaks])[::-1][:num]]
#     for i in range(num):
#         l.append(ans[peaks[i]])
#         l.append(peaks[i])



#     return l

def Lomb_Scargle(path, save_dir=None, para='RTT'):
    data = plot.read_data(str(path), 30)
    t = data['sec'].to_list()
    rtt = data['value'].to_list()

    # plt.title(str(path.parent.name)[:-10])
    # plt.title(str(path.parent.name)[:-7])
    plt.xlabel('time[s]')
    plt.ylabel(f'{para}[s]')
    plt.subplots_adjust(left=0.15, bottom=0.15)
    plt.plot(t, rtt)

    save_dir = save_dir / path.stem
    save_dir.mkdir(exist_ok=True)
    print('***************************:')
    print(str(save_dir / f'{para}_{path.stem}.png'))
    plt.savefig(str(save_dir / f'{para}_{path.stem}.png'))
    plt.clf()

    n = len(t)


    # frequency, power = LombScargle(t[int(n/6):],rtt[int(n/6):]).autopower(maximum_frequency=5.0)
    frequency, power = LombScargle(t,rtt).autopower(maximum_frequency=5.0)
    pprint.pprint(f'****************************** {len(t)} ********')
    pprint.pprint(f'****************************** {len(power)} ********')
    l = []
    num = 3
    # peaks,_ = find_peaks(power,prominence=0.1)
    peaks,_ = find_peaks(power)
    peaks = peaks[np.argsort(power[peaks])[::-1][:num]]
    if len(peaks) != 0:
        for i in range(num):
            l.append(power[peaks[i]])
            l.append(frequency[peaks[i]])
        plt.scatter(frequency[peaks], power[peaks], color='red')

    # plt.title(str(path.parent.name)[:-10])
    # plt.title(str(path.parent.name)[:-7])
    plt.xlabel('frequency[Hz]')
    plt.ylabel('amplitude[s]')
    plt.subplots_adjust(left=0.15, bottom=0.15)
    plt.grid(color='b', linestyle=':', linewidth=0.4)
    plt.plot(frequency[:int(len(frequency)*1.5/5)], power[:int(len(frequency)*1.5/5)])

    plt.savefig(str(save_dir / f'Lomb_{path.stem}.png'))
    plt.clf()
    return l

def DUP_ACK(path, stream_idx):
    with open(str(path)) as f:
        l_strip = [s.strip() for s in f.readlines()]
        l = [elm.split()[1] for elm in l_strip]
    sum = 0
    for i in range(3):
        sum += int(l[i])
    # return [int(l[stream_idx])]
    return [sum]

def check():
    base_path = ROOT / 'data'
    # save_dir = base_path / 'LS'
    # save_dir = base_path / 'LS_data'
    save_dir = base_path / 'presentation'
    save_dir.mkdir(exist_ok=True)
    path_list = glob.glob(str(base_path/'*'))
    name_list = [Path(p).name for p in path_list]
    category = 'test'
    # category = 'Normal'
    # NG_list = ['Link','TCP']
    NG_list = []
    name_list = utils.spot_list(name_list, category, NG_list)
    path_list = [base_path / name for name in name_list]
    path_list.sort()
    pprint.pprint(path_list)

    # return 
    for p in path_list:
        name = p.stem
        # target_path = p / f'{name}-flw0-rtt.data'
        para = 'RTT'
        target_path_list = [p / f'{name}-flw{i}-rtt_estimate.data' for i in range(3)]
        # target_path_list = [p / f'{name}-flw{i}-{para}.data' for i in range(3)]
        for target_path in target_path_list:
            Lomb_Scargle(target_path, save_dir)



if __name__ == '__main__':
    # pre_process()
    check()