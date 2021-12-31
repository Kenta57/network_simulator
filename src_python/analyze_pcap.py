import pyshark
from pathlib import Path

ROOT = Path.cwd().parent

path = ROOT / 'result' / 'test' / 'TcpNewReno-0-2.pcap'

if __name__ == '__main__':
    cap = pyshark.FileCapture(str(path))
    packet = cap[0]
    packet.show()
    
    # tcpで使える関数
    print(dir(packet.tcp))

    # packetの到着時間
    print(packet.sniff_time)

