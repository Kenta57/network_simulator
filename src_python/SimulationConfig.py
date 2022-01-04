import configparser
from typing import Dict, Tuple, Union, Any
import subprocess
from pathlib import Path


ROOT = Path.cwd().parent

class SimulationConfig:
    """ シミュレーションを行う際の設定を管理するクラス """

    def __init__(self):
        self.cmd = None

        self.parameters = {
            'transport_prot':'TcpNewReno', 
            'tracing':True, 
            'duration':100, 
            'prefix_name':'result/test',
            'error_p_local':0.0, 
            'error_p_global':0.0, 
            'bandwidth':"1Mbps", 
            'delay':"1ms",
            'access_bandwidth':"100Mbps", 
            'access_delay':"10ms", 
            'data':0, 
            'mtu':1500, 
            'flow_monitor':False, 
            'pcap_tracing':False,
            'q_size':100, 
            'num_flows':3
        }

    def update(self, setting: Dict) -> None:
        """ 設定を更新する """

        for key, value in setting.items():
            if key in self.parameters.keys():
                self.parameters[key]=value

    # コマンドライン引数を追加したコマンドを作成する関数
    def make_command(self):
        cmd = './waf --run "mytest'
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

    def show(self):
        print(self.parameters)
        return self.parameters

if __name__=='__main__':
    s = SimulationConfig()
    setting = {}
    setting['duration'] = 10
    s.update(setting)
    s.show()
    s.execute()

