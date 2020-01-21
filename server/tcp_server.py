import asyncio
import getopt
import json
import sys
from time import sleep

import aioredis
import tornado.ioloop
from aio_pika import connect_robust, Message, IncomingMessage
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

import settings


async def on_message_output(message: IncomingMessage):
    with message.process():
        data = json.loads(message.body)
        print(
            server.devices
        )
        # отправить клиенту
        for iostream in server.devices.get(data['id'], []):
            if not iostream.closed():
                print(
                    'send to client'
                )
                iostream.write(
                    bytes(
                        "@{id},{report}@".format(**data).encode('utf8')
                    )
                )


async def make_amqp_connection():
    amqp_connection = await connect_robust(host=settings.RABBIT_HOST, port=5672)
    channel = await amqp_connection.channel()

    report_exchange = await channel.declare_exchange('report')

    queue = await channel.declare_queue()
    await queue.bind(report_exchange, routing_key='output')
    await queue.consume(on_message_output)

    return amqp_connection


class EchoServer(TCPServer):
    devices = {}
    clients = {}

    def __init__(self, amqp_connection, *args, **kwargs) -> None:
        self.amqp_connection = amqp_connection
        super().__init__(*args, **kwargs)

    async def handle_stream(self, stream, address):
        amqp_connection = self.amqp_connection
        channel = await amqp_connection.channel()

        report_exchange = await channel.declare_exchange('report')

        while True:
            try:
                b_data = await stream.read_until_regex(b"@([^\@]+)@")
                data = b_data.decode('utf8')
                assert data[0] == '@'
                assert data[-1] == '@'

                device_id_str, report = data[1:-1].split(',')

                device_id = int(device_id_str)

                print(
                    'Server: connected device id', data
                )

                if [stream] != self.devices.setdefault(device_id, [stream]):
                    self.devices[device_id].append(stream)

                self.clients[stream] = device_id

                await report_exchange.publish(
                    Message(body=json.dumps(
                        {
                            'id': device_id,
                            'report': report
                        }
                    ).encode('utf8')),
                    routing_key='input',
                )

                redis = await aioredis.create_redis_pool(settings.REDIS_URI)
                await redis.set(device_id, report)
                redis.close()
                await redis.wait_closed()

                # await stream.write(data)
            except StreamClosedError as es:
                device_id = self.clients.pop(stream, None)
                if device_id:
                    self.devices[device_id] = list(
                        filter(lambda saved_stream: stream != saved_stream, self.devices[device_id])
                    )
                print(
                    'StreamClosedError',
                    es
                )

                break
            except Exception as es:
                print(es)


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:", ["help", "delay="])
    except getopt.GetoptError as es:
        print(str(es))
        sys.exit(2)

    for currentArgument, currentValue in opts:
        if currentArgument in ("-h", "--help"):
            print(
                "-d --delay start up delay in seconds",
                "-h --help print this message",
                sep='\n')
            sys.exit(2)
        if currentArgument in ("-d", "--delay"):
            sleep(int(currentValue))

    tornado.ioloop.IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
    io_loop = tornado.ioloop.IOLoop.current()
    asyncio.set_event_loop(io_loop.asyncio_loop)

    amqp_connection = io_loop.asyncio_loop.run_until_complete(
        make_amqp_connection()
    )

    server = EchoServer(amqp_connection)
    server.listen(8889)

    print("START LISTEN 8889")

    io_loop = tornado.ioloop.IOLoop.current()
    try:
        io_loop.start()
    except KeyboardInterrupt:
        amqp_connection.close()
        io_loop.close()
