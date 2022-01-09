
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

sns.set_style(style='ticks')
plt.rcParams['font.size'] = 14

ROOT = Path.cwd().parent

# 計算結果を出力するディレクトリ名．
save_path = ROOT / 'result'
# TCPアルゴリズム一覧．
algorithms = [
    'TcpNewReno', 'TcpHybla', 'TcpHighSpeed', 'TcpHtcp',
    'TcpVegas', 'TcpScalable', 'TcpVeno', 'TcpBic', 'TcpYeah',
    'TcpIllinois', 'TcpWestwood']

# 保存用ディレクトリを作成．
save_path.mkdir(exist_ok=True)

def read_data(file_name, duration):
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

# 複数の送信ノードのTCPの内部状態をプロットする関数．
def plot_para(name, duration, num_flows, para, save_dir):
    paths = [save_dir / f'{name}-flw{i}-{para}.data' for i in range(num_flows)]

    plt.figure(figsize=(12, 12))
    plt.title(name)
    for index, path in enumerate(paths):
        data = read_data(path, duration)
        plt.subplot(4, 1, index+1)
        x_ticks = index+1==num_flows 
        plot_metric(data, duration, para, None, 1, x_ticks)

    # 保存
    plt.savefig(str(save_dir/f'{name}-{para}-flows.png'))

# algorithmのcwnd，ssth，rtt，cong-stateをプロットする関数．
def plot_algorithm(name, duration, flow):
    save_path = ROOT / 'result' / name
    # para = [
    #     'ack', 'cong-state', 'cwnd', 'inflight', 'next-rx', 'next-tx',
    #     'rto', 'rtt', 'ssth', 'throughput'
    #         ]

    paras = ['cwnd', 'ssth', 'inflight']

    paths = [save_path / f'{name}-flw{flow}-{p}.data' for p in paras]

    plt.figure(figsize=(12, 12))
    plt.title(name)
    index = 1
    for para, path in zip(paras,paths):
        data = read_data(path, duration)
        plt.subplot(4, 1, index)
        plot_metric(data, duration, para)
        index += 1

    path = save_path / f'{name}-flw{flow}-cong-state.data'
    cong_state = read_data(path, duration)

    plt.subplot(4, 1, 4)
    # 一番下のプロットのみx軸を描画．
    plot_cong_state(
        cong_state, duration, 'cong-state',
        x_ticks=True)

    # 保存
    plt.savefig(str(save_path/f'{name}-flw{flow}.png'))

def main():
    filename = 'mytest'
    name = 'test_3'
    duration = 10
    execute(filename=filename, name=name, duration=duration)
    plot_para(name=name, duration=duration, num_flows=3, para='cwnd')
    plot_algorithm(name=name, duration=duration, flow=0)


if __name__ == '__main__':
    main()
