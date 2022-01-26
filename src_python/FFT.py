import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from tqdm import tqdm
from scipy.signal import find_peaks
from astropy.timeseries import LombScargle
import glob

import plot

ROOT = Path.cwd().parent

def main(path,save_dir):
    duration = 30
    # size_frame = 4096 * 2 # フレームサイズ
    SR = 400		# サンプリングレート
    # size_shift = 16000 / 100 # シフトサイズ = 0.001 秒 (10 msec)
    rate = 1/SR
    # ハミング窓
    time = np.arange(0,duration,rate)

    data = plot.read_data(str(path), duration)
    size_frame = len(time)
    hamming_window = np.hamming(size_frame)
    pre_value = 0
    x = []

    for t in time:
        pre_value = func(data,t,rate,pre_value)
        x.append(pre_value)



    x = np.array(x)

    fft_spec = np.fft.rfft(x * hamming_window)

    ans = np.abs(fft_spec)

    save_path = ROOT / 'result' / save_dir
    save_path.mkdir(exist_ok=True)

    np.save(str(save_path / (path.stem+'.npy')), x)

    plt.plot(ans[2:100])
    plt.savefig(str(save_path / (path.stem+'.png')))
    plt.clf()

def sampling(target_name, save_dir_name):
    duration = 30
    # size_frame = 4096 * 2 # フレームサイズ
    SR = 400		# サンプリングレート
    # size_shift = 16000 / 100 # シフトサイズ = 0.001 秒 (10 msec)
    # x, _ = librosa.load(f'./audio/{filename}', sr=self.SR)
    rate = 1/SR
    # ハミング窓
    time = np.arange(0,duration,rate)

    base_path = ROOT / 'result' / target_name
    path_list = [base_path / (target_name+f'-flw{i}-rtt.data') for i in range(3)]

    for p in tqdm(path_list):
        data = plot.read_data(str(p), duration)
        size_frame = len(time)
        hamming_window = np.hamming(size_frame)
        pre_value = 0
        x = []

        for t in tqdm(time):
            pre_value = func(data,t,rate,pre_value)
            x.append(pre_value)

        x = np.array(x)

        save_path = ROOT / 'result' / save_dir_name
        save_path.mkdir(exist_ok=True)

        np.save(str(save_path / (p.stem+'.npy')), x)

def plot_stack(target_name, save_dir_name):
    base_path = ROOT / 'result' / save_dir_name
    path_list = [base_path / (target_name+f'-flw{i}-rtt.npy') for i in range(3)]

    for p in path_list:
        x = np.load(p)
        size_frame = len(x)
        hamming_window = np.hamming(size_frame)
        fft_spec = np.fft.rfft(x * hamming_window)
        ans = np.abs(fft_spec)
        # ans = np.log(np.abs(fft_spec))
        plt.plot(ans[2:100],label=p.stem)
        plt.legend()

    plt.savefig(str(base_path / f'{target_name}.png'))
    plt.clf()

def compare_group(target_name, condition, save_dir_name):
    base_path = ROOT / 'result' / save_dir_name
    path_list = [base_path / (target_name + f'_{i}' + condition) for i in range(2,5,1)]

    for p in path_list:
        x = np.load(p)
        n = len(x)
        x = x[int(n/6):]
        size_frame = len(x)
        hamming_window = np.hamming(size_frame)
        fft_spec = np.fft.rfft(x * hamming_window)
        ans = np.abs(fft_spec)
        # ans = np.log(np.abs(fft_spec))
        plt.plot(ans[2:100],label=p.stem)
        plt.legend()

    base_path = ROOT / 'result' / 'test2'
    base_path.mkdir(exist_ok=True)

    save_path = base_path / 'figure'
    save_path.mkdir(exist_ok=True)
    plt.savefig(str(save_path / (f'{target_name}_{condition}.png')))

