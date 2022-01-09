import pyshark
from pathlib import Path

from Extractor import Extractor
import plot


ROOT = Path.cwd().parent

def main():
    name = 'udp_100Mbps'
    save_dir = ROOT / 'result' / name
    target_path = save_dir / f'{name}-1-1.pcap'
    Ex = Extractor(target_path, sack_option=True)
    Ex.extract_inflight()
    del Ex
    plot.plot_para(name='pcap', duration=10, num_flows=3, para='inflight', save_dir=save_dir)


if __name__ == '__main__':
    main()

