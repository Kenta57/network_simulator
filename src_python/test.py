#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from tqdm import tqdm
from pathlib import Path
import glob

from SimulationConfig import SimulationConfig
from Extractor import Extractor
import plot



ROOT = Path.cwd().parent

def execute(filename, name, duration):
    save_path = ROOT / 'data' / name
    save_path.mkdir(exist_ok=True)
    save_path = save_path / name

    sim_config = SimulationConfig(filename)
    setting = {}
    setting['duration'] = duration
    setting['prefix_name'] = str(save_path.relative_to(ROOT))
    setting['error_p'] = 0.0
    setting['delay_random'] = True
    setting['global_delay'] = '10ms'
    setting['access_bandwidth'] = '10Mbps'
    setting['bandwidth'] = '30Mbps'
    setting['udp_flag'] = True
    setting['udp_bandwidth'] = '10Mbps'
    setting['pcap_tracing'] = True
    setting['q_size'] = 40
    setting['flow_monitor'] = True
    setting['num_flows'] = 3
    sim_config.update(setting)

    sim_config.execute()
    sim_config.delete_pcap()

def analyze_pcap(name, duration,sack_option=True):
    save_dir = ROOT / 'data' / name
    target_path = save_dir / f'{name}-1-1.pcap'
    Ex = Extractor(target_path, sack_option=sack_option)
    Ex.extract()
    del Ex
    # plot.plot_para(name=f'{name}-sack-{sack_option}', duration=duration, num_flows=3, para='inflight', save_dir=save_dir)

def main():
    for i in range(10):
        filename = 'mytest'
        name = f'UDP_Congestion_{i}_range10'
        duration = 30
        save_dir = ROOT / 'data' / name

        execute(filename=filename, name=name, duration=duration)

        plot.plot_cwnd_rtt(name=name, duration=duration, num_flows=3, save_dir=save_dir)
        plot.plot_para(name=name, duration=duration, num_flows=3, para='cwnd', save_dir=save_dir)
        plot.plot_para(name=name, duration=duration, num_flows=3, para='rtt', save_dir=save_dir)
        # plot.plot_algorithm(name=name, duration=duration, flow=0)

        # analyze_pcap(name,duration,True)
        # analyze_pcap(name,duration,False)
        # analyze_pcap(name, True)

def calc_byte_dup():
    duration = 30
    base_path = ROOT / 'data'
    path_list = [Path(p).name for p in glob.glob(str(base_path/'*range10*'))]
    path_list.sort()
    print(path_list)
    for name in tqdm(path_list):
        print(name)
        analyze_pcap(name, duration, True)


if __name__ == '__main__':
    # main()
    calc_byte_dup()
