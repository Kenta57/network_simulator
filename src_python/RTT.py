import pyshark
from pathlib import Path
from tqdm import tqdm
from collections import deque

import plot
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent

class rtt_estimator:
    def __init__(self, target_path, save_path):
        self.alpha = 0.125
        self.estimatedRtt = None
        self.samplingRtt = None
        self.cap = pyshark.FileCapture(str(target_path))
        paths = [save_path / 'rtt_sampling.data', save_path / 'rtt_estimate.data']

        self.streams = [open(str(p), mode='a') for p in paths]

    def isACK(self, segment):
        seq = int(segment.seq)
        ack = int(segment.ack)
        return seq == 1 and ack != 1

    def test(self):
        ack_queue = deque()
        TSval = None
        for index, packet in enumerate(self.cap):
            transport_layer = packet.transport_layer
            if transport_layer == 'TCP':
                # segment = packet.tcp
                stream_idx = int(packet.tcp.stream)
                if stream_idx != 0:
                    continue

                if self.isACK(packet.tcp):
                    ack_queue.append(packet)
                elif len(ack_queue) != 0:
                    if TSval is not None and packet.tcp.options_timestamp_tsecr == TSval:
                        continue
                    else:
                        TSval = ack_queue[0].tcp.options_timestamp_tsval
                        self.rtt_sampling(ack_queue[0], packet)
                        self.rtt_estimate()
                        ack_queue.popleft()
                        # TODO: RTT_sampling

    def rtt_sampling(self, packet_TSval, packet_TSecr):
        self.samplingRtt = float(packet_TSecr.sniff_timestamp) - float(packet_TSval.sniff_timestamp)
        self.time = packet_TSecr.sniff_timestamp
        self.streams[0].write(f'{self.time} {self.samplingRtt}\n')
        print(f'time : {self.time}, rtt_s : {self.samplingRtt}')
        return self.samplingRtt

    def rtt_estimate(self):
        if self.estimatedRtt is None:
            self.estimatedRtt = self.samplingRtt
        else:
            self.estimatedRtt += (self.samplingRtt - self.estimatedRtt) * self.alpha
        print(f'time : {self.time}, rtt_e : {self.estimatedRtt}')
        self.streams[1].write(f'{self.time} {self.estimatedRtt}\n')
        return self.estimatedRtt

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
                



if __name__ == '__main__':
    # target_path = ROOT / 'result' / 'udp_100Mbps' / 'udp_100Mbps-1-1.pcap'
    # Ex = Extractor(target_path)
    # Ex.extract_inflight()
    # del Ex

    target_path = Path('/home/murayama/Document/ns3/ns-3-allinone/ns-3.30/data/Normal_0_range10/Normal_0_range10-1-1.pcap')
    save_path = Path('/home/murayama/Document/ns3/ns-3-allinone/ns-3.30/src_python')
    # r_estimator = rtt_estimator(target_path, save_path)
    # r_estimator.test()

    path_list = [save_path / 'rtt_samplig.data', save_path / 'rtt_estimate.data']
    for p in path_list:
        plot_rtt(p)



