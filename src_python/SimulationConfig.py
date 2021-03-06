import configparser
from typing import Dict, Tuple, Union, Any
import subprocess
from pathlib import Path
import glob
import json


ROOT = Path.cwd().parent

class SimulationConfig:
    """ シミュレーションを行う際の設定を管理するクラス """

    def __init__(self, filename):
        self.cmd = None
        self.filename = filename

        self.parameters = {
            'transport_prot':'TcpNewReno', 
            'tracing':True, 
            'duration':100, 
            'error_p':0.001,
            'prefix_name':'result/test',
            'bandwidth':"1Mbps", 
            'delay':"1ms",
            'global_delay':"5ms",
            'delay_random':True,
            'access_bandwidth':"100Mbps", 
            'access_delay':"10ms", 
            'udp_flag':True, 
            'udp_bandwidth':"100Mbps", 
            'data':0, 
            'mtu':1500, 
            'flow_monitor':False, 
            'pcap_tracing':False,
            'q_size':10, 
            'num_flows':3
        }

    def update(self, setting: Dict) -> None:
        """ 設定を更新する """

        for key, value in setting.items():
            if key in self.parameters.keys():
                self.parameters[key]=value
    
    def update_json(self, json_path):
        with open(str(save_path)) as f:
            self.parameters = json.load(f)

    # コマンドライン引数を追加したコマンドを作成する関数
    def make_command(self):
        cmd = f'./waf --run "{self.filename}'
        for key, value in self.parameters.items():
            cmd += f' --{key}={value}'
        cmd += '"'
        self.cmd = cmd
        return self.cmd
    
    def execute(self):
        if self.cmd is None:
            self.make_command()
        print(self.cmd)
        subprocess.check_output(self.cmd, shell=True, cwd=str(ROOT)).decode()
        self.__setting_save()

    def show(self):
        print(self.parameters)
        return self.parameters

    def __setting_save(self):
        save_path = ROOT / (self.parameters['prefix_name'] + '_setting.txt')
        json_path = ROOT / (self.parameters['prefix_name'] + '_setting.json')
        with open(str(json_path), 'w') as f:
            json.dump(self.parameters, f, indent=4)
        with open(str(save_path), mode='a') as f:
            for key, value in self.parameters.items():
                f.write(f'{key} : {value}\n')

    def delete_pcap(self):
        base_path = (ROOT / self.parameters['prefix_name']).parent
        target_paths = [Path(p).unlink() for p in glob.glob(str(base_path / '*.pcap')) if '-1-1' not in p]

    


if __name__=='__main__':
    filename = 'mytest'
    s = SimulationConfig(filename)
    setting = {}
    setting['duration'] = 10
    s.update(setting)
    s.show()
    s.execute()

