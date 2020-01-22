import asyncio
import datetime
import sys
import os
import getopt
from time import sleep

import requests
from tornado.tcpclient import TCPClient


async def writer(stream, message_body):
    try:
        while True:
            print(
                'Write to stream ', message_body
            )
            await stream.write(message_body)
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        pass


async def reader(stream, message_body, writer_task):
    while True:
        data = await stream.read_until_regex(b"@([^\@]+)@")

        if not writer_task.cancelled():
            writer_task.cancel()
            print(
                "STOP writer by reader"
            )

        print(
            "{time}: Data {data}, {status}".format(
                time=datetime.datetime.now(),
                data=data,
                status='Success' if message_body == data else "Error"
            )
        )


async def multiple_tasks(device_id):
    print(
        "CLIENT {id} CONNECTED TO 8889".format(id=device_id)
    )
    tcp_client = TCPClient()

    stream = await tcp_client.connect(os.environ.get('OPEN_SOLUTION_TCP_SERVER_HOST', 'localhost'), 8889)

    message_body = bytes(
        "@{device_id},{report}@".format(device_id=device_id, report='name').encode('utf8')
    )

    writer_task = asyncio.run_coroutine_threadsafe(
        writer(stream, message_body),
        asyncio.get_event_loop()
    )

    # try:
    #     await asyncio.wait_for(asyncio.sleep(10), timeout=10)
    # except asyncio.TimeoutError:
    #     if not writer_task.cancelled():
    #         writer_task.cancel()
    #         print(
    #             "STOP writer"
    #         )


    input_coroutines = [
        reader(stream, message_body, writer_task)
    ]

    res = await asyncio.gather(*input_coroutines, return_exceptions=False)
    return res


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:d:", ["help", "id=", "delay="])
    except getopt.GetoptError as es:
        print(str(es))
        sys.exit(2)

    device_id = None
    for currentArgument, currentValue in opts:
        if currentArgument in ("-h", "--help"):
            print(
                "-d --delay start up delay in seconds",
                "-i --id device id",
                "-h --help print this message",
                sep='\n')
            sys.exit(2)
        if currentArgument in ("-i", "--id"):
            device_id = int(currentValue)
        if currentArgument in ("-d", "--delay"):
            sleep(int(currentValue))

    if not device_id:
        print(
            "Error: need set device id, use --help or -h for detail"
        )
        sys.exit(1)

    print(
        "CREATE DEVICE ", device_id
    )
    requests.post(
        "http://{host}:8888/api/v1/device".format(
            host=os.environ.get('OPEN_SOLUTION_WEB_HOST', 'localhost')
        ),
        json={
            "id": device_id,
        }
    )

    ioloop = asyncio.get_event_loop()

    ioloop.run_until_complete(
        multiple_tasks(device_id)
    )

    ioloop.close()
