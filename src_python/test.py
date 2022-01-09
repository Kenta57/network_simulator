#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from tqdm import tqdm
from pathlib import Path

from SimulationConfig import SimulationConfig
import plot

ROOT = Path.cwd().parent

def execute(filename, name, duration):
    save_path = ROOT / 'result' / name
    save_path.mkdir(exist_ok=True)
    save_path = save_path / name

    sim_config = SimulationConfig(filename)
    setting = {}
    setting['duration'] = duration
    setting['prefix_name'] = str(save_path.relative_to(ROOT))
    setting['error_p'] = 0.001
    setting['udp_flag'] = False
    # setting['udp_bandwidth'] = '100Mbps'
    setting['pcap_tracing'] = True
    sim_config.update(setting)

    sim_config.execute()


def main():
    filename = 'mytest'
    name = 'error_gw_0.001'
    duration = 10
    # execute(filename=filename, name=name, duration=duration)
    save_dir = ROOT / 'result' / name
    plot.plot_para(name=name, duration=duration, num_flows=3, para='cwnd', save_dir=save_dir)
    plot.plot_algorithm(name=name, duration=duration, flow=0)


if __name__ == '__main__':
    main()
