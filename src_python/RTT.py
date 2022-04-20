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

def main():
    target_dir = Path('/home/murayama/Document/ns3/ns-3-allinone/ns-3.30/data/Normal_0_range10')
    r_estimators = [rtt_estimator(target_dir, index) for index in range(3)]
    prefix = target_dir.name
    target_path = target_dir / f'{prefix}-1-1.pcap'
    cap = pyshark.FileCapture(str(target_path))
    
    for index, packet in enumerate(cap):
        transport_layer = packet.transport_layer
        if transport_layer == 'TCP':
            stream_idx = int(packet.tcp.stream)
            r_estimators[stream_idx].push(packet)

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

def plot_old_new_rtt():
    base_path = ROOT / 'data'
    path_list = [Path(p).name for p in glob.glob(str(base_path / '*'))]
    path_list.sort()
    # pprint.pprint(path_list)

    # base_path = ROOT / 'result'

    name_list = ['Normal_0_range10']

    # category = 'Normal_0_range10'
    # name_list = []
    # for name in path_list:
    #     if category in name:
    #         name_list.append(name)
    
    print(name_list)

    # p_l = [base_path/name for name in name_list]
    old_rtt_list = []
    flow_index = 0
    para = 'rtt'
    duration = 30
    for name in name_list:
        plt.figure(figsize=(12, 12))
        plt.title(name)
        p = base_path / name / f'{name}-flw{flow_index}-{para}.data' 
        __plot_old_new_rtt(p, 1, duration, para)
        p = base_path / name / f'{name}-flw{flow_index}-{para}_sampling.data' 
        __plot_old_new_rtt(p, 2, duration, para)
        p = base_path / name / f'{name}-flw{flow_index}-{para}_estimate.data' 
        __plot_old_new_rtt(p, 3, duration, para)
        
        # old_rtt_list.append(p)
        # data = plot.read_data(file_name = str(p), duration = duration)
        # plt.subplot(3, 1, 1)
        # plot.plot_metric(data, duration, para, None, 1, True)

        

    save_path = ROOT / 'src_python' / 'test.png'
    plt.savefig(str(save_path))
    # print(old_rtt_list[0].exists())

    # for p in p_l:
    #     save_dir = p
    #     name = p.name
    #     duration = 30
    #     plot_one(name=name, duration=duration, flow_index=0, para='rtt', save_dir=save_dir)

def __plot_old_new_rtt(path, plt_index, duration, para):
    data = plot.read_data(file_name = str(path), duration = duration)
    plt.subplot(3, 1, plt_index)
    plot.plot_metric(data, duration, para, None, 1, True)

                

if __name__ == '__main__':
    # target_dir = Path('/home/murayama/Document/ns3/ns-3-allinone/ns-3.30/data/Normal_0_range10')
    # r_estimator = rtt_estimator(target_dir)
    # r_estimator.test()

    # path_list = [save_path / 'rtt_sampling.data', save_path / 'rtt_estimate.data']
    # for p in path_list:
    #     plot_rtt(p)
    plot_old_new_rtt()
    # main()



