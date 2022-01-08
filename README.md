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
