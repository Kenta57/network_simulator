import pyshark
from pathlib import Path

ROOT = Path.cwd().parent
path = ROOT / 'result' / 'test_2' / 'test_2-2-1.pcap'


def get_inflight(cap, save_path):
    highest_ack = 0
    highest_nxt_seq = 0
    inflight = 0

    with open(save_path, mode='w') as f:
        for i, packet in enumerate(cap):
            seq = int(packet.tcp.seq)
            ack = int(packet.tcp.ack)
            nxt_seq = int(packet.tcp.nxtseq)
            if seq == 1 and not(ack == 1):
                try:
                    sack_option_raw = packet.tcp.options_sack
                    ack_virtual = get_virtual_ack(sack_option_raw, ack)
                    highest_ack = ack_virtual
                except AttributeError:
                    highest_ack = max(ack, highest_ack)

            if not(seq == 1) and ack == 1:
                highest_nxt_seq = nxt_seq
                __inflight = highest_nxt_seq - highest_ack
                inflight = __inflight if __inflight > 0 else inflight
                time = packet.tcp.time_relative
                f.write(f'{i+1} {time} {inflight}\n')

def get_sack(byte_raw):
    data = byte_raw.split(':00')
    kind,length = data[0].split(':')
    __sack = [int(''.join(d.split(':')),16) for d in data[1:]]
    sack_cnt = len(__sack)//2
    sack = []
    for i in range(sack_cnt)[::-1]:
        sack += __sack[2*i:2*i+2]
    return sack

def get_virtual_ack(byte_raw, ack):
    sack = get_sack(byte_raw)
    received = ack - 1
    for i in range(sack_cnt):
        received += sack[2*i+1] - sack[2*i]
    return received+1


if __name__ == '__main__':
    cap = pyshark.FileCapture(str(path))
    save_path = ROOT / 'src_python' / 'inflight.data'
    get_inflight(cap, save_path)

        
    # # tcpで使える関数
    # print(dir(packet.tcp))

    # # packetの到着時間
    # print(packet.sniff_time)

