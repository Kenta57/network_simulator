import pyshark
from pathlib import Path

ROOT = Path.cwd().parent

class Extractor:
    def __init__(self, target_path, prefix):
        self.cap = pyshark.FileCapture(str(target_path))
        self.prefix = prefix
        self.save_dir = ROOT / 'src_python'
        self.save_paths = [self.save_dir / (self.prefix + f'-flow{i}.data') for i in range(3)]

        self.clean_file()

        self.f_streams = [open(str(path), mode='a') for path in self.save_paths]
        self.highest_ack = [0]*3
        self.inflight = [0]*3

    def __del__(self):
        for f in self.f_streams:
            f.close()

    def clean_file(self):
        for p in self.save_paths:
            p.unlink(missing_ok=True)
            p.touch(exist_ok=True)

    def extract_inflight(self):
        for i, packet in enumerate(self.cap):
            transport_layer = packet.transport_layer
            if transport_layer == 'TCP':
                stream_idx = int(packet.tcp.stream)
                self.get_inflight(packet, stream_idx, i)

    def get_inflight(self, packet, stream_idx, index):
        seq = int(packet.tcp.seq)
        ack = int(packet.tcp.ack)
        nxt_seq = int(packet.tcp.nxtseq)
        if seq == 1 and not(ack == 1):
            try:
                sack_option_raw = packet.tcp.options_sack
                ack_virtual = self.get_virtual_ack(sack_option_raw, ack)
                self.highest_ack[stream_idx] = ack_virtual
            except AttributeError:
                self.highest_ack[stream_idx] = max(ack, self.highest_ack[stream_idx])
            # self.highest_ack[stream_idx] = max(ack, self.highest_ack[stream_idx])
        if not(seq == 1) and ack == 1:
            highest_nxt_seq = nxt_seq
            __inflight = highest_nxt_seq - self.highest_ack[stream_idx]
            self.inflight[stream_idx] = __inflight if __inflight > 0 else self.inflight[stream_idx]
            time = packet.tcp.time_relative
            self.f_streams[stream_idx].write(f'{index+1} {time} {self.inflight[stream_idx]} {stream_idx}\n')
            # return time, inflight

    def get_virtual_ack(self, byte_raw, ack):
        sack = self.get_sack_list(byte_raw)
        sack_cnt = len(sack)//2
        received = ack - 1
        for i in range(sack_cnt):
            received += sack[2*i+1] - sack[2*i]
        return received+1

    def get_sack_list(self, byte_raw):
        data = byte_raw.split(':00')
        kind,length = data[0].split(':')
        __sack = [int(''.join(d.split(':')),16) for d in data[1:]]
        sack_cnt = len(__sack)//2
        sack = []
        for i in range(sack_cnt)[::-1]:
            sack += __sack[2*i:2*i+2]
        return sack

if __name__ == '__main__':
    target_path = ROOT / 'result' / 'udp_100Mbps' / 'udp_100Mbps-1-1.pcap'
    prefix = 'new_data'
    Ex = Extractor(target_path, prefix)
    Ex.extract_inflight()
    del Ex



