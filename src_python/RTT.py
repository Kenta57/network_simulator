import pyshark
from pathlib import Path
from tqdm import tqdm
from collections import deque
import glob
import pprint

import plot
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent

class rtt_estimator:
    def __init__(self, target_dir, flow_idx):
        self.alpha = 0.125
        self.estimatedRtt = None
        self.samplingRtt = None
        self.ack_queue = deque()
        self.TSval = None
        self.prefix = target_dir.name
        save_path_sampling = target_dir / f'{self.prefix}-flw{flow_idx}-rtt_sampling.data'
        save_path_estimate = target_dir / f'{self.prefix}-flw{flow_idx}-rtt_estimate.data'
        for p in [save_path_sampling, save_path_estimate]:
            p.unlink(missing_ok=True)

        self.stream_sampling = open(str(save_path_sampling), mode='a')
        self.stream_estimate = open(str(save_path_estimate), mode='a')
    
    def __del__(self):
        self.stream_sampling.close()
        self.stream_estimate.close()

    def isACK(self, segment):
        seq = int(segment.seq)
        ack = int(segment.ack)
        return seq == 1 and ack != 1

    def push(self, packet):
        if self.isACK(packet.tcp):
            self.ack_queue.append(packet)
        elif len(self.ack_queue) != 0:
            if self.TSval is not None and packet.tcp.options_timestamp_tsecr == self.TSval:
                pass
            else:
                self.TSval = self.ack_queue[0].tcp.options_timestamp_tsval
                self.rtt_sampling(self.ack_queue[0], packet)
                self.rtt_estimate()
                self.ack_queue.popleft()

    def rtt_sampling(self, packet_TSval, packet_TSecr):
        self.samplingRtt = float(packet_TSecr.sniff_timestamp) - float(packet_TSval.sniff_timestamp)
        self.time = packet_TSecr.sniff_timestamp
        self.stream_sampling.write(f'{self.time} {self.samplingRtt}\n')
        print(f'time : {self.time}, rtt_s : {self.samplingRtt}')
        return self.samplingRtt

    def rtt_estimate(self):
        if self.estimatedRtt is None:
            self.estimatedRtt = self.samplingRtt
        else:
            self.estimatedRtt += (self.samplingRtt - self.estimatedRtt) * self.alpha
        print(f'time : {self.time}, rtt_e : {self.estimatedRtt}')
        self.stream_estimate.write(f'{self.time} {self.estimatedRtt}\n')
        return self.estimatedRtt

def main(target_dir):
    r_estimators = [rtt_estimator(target_dir, index) for index in range(3)]
    prefix = target_dir.name
    target_path = target_dir / f'{prefix}-1-1.pcap'
    cap = pyshark.FileCapture(str(target_path))
    
    for index, packet in enumerate(cap):
        transport_layer = packet.transport_layer
        if transport_layer == 'TCP':
            stream_idx = int(packet.tcp.stream)
            if stream_idx > 2:
                    continue
            r_estimators[stream_idx].push(packet)
    
    for r_e in r_estimators:
        del r_e

def plot_rtt(target_path):
    metric = plot.read_data(file_name = target_path, duration = 30)

    # plt.title(name[:-10])
    plt.subplots_adjust(left=0.2)
    x_ticks = True
    x_max = None
    y_max = None
    para = 'rtt'
    y_label = para
    if para=='inflight' or para=='cwnd':
        y_max = 250000

    y_deno = 1
    # 階段状にplotする
    # where=preは左側にstepができる
    # cは色でkは黒
    plt.step(
        metric.sec, metric.value/y_deno,
        # c='k', 
        where='pre')
    # x方向の表示範囲
    plt.xlim(0, x_max)
    # y軸のラベル名
    plt.ylabel(y_label.upper()+'[s]')

    # y軸の最大値．
    if y_max:
        plt.ylim(0, y_max)

    # x軸のメモリを表示するか否か．
    if x_ticks:
        plt.xlabel('time[s]')
    else:
        plt.xticks([])

    save_path = ROOT / f'src_python/{target_path.stem}.png'

    # 保存
    plt.savefig(str(save_path))
    plt.clf()

def plot_old_new_rtt(name_list):
    base_path = ROOT / 'data'
    para = 'rtt'
    duration = 30

    for name in name_list:
        plt.figure(figsize=(10*3, 20))
        plt.suptitle(name, fontsize=50)
        for flow_index in range(3):
            p = base_path / name / f'{name}-flw{flow_index}-{para}.data' 
            __plot_old_new_rtt(p, 1 + flow_index, duration, para)
            p = base_path / name / f'{name}-flw{flow_index}-{para}_sampling.data' 
            __plot_old_new_rtt(p, 4 + flow_index, duration, para)
            p = base_path / name / f'{name}-flw{flow_index}-{para}_estimate.data' 
            __plot_old_new_rtt(p, 7 + flow_index, duration, para)

        save_path = ROOT / 'data' / name / 'figure' / f'{name}-rtt_estimate.png'
        plt.savefig(str(save_path))
        plt.clf()

def __plot_old_new_rtt(path, plt_index, duration, para):
    data = plot.read_data(file_name = str(path), duration = duration)
    plt.subplot(3, 3, plt_index)
    plot.plot_metric(data, duration, para, None, 1, True)
    plt.title(path.stem[len(path.parent.stem)+6:])

def spot_list(target_list, OK_word, NG_list):
    flag = True
    name_list = []
    for name in target_list:
        if OK_word in name:
            for word in NG_list:
                if word in name:
                    flag = False
            if flag:
                name_list.append(name)
            flag = True 
    return name_list   

if __name__ == '__main__':
    base_path = ROOT / 'data'
    path_list = [Path(p).name for p in glob.glob(str(base_path / '*'))]
    path_list.sort()

    category = 'range50'
    NG_list = ['UDP']
    name_list = spot_list(path_list, category, NG_list)

    pprint.pprint(name_list)

    for name in tqdm(name_list):
        print(name)
        main(base_path/name)

    plot_old_new_rtt(name_list)



