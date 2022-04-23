# network_simulator
## ns3の環境構築
下記のサイトなどに従ってns3の環境構築を行う. バージョンは`ns-3.30`とする.

https://qiita.com/dorapon2000/items/5c0c0a399aeee629be63

## pythonのライブラリ
```
$ cd src_python
$ pip3 install -r requirements.txt
```
## pysharkを動かすために
tsharkをinstallする必要があるので下記のコマンドを実行
```
$ apt-get update
$ apt-get install -y tshark
```

## ディレクトリ
### `scratch` : ns3のシナリオファイルを保存
+ `mytest.cc` : 対象となるネットワークの構築, 値のトレースを実装. 引数によってシナリオを変更できるように実装. 

### `src_python` : シナリオファイルのパラメータの設定, パケットの解析, 前処理, 機械学習等をpythonで実装
+ `RTT.py` : TCPのend-to-endの通信を中間ノードで観測し, そこで得られたパケットキャプチャからTimestampを使って, RTTの推定を行う.
+ `Extractor.py` : 上記と同様に中間ノードで得られたパケットキャプチャからbyte-in-flight, ACKの推定, 測定を行う. 
+ `plot.py` : グラフの描画の実装
+ `SimulationConfig.py` : シナリオファイルのパラメータの管理とデータの生成を担当
+ `classifier.py` : K-meansを用いたクラスタリングの実装
+ `FFT.py` : FFT, Lomb-Scargle等の周波数分析を実装
+ `random_forest.py` : ランダムフォレストを用いたクラス分類の実装
+ `analyze_pcap.py` : pcapファイルの解析
+ `test.py` : データの生成, グラフの描画, pcapファイルの解析の実装
