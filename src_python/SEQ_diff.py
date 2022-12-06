import pyshark
from pathlib import Path
from tqdm import tqdm
from collections import deque
import glob
import pprint

import plot
import utils
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent

class Extractor_seq_diff:
    def __init__(self, target_dir, flow_idx):
        self.seq = 0
        self.time = 0.0
        self.prefix = target_dir.name
        # save_path = target_dir / f'{self.prefix}-flw{flow_idx}-seq_diff.data'
        save_path = target_dir / f'{self.prefix}-flw{flow_idx}-delta_send.data'
        save_path.unlink(missing_ok=True)

        self.stream_seq = open(str(save_path), mode='a')
    
    def __del__(self):
        self.stream_seq.close()

    def isACK(self, segment):
        seq = int(segment.seq)
        ack = int(segment.ack)
        return seq == 1 and ack != 1

    def push(self, packet):
        if not self.isACK(packet.tcp):
            seq_diff = int(packet.tcp.seq)- self.seq
            time_diff = float(packet.sniff_timestamp) - self.time
            print(seq_diff, time_diff, seq_diff/time_diff)
            # self.stream_seq.write(f'{packet.sniff_timestamp} {seq_diff/time_diff}\n')
            self.stream_seq.write(f'{packet.sniff_timestamp} {time_diff}\n')
            self.seq = int(packet.tcp.seq)
            self.time = float(packet.sniff_timestamp)

def main(target_dir):
    r_estimators = [Extractor_seq_diff(target_dir, index) for index in range(3)]
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

def plot_old_new_rtt(name):
    base_path = ROOT / 'data'
    para = 'seq_diff'
    duration = 30

    plt.figure(figsize=(10*3, 20))
    # plt.suptitle(name, fontsize=50)
    for flow_index in range(3):
        p = base_path / name / f'{name}-flw{flow_index}-{para}.data' 
        __plot_old_new_rtt(p, 1 + flow_index, duration, para)
        # p = base_path / name / f'{name}-flw{flow_index}-{para}_sampling.data' 
        # __plot_old_new_rtt(p, 4 + flow_index, duration, para)
        # p = base_path / name / f'{name}-flw{flow_index}-{para}_estimate.data' 
        # __plot_old_new_rtt(p, 7 + flow_index, duration, para)

    save_path = ROOT / 'data' / name / 'figure' / f'{name}-seq_diff.png'
    plt.savefig(str(save_path))
    plt.clf()

def __plot_old_new_rtt(path, plt_index, duration, para):
    data = plot.read_data(file_name = str(path), duration = duration)
    plt.subplot(3, 3, plt_index)
    plot.plot_metric(data, duration, para, 1e7, 1, True)
    plt.title(path.stem[len(path.parent.stem)+6:])
    
if __name__ == '__main__':
    base_path = ROOT / 'data'
    path_list = [Path(p).name for p in glob.glob(str(base_path / '*'))]
    path_list.sort()

    # targetの絞り込み
    category = 'range100'
    NG_list = ['UDP', '00', 'Link', 'TCP']
    NG_list = []
    name_list = utils.spot_list(path_list, category, NG_list)

    name_list = ['Normal_0_range100', 'TCP_Congestion_0_range100', 'Link_Error_0_range100']

    pprint.pprint(name_list)


    for name in tqdm(name_list[1:]):
        print(name)
        main(base_path/name)
        # # plot_old_new_rtt(name)
        # break




