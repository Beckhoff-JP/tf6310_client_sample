# TF6310 TCP/IP Socket communication sample

このプログラムは、[TF6310 TCP/IP](https://infosys.beckhoff.com/content/1033/tf6310_tc3_tcpip/index.html?id=9025637582166106076) を用いたST言語で実装した TCP/IPのサンプルプログラムです。

[テクニカルノート](https://beckhoff-jp.github.io/TwinCATHowTo/tf6310/index.html) も併せてご覧ください。

## TwinCAT が TCP/IP クライアントとなるサンプル

* TwinCAT TCP/IP クライアント

    SampleSocketCommunication.sln

* Python TCP/IP サーバ

    testserver.py


## Quick start

#### Python サーバの起動

Python 3.10 以上の環境にて、次の通り実行してください。接続待ち状態となります。

``` bash
$ python testserver.py
Starting TCP server
```

Listenポートは9998でローカルからの接続のみ受け付ける設定となっています。

``` python
async def main():
    loop = asyncio.get_running_loop()
    print("Starting TCP server")
    # ポート9998のUDPで全ホストからの接続を待つ。
    server = await loop.create_server(
            lambda: DummyMeasurementMachineProtocol(),
            '127.0.0.1', 9998
        )

    async with server:
        await server.serve_forever()

    loop.close()
```

外部からの接続を許可するには、ファイヤウォールの任意のポートを許可した上で、インターフェース指定部分を `0.0.0.0` に設定します。

``` python
async def main():
    loop = asyncio.get_running_loop()
    print("Starting TCP server")
    # ポート9998のUDPで全ホストからの接続を待つ。
    server = await loop.create_server(
            lambda: DummyMeasurementMachineProtocol(),
            '0.0.0.0', 9998
        )

    async with server:
        await server.serve_forever()

    loop.close()
```

#### TwinCAT側の設定

事前にTF6310 TCP/IP のインストール、およびライセンス有効が必要です。

MAINプログラムの、以下のプログラムで接続先のPythonのサーバが稼働しているIPアドレスとポートを設定してください。PLCをスタート後、変数 `connect` をTRUEにすると接続と送信、受信を1秒毎に繰り返す動作が開始します。

``` pascal
IF connect THEN
    handle := controller.connect('127.0.0.1', 9998);
ELSE
```

`FB_TestProtocol` ファンクションブロックのインスタンス変数である、`MAIN.protcol` の入力変数 `send_data` がTwinCATからPythonサーバへの送信データ、出力変数 `receive_data` がPythonサーバからの受信データです。受信データは約10kByteの文字列データが格納されています。

## サンプルプログラムの解説

本通信サンプルでは、通信手順を実行するプログラム部と、通信プロトコルのプログラム部を明確に分離しています。

通信プロトコルのプログラムでは、各ユーザ開発者が、送信メッセージと受信メッセージ、およびそのデータチェック等のメソッドを定義するインターフェース `ITF_Sender`, `ITF_Receiver` を実装することで独自のメッセージプロトコルを定義可能です。

通信手順を実行するプログラムでは、これらのインターフェースを通じてユーザが実装した任意のプロトコルを処理します。

> [!tip]
> * 通信手順を定義するプログラムは  `libSocketClient` フォルダ以下
> * 通信プロトコルを定義するプログラムは `Protocols` フォルダ以下に格納しています。共通のメソッドは `FB_SocketClientProtocolBase` 抽象FBに定義されており、各具象プロトコルはこれを継承して定義します。本サンプルのプロトコルは `TestProtocol` フォルダ以下に定義しています。


通信手順を実行するプログラムには、メインプログラム側から非同期に通信を行えるように、 `FB_MessageQueue` FIFOキューが用意されています。キューインしたプロトコルジョブは、 `ITF_TaskObserver` を実装しておくことで、このインターフェースメソッドやプロパティを通して通信実行の進捗やエラー状態をチェックする事ができます。

### ファンクションブロックの構成

#### 通信手順制御プログラムの解説

`libSocketClient` フォルダ以下のPOU

|リソース名|タイプ|説明|
|---|---|---|
|ITF_Sender|インターフェース|送信プロトコルを定義するインターフェース|
|ITF_Receiver|インターフェース|受信プロトコルを定義するインターフェース|
|ITF_TaskObserver|インターフェース|通信の進捗状態、エラーの観察ロジックを定義するインターフェース|
|ST_CommandContainer|構造体|ITF_SenderとITF_Receiverをパックした構造体。`FB_MessageQueue` キュー配列の要素型として用いる。|
|ST_CommunicationMetaData|構造体|送受信に用いるバイトデータブロックのポインタ `pData: PVOID` とサイズ指定 `cbLen : UDINT` をパックしたもの。`T_Arg` 型の重複であるが、これによりTc2_Utilityライブラりの追加を必要としない。|
|E_SocketCommStateMachine|列挙体|`FB_SocketClientController` 内の通信制御の状態マシンを定義します。|
|FB_MessageQueue|ファンクションブロック|通信コマンドを非同期で処理するためのFIFOキューです。これによりコマンド通信処理中でも別のコマンドを受け付けることができます。|
|FB_SocketClientController|ファンクションブロック|1. ソケット接続、2. ITF_Senderを用いたデータ送信、3. ITF_Receiverを用いたデータ受信、4. ソケット切断 の通信手順を実行するファンクションブロック。|

#### プロトコル定義

`protocols` フォルダ以下のPOUは以下のとおりです。本プロジェクトには `TestProtocol` プロトコルが定義されています。同様の方法で任意のプロトコルを定義することができます。

|リソース名|タイプ|説明|
|---|---|---|
|FB_SocketClientProtocolBase|ファンクションブロック|ITF_Sender, ITF_Receiver, ITF_TaskObserverを実装した抽象規定クラス。全てのプロトコルはこのファンクションブロックを継承して作成する。|
|TestProtocol/FB_TestProtocol|ファンクションブロック|FB_SocketClientProtocolBaseを継承して実装したプロトコルFB|
|TestProtocol/ST_SendDataFormat|構造体|受信データのフレーム構造定義。FB_TestProtocolの入力変数として送信データをセットする。|
|TestProtocol/ST_ReceiveDataFormat|構造体|受信データのフレーム構造定義。FB_TestProtocolの出力変数として受信データが格納される。|

上記の`FB_TestProtocol`のとおり、プロトコル特有のメソッドやプロパティを実装する必要が有るのは、次の通りです。

|リソース名|タイプ|引数|戻り値|説明|
|---|---|---|---|---|
|Parse|メソッド|なし|BOOL|親クラスで定義されている `SUPER^.receive_data_buffer` にはTF6310の受信バッファから取り出したデータが蓄積されています。このデータを受信データ構造体 `ST_ReceiveDataFormat` のインスタンス変数にメモリコピーします。|
|received|プロパティ(Get)|"---"|BOOL|受信バッファのデータを蓄積し、組立終わった際にTRUEを返します。`SUPER^.receive_data_size` には受信バッファから取り出して `SUPER^.receive_data_buffer` に蓄積済みのサイズが格納されています。このサイズが規定量 `SIZEOF(<ST_SendDataFormatの変数>)` に達したかどうかを定義するのが良いでしょう。|
|SendData|メソッド|"---"|ST_CommunicationMetaData|送信データ構造体 `ST_SendDataFormat` のインスタンス変数のサイズとポインタを返します。このデータをサーバへ送信します。|

上記以外は親クラスの定義済みのメソッド、プロパティのままで再定義の必要はありません。

### メインプログラム

用意したプロトコルモデルを通じてメインプログラムでは次の通り通信コマンドを発行します。

``` pascal
PROGRAM MAIN
VAR
    protcol : FB_TestProtocol;
    controller : FB_SocketClientController;
    connect : BOOL; // 接続要求

    // Command execution
    execute : BOOL;
    busy : BOOL;
    // Receive data
    receive_data : REFERENCE TO ST_ReceiveDataFormat;
END_VAR

IF connect THEN // <---- 接続する場合このフラグをTRUEにする
	handle := controller.connect('169.254.214.145', 9998); // 接続
ELSE
	controller.disconnect();  // 切断
	busy := FALSE;
END_IF

IF handle.handle <> 0 THEN
    IF execute and NOT busy THEN
        protocol.send_data.hoge := *****; // 送りたいデータをセット
        protocol.send_data.huga := *****;
        controller.queue.put(protcol, protcol); // 作成したプロトコルコマンドをキューに追加して実行予約。
    END_IF

    IF busy AND protcol.complete THEN // キューの処理が完了したらcompleteがTRUEになる。
        receive_data REF= protocol.receive_data; // 受信データを参照取り出しする
        busy := FALSE;
    END_IF
END_IF

controller(); // 常時実行
```
