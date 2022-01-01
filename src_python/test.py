#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from tqdm import tqdm
from pathlib import Path

sns.set_style(style='ticks')
plt.rcParams['font.size'] = 14

ROOT = Path.cwd().parent

# 計算結果を出力するディレクトリ名．
save_path = ROOT / 'result' / 'test'
# TCPアルゴリズム一覧．
algorithms = [
    'TcpNewReno', 'TcpHybla', 'TcpHighSpeed', 'TcpHtcp',
    'TcpVegas', 'TcpScalable', 'TcpVeno', 'TcpBic', 'TcpYeah',
    'TcpIllinois', 'TcpWestwood']

# 保存用ディレクトリを作成．
save_path.mkdir(exist_ok=True)


# コマンドライン引数を追加したコマンドを作成する関数
def make_command(
        algorithm=None, prefix_name=None, tracing=None,
        duration=None, error_p=None, bandwidth=None, delay=None,
        access_bandwidth=None, access_delay=None,
        data=None, mtu=None, flow_monitor=None, pcap_tracing=None, q_size=None, num_flows=None):

    """
    - algorithm: 輻輳制御アルゴリズム名．
    - prefix_name: 出力するファイルのプレフィックス名．pwdからの相対パスで表す．
    - tracing: トレーシングを有効化するか否か．
    - duration: シミュレーション時間[s]．
    - error_p: パケットエラーレート．
    - bandwidth: ボトルネック部分の帯域．例：'2Mbps'
    - delay: ボトルネック部分の遅延．例：'0.01ms'
    - access_bandwidth: アクセス部分の帯域．例:'10Mbps'
    - access_delay: アクセス部分の遅延．例:'45ms'．
    - data: 送信するデータ総量[MB]．
    - mtu: IPパケットの大きさ[byte]．
    - flow_monitor: Flow monitorを有効化するか否か．
    - pcap_tracing: PCAP tracingを有効化するか否か．
    - q_size : キューのサイズ(パケット)
    - num_flows : フローの数
    """

    cmd = './waf --run "mytest'
    if algorithm:
        cmd += ' --transport_prot={}'.format(algorithm)
    if prefix_name:
        cmd += ' --prefix_name={}'.format(prefix_name)
    if tracing:
        cmd += ' --tracing={}'.format(tracing)
    if duration:
        cmd += ' --duration={}'.format(duration)
    if error_p:
        cmd += ' --error_p={}'.format(error_p)
    if bandwidth:
        cmd += ' --bandwidth={}'.format(bandwidth)
    if delay:
        cmd += ' --delay={}'.format(delay)
    if access_bandwidth:
        cmd += ' --access_bandwidth={}'.format(access_bandwidth)
    if access_delay:
        cmd += ' --access_delay={}'.format(access_delay)
    if data:
        cmd += ' --data={}'.format(data)
    if mtu:
        cmd += ' --mtu={}'.format(mtu)
    if flow_monitor:
        cmd += ' --flow_monitor={}'.format(flow_monitor)
    if pcap_tracing:
        cmd += ' --pcap_tracing={}'.format(pcap_tracing)
    if q_size:
        cmd += ' --q_size={}'.format(q_size)
    if num_flows:
        cmd += ' --num_flows={}'.format(num_flows)
    cmd += '"'

    return cmd


# def read_data(prefix_name, metric, duration):
def read_data(file_name, duration):
    """
    {prefix_name}{metric}.dataを読みだす関数
    """

    # file_name = '{}{}.data'.format(prefix_name, metric)
    # headerをつけて, 読み込み
    data = pd.read_table(
        file_name, names=['sec', 'value'], delimiter=' ')

    # FIXME: SettingWithCopyWarningを解消したい
    # []でmaskをつける. 条件を満たすもののみ残す.  行のindexを0から振りなおす
    data = data[data.sec <= duration].reset_index(drop=True)
    

    # 作画用に，最終行にduration秒のデータを追加．
    if duration > data.sec.max():
        # 末尾の1行を取得
        tail = data.tail(1)
        tail.sec = duration
        data = pd.concat([data, tail])
    return data


