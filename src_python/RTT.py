import pyshark
from pathlib import Path
from tqdm import tqdm
from collections import deque

ROOT = Path.cwd().parent

class Extractor:
    def __init__(self, target_path, sack_option=True, prefix='inflight'):
        self.cap = pyshark.FileCapture(str(target_path))
        self.prefix = prefix
        self.save_dir = target_path.parent
        self.sack_option = sack_option
        self.save_paths = [self.save_dir / f'{self.save_dir.name}-sack-{self.sack_option}-flw{i}-{self.prefix}.data' for i in range(3)]
        for p in self.save_paths:
            p.unlink(missing_ok=True)

        self.clean_file()

        self.f_streams = [open(str(path), mode='a') for path in self.save_paths]
        self.highest_ack = [0]*3
        self.inflight = [0]*3
        self.DUP_ACK_cnt = [0]*3
        self.ACK = [0]*3

    def __del__(self):
        self.output_DUP_ACK()
        for f in self.f_streams:
            f.close()

    def clean_file(self):
        for p in self.save_paths:
            p.unlink(missing_ok=True)
            p.touch(exist_ok=True)

    def extract(self):
        for i, packet in tqdm(enumerate(self.cap)):
            transport_layer = packet.transport_layer
            if transport_layer == 'TCP':
                stream_idx = int(packet.tcp.stream)
                if stream_idx > 2:
                    continue
                self.get_inflight(packet, stream_idx)
                self.count_DUP_ACK(packet, stream_idx)

    def count_DUP_ACK(self, packet, stream_idx):
        ack = int(packet.tcp.ack)
        seq = int(packet.tcp.seq)
        if seq == 1 and not(ack == 1):
            if ack == self.ACK[stream_idx]:
                self.DUP_ACK_cnt[stream_idx] += 1
            else:
                self.ACK[stream_idx] = ack

    def get_inflight(self, packet, stream_idx):
        seq = int(packet.tcp.seq)
        ack = int(packet.tcp.ack)
        nxt_seq = int(packet.tcp.nxtseq)
        if seq == 1 and not(ack == 1):
            if self.sack_option:
                try:
                    sack_option_raw = packet.tcp.options_sack
                    ack_virtual = self.get_virtual_ack(sack_option_raw, ack)
                    self.highest_ack[stream_idx] = ack_virtual
                except AttributeError:
                    self.highest_ack[stream_idx] = max(ack, self.highest_ack[stream_idx])
            else:
                self.highest_ack[stream_idx] = max(ack, self.highest_ack[stream_idx])
        if not(seq == 1) and ack == 1:
            highest_nxt_seq = nxt_seq
            __inflight = highest_nxt_seq - self.highest_ack[stream_idx]
            self.inflight[stream_idx] = __inflight if __inflight > 0 else self.inflight[stream_idx]
            time = packet.sniff_timestamp
            self.f_streams[stream_idx].write(f'{time} {self.inflight[stream_idx]}\n')

    def get_virtual_ack(self, byte_raw, ack):
        sack = self.get_sack_list(byte_raw)
        sack_cnt = len(sack)//2
        received = ack - 1
        for i in range(sack_cnt):
            received += sack[2*i+1] - sack[2*i]
        return received+1

    def get_sack_list(self, byte_raw):
        data = byte_raw.split(':')
        kind, length = data[0:2]
        data = data[2:]
        n = len(data)//4
        __sack = [int(''.join(data[4*i+1:4*i+4]),16) for i in range(n)]
        sack_cnt = len(__sack)//2
        sack = []
        for i in range(sack_cnt)[::-1]:
            sack += __sack[2*i:2*i+2]
        return sack

    def output_DUP_ACK(self):
        save_path = self.save_dir / f'{self.save_dir.name}-DUP_ACK_num.data'
        with open(str(save_path), mode='w') as f:
            for i, v in enumerate(self.DUP_ACK_cnt):
                f.write(f'{i} {v}\n')

class rtt_estimator:
    def __init__(self, target_path):
        self.alpha = 0.125
        # self.beta =0.25
        self.estimatedRtt = None
        self.samplingRtt = None
        self.cap = pyshark.FileCapture(str(target_path))

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
                        self.rtt_sampling(ack_queue[0], packet, index)
                        self.rtt_estimate()
                        ack_queue.popleft()
                        # TODO: RTT_sampling

    def rtt_sampling(self, packet_TSval, packet_TSecr, index):
        self.samplingRtt = float(packet_TSecr.sniff_timestamp) - float(packet_TSval.sniff_timestamp) 
        # print(f'TSval : {packet_TSval.tcp.options_timestamp_tsval}')
        # print(f'TSecr : {packet_TSecr.tcp.options_timestamp_tsecr}')
        print(f'rtt_s : {self.samplingRtt}, index : {index}')
        return self.samplingRtt

    def rtt_estimate(self):
        if self.estimatedRtt is None:
            self.estimatedRtt = self.samplingRtt
        else:
            self.estimatedRtt += (self.samplingRtt - self.estimatedRtt) * self.alpha
        print(f'rtt_e : {self.estimatedRtt}')
        return self.estimatedRtt

                



if __name__ == '__main__':
    # target_path = ROOT / 'result' / 'udp_100Mbps' / 'udp_100Mbps-1-1.pcap'
    # Ex = Extractor(target_path)
    # Ex.extract_inflight()
    # del Ex

    target_path = Path('/home/murayama/Document/ns3/ns-3-allinone/ns-3.30/data/Normal_0_range10/Normal_0_range10-1-1.pcap')
    # cap = pyshark.FileCapture(str(target_path))
    # test(cap)
    r_estimator = rtt_estimator(target_path)
    r_estimator.test()



