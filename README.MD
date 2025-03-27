# TF6310 TCP/IP Socket communication sample

このプログラムは、[TF6310 TCP/IP](https://infosys.beckhoff.com/content/1033/tf6310_tc3_tcpip/index.html?id=9025637582166106076) を用いたST言語で実装した TCP/IPのサンプルプログラムです。

[テクニカルノート](https://beckhoff-jp.github.io/TwinCATHowTo/tf6310/index.html) も併せてご覧ください。

## TwinCAT が TCP/IP クライアントとなるサンプル

* TwinCAT TCP/IP クライアント

    SampleSocketCommunication.sln

* Python TCP/IP サーバ

    testserver.py


### 使い方

#### サーバの起動

Python 3.10 以上の環境にて、次の通り実行してください。接続待ち状態となります。

``` bash
$ python testserver.py
Starting TCP server
```

#### TwinCATの設定と接続

MAINプログラムの、下記の通り接続してください。

``` pascal
PROGRAM MAIN
VAR
    :
    server_addr	: ST_SockAddr := (nPort := 9998, sAddr := '127.0.0.1'); 
    :
END_VAR
```
#### TwinCAT

メインプログラムの下記変数を次の通り制御してください。

``` pascal
PROGRAM MAIN
VAR
    :
    bConnect	: BOOL; // サーバへの接続
    bStart		: BOOL; // サーバへのコマンド送信とデータ受信待ちシーケンス開始
    :
END_VAR
```

|変数|説明|
|--|--|
|bConnect|TRUEにすると接続開始し、FALSEにすると切断します。ただし、bStartによるシーケンス実行中は切断できません。|
|bStart|TRUEにするとサーバへのコマンド送信とデータ受信待ちシーケンス開始します。終了すると自動的にFALSEに戻ります。|