def plot_metric(
        metric, x_max, y_label, y_max=None,
        y_deno=1, x_ticks=False):

    """
    metricの時系列変化をプロットする関数．
    y_denoは単位変換に用いる（byte->segment）
    """

    # 階段状にplotする
    # where=preは左側にstepができる
    # cは色でkは黒
    plt.step(
        metric.sec, metric.value/y_deno,
        c='k', where='pre')
    # x方向の表示範囲
    plt.xlim(0, x_max)
    # y軸のラベル名
    plt.ylabel(y_label)

    # y軸の最大値．
    if y_max:
        plt.ylim(0, y_max)

    # x軸のメモリを表示するか否か．
    if x_ticks:
        plt.xlabel('time[s]')
    else:
        plt.xticks([])


def plot_cong_state(
        cong_state, x_max, y_label, x_ticks=False):
    """
    cong_stateの時系列変化をプロットする関数．
    """

    # 2:rcwは今回の分析対象外なので，
    # 3，4を一つ前にずらす．
    new_state = {
        0: 0, 1: 1, 3: 2, 4: 3}

    # 最初はOpen状態．
    plt.fill_between(
        [0, x_max],
        [0, 0],
        [1, 1],
        facecolor='gray')

    # 各輻輳状態ごとに該当秒数を塗りつぶす．
    for target_state in range(4):
        for sec, state in cong_state.values:
            if new_state[state] == target_state:
                color = 'gray'
            else:
                color = 'white'

            plt.fill_between(
                [sec, x_max],
                [target_state, target_state],
                [target_state+1, target_state+1],
                facecolor=color)

    # 各服装状態を区切る横線を描画．
    for i in range(1, 4):
        plt.plot([0, x_max], [i, i], 'k-')

    plt.xlim(0, x_max)
    plt.ylim(0, 4)
    plt.yticks(
        [0.5, 1.5, 2.5, 3.5],
        ['open', 'disorder', 'recovery', 'loss'])
    plt.ylabel(y_label)

    # x軸のメモリを表示するか否か．
    if x_ticks:
        plt.xlabel('time[s]')
    else:
        plt.xticks([])


# algorithmのcwnd，ssth，rtt，cong-stateをプロットする関数．
def plot_algorithm(algo, duration, save_path, flow):

    # para = [
    #     'ack', 'cong-state', 'cwnd', 'inflight', 'next-rx', 'next-tx',
    #     'rto', 'rtt', 'ssth', 'throughput'
    #         ]

    paras = ['cwnd', 'ssth', 'inflight']

    paths = [save_path / f'TcpNewReno-flw{flow}-{p}.data' for p in paras]

    plt.figure(figsize=(12, 12))
    plt.title(algo)
    index = 1
    for para, path in zip(paras,paths):
        data = read_data(path, duration)
        plt.subplot(4, 1, index)
        plot_metric(data, duration, para)
        index += 1

    path = save_path / 'TcpNewReno-flw0-cong-state.data'
    cong_state = read_data(path, duration)

    plt.subplot(4, 1, 4)
    # 一番下のプロットのみx軸を描画．
    plot_cong_state(
        cong_state, duration, 'cong-state',
        x_ticks=True)

    # 保存
    plt.savefig(str(save_path)+f'_flow{flow}.png')


# ns-3コマンドを実行して，結果をプロットする関数．
def execute_and_plot(
        algo, duration, save_path=save_path, error_p=None, tracing=None,
        bandwidth=None, delay=None, access_bandwidth=None,
        access_delay=None, data=None, mtu=None,
        flow_monitor=None, pcap_tracing=None,
        q_size=None, num_flows=None):

    # 保存用ディレクトリを作成．
    path = save_path / algo
    path.mkdir(exist_ok=True)

    prefix_name = str(path.relative_to(ROOT))

    cmd = make_command(
        algorithm=algo, tracing=tracing,
        duration=duration, prefix_name=prefix_name,
        error_p=error_p, bandwidth=bandwidth, delay=delay,
        access_bandwidth=access_bandwidth,
        access_delay=access_delay,
        data=data, mtu=mtu, flow_monitor=flow_monitor,
        pcap_tracing=pcap_tracing, q_size=q_size, num_flows=num_flows)

    subprocess.check_output(cmd, shell=True, cwd=str(ROOT)).decode()
    # plot_algorithm(algo, duration, save_path)


def main():
    execute_and_plot(algo='TcpNewReno', duration=10, tracing=True, num_flows=3, q_size=100)


if __name__ == '__main__':
    execute_and_plot(algo='TcpNewReno', duration=10, tracing=True, num_flows=3, q_size=100, pcap_tracing=True)
    # algo = 'TcpNewReno'
    # duration = 60
    # plot_algorithm(algo, duration, save_path,0)