def compare(condition, save_dir_name):
    range10_list = [
        'error_0001_2_range10-flw0-rtt.npy',
        'gw_30_normal_2_range10-flw0-rtt.npy',
        'normal_2-flw0-rtt.npy',
        'udp_2_range10-flw0-rtt.npy'
    ]
    range50_list = [
        'error_0001_2_range50-flw0-rtt.npy',
        'gw_30_normal_2_range50-flw0-rtt.npy',
        'normal_2_range50-flw0-rtt.npy',
        'udp_2_range50-flw0-rtt.npy'
    ]
    if condition == 10:
        target_list = range10_list
    elif condition == 50:
        target_list = range50_list

    base_path = ROOT / 'result' / save_dir_name
    path_list = [base_path / f_name for f_name in target_list]

    for p in path_list:
        x = np.load(p)
        n = len(x)
        x = x[int(n/6):]
        size_frame = len(x)
        hamming_window = np.hamming(size_frame)
        fft_spec = np.fft.rfft(x * hamming_window)
        ans = np.abs(fft_spec)
        ans = ans[2:100]
        peaks,_ = find_peaks(ans,prominence=0.1)


        peaks = peaks[np.argsort(ans[peaks])[::-1][:3]]
        


        # ans = np.log(np.abs(fft_spec))
        SR = 400
        fq = np.linspace(0, SR, n)
        fq = fq[2:100]

        # plt.plot(fq[2:100], ans[2:100]label=p.stem)
        # plt.plot(fq, ans, label=p.stem)
        plt.plot(ans, label=p.stem)
        # plt.scatter(fq[peaks], ans[peaks],color='red')
        plt.scatter(peaks, ans[peaks],color='red')

        plt.legend()

    base_path.mkdir(exist_ok=True)

    save_path = base_path / 'figure'
    save_path.mkdir(exist_ok=True)
    plt.savefig(str(save_path / (f'{condition}.png')))
    plt.clf()



def func(data, time, rate, pre_value):
    ans = data[(time-rate < data['sec']) & (data['sec'] < time)]['value']
    if ans.empty:
        return pre_value
    else:
        return ans.mean()


def Lomb_Scargle(path):
    data = plot.read_data(str(path), 30)
    t = data['sec'].to_list()
    rtt = data['value'].to_list()
    frequency, power = LombScargle(t,rtt).autopower(maximum_frequency=5.0)
    plt.plot(frequency, power)
    plt.savefig(f'{path.stem}.png')
    plt.clf()

def check():
    base_path = ROOT / 'result'
    path_list = glob.glob(str(base_path / '*range50*'))
    path_list = [Path(p) for p in path_list]
    print(path_list)
    for p in path_list:
        name = p.stem
        target_path = p / f'{name}-flw0-rtt.data'
        Lomb_Scargle(target_path)

if __name__ == '__main__':
    
    l = [
        # 'error_0001_2_range10',
        # 'error_0001_2_range50',
        'error_0001_3_range10',
        'error_0001_3_range50',
        'error_0001_4_range10',
        'error_0001_4_range50',
        # 'gw_30_normal_2_range10',
        # 'gw_30_normal_2_range50',
        'gw_30_normal_3_range10',
        'gw_30_normal_3_range50',
        'gw_30_normal_4_range10',
        'gw_30_normal_4_range50',
        # 'normal_2',
        # 'normal_2_range50',
        'normal_3',
        'normal_3_range50',
        'normal_4',
        'normal_4_range50',
        # 'udp_2_range10',
        # 'udp_2_range50',
        'udp_3_range10',
        'udp_3_range50',
        'udp_4_range10',
        'udp_4_range50'
    ]
    
    # target_name = 'gw_30_normal_2_range10'
    # for target_name in l:
    #     save_dir_name = 'test'
    #     sampling(target_name, save_dir_name)
    #     plot_stack(target_name,save_dir_name)

    # target_name = 'normal'
    # condition = '_range50-flw0-rtt.npy'
    # save_dir_name = 'test'
    # compare_group(target_name, condition, save_dir_name)

    # compare(10,'test')

    check()

    # path = ROOT / 'result' / 'TCP_Congestion_2_range50' / 'TCP_Congestion_2_range50-flw0-rtt.data'
    # Lomb_Scargle(path)