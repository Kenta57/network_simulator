import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from pathlib import Path
import glob
from scipy.signal import find_peaks


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
        # if not ('range50' in str(p)):
        if 'range50' in str(p):
            p_l.append(p)
        

    name = [p.stem for p in p_l]
    print(name)


    data = []

    # for p in p_l:
    #     l = high_frq(p,r=20)
    #     data.append(l)

    i = 0
    for p in p_l:
        if i == 0:
            l = high_frq(p,r=20)
            i += 1
        elif i == 1:
            l += high_frq(p,r=20)
            i += 1
        else:
            l += high_frq(p,r=20)
            data.append(l)
            i = 0
    
    
    data = np.array(data)
    df = pd.DataFrame(data=data)
    name = [name[3*i] for i in range(len(name)//3)]
    df['name'] = name
    pred = KMeans(n_clusters=4).fit_predict(data)
    df['pred'] = pred
    df = df.rename(columns={0: 'amplitude_flow0'})
    df = df.rename(columns={1: 'frequency_flow0'})
    df = df.rename(columns={2: 'amplitude_flow1'})
    df = df.rename(columns={3: 'frequency_flow1'})
    df = df.rename(columns={4: 'amplitude_flow2'})
    df = df.rename(columns={5: 'frequency_flow2'})
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



if __name__ == '__main__':
    pre_process()