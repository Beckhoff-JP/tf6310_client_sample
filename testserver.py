import asyncio
from struct import pack, unpack

class DummyMeasurementMachineProtocol(asyncio.Protocol):

    def __init__(self):
        self.counter = 0;

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def connection_lost(self, e):
        peername = self.transport.get_extra_info('peername')
        print('Disconnected with {}'.format(peername))
        if e is not None:
            raise(e)


    def data_received(self, data):
        """
        受信イベントハンドラ
         struct.pack/unpackは以下のドキュメント参照のこと。
         https://docs.python.org/ja/3/library/struct.html
         PLCからデータ受信したバイトデータ data を以下の変数へ展開。
         '<'   : リトルエンディアンのバイト配列として解釈
         '5s'  : 5Byte 文字列を、 commandへ展開し、decode()処理して文字列型へ
         'Q'   : unsigned long long int 型 (PLCではULINT型)としてsender_sequence, valueに展開
        """
        command, sender_sequence, value = unpack('<5sQQ', data)
        command = command.decode()
        # 標準出力への表示
        print(f"Received {command}, {sender_sequence}, {value} ")
        print(f"Send sequence : {self.counter}")
        """
        PLCに送信する電文データをバイトデータへパック
         '<'   : リトルエンディアンのバイト配列に組み立てる
         '5s'  : 5Byte 文字列として、'RCOM'という文字にNULLを付加したバイトデータをセット
         'Q'   : sender_sequenceをセット
         '32s'   : 32文字をセット
        """
        send_data = pack('<5sQ32s', b'RCOM\x00', sender_sequence, f"Server count value is : {self.counter}".encode() + b'\x00')
        # 組み立てた電文をPLCに送り返す。
        self.transport.write(send_data)
        # シーケンス番号を繰り上げる。
        if self.counter <= 99999:
            self.counter += 1;
        else:
            self.counter = 0;


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

asyncio.run(main())