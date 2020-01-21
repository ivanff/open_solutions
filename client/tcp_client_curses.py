import asyncio
import datetime
import functools
import sys
import curses
from curses import wrapper

from tornado.tcpclient import TCPClient

try:
    device_id = int(sys.argv[1])
except:
    print(
        "Need device id set as first argument"
    )
    sys.exit(1)


async def connect(stream, stdscr):
    message_body = bytes(
        "@{device_id},{report}@".format(device_id=device_id, report='name').encode('utf8')
    )

    await stream.write(message_body)

    while True:
        data = await stream.read_until_regex(b"@([^\@]+)@")
        stdscr.addstr(
            0, 0, "{time}: Data {data}, {status}".format(
                time=datetime.datetime.now(),
                data=data,
                status='Success' if message_body == data else "Error"
            )
        )
        stdscr.refresh()
        # print(
        #     datetime.datetime.now(),
        #     "Client get value",
        #     data,
        #     'Success' if message_body == data else "Error"
        # , end='\r', flush=True)


def my_raw_input(stdscr, r, c, prompt_string):
    curses.echo()
    curses.curs_set(1)
    stdscr.addstr(r, c, prompt_string)
    stdscr.refresh()
    input = stdscr.getstr(r + 1, c)
    return input


class Prompt:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.q = asyncio.Queue(loop=self.loop)
        self.loop.add_reader(sys.stdin, self.got_input)

    def got_input(self):
        asyncio.ensure_future(self.q.put(sys.stdin.readline()), loop=self.loop)

    async def __call__(self, msg, stdscr, end='\n', flush=False):
        # print(msg, end=end, flush=flush)
        stdscr.addstr(
            1, 0, "{prompt}".format(
                prompt=msg
            )
        )
        stdscr.refresh()

        return (await self.q.get()).rstrip('\n')


prompt = Prompt()
raw_input = functools.partial(prompt, end='\r', flush=True)


async def keyboard(stream, stdscr):
    while True:
        ioloop = asyncio.get_event_loop()

        report = await ioloop.run_in_executor(
            None,
            functools.partial(my_raw_input, stdscr, 0, 0, "Send report value:")
        )

        await stream.write(
            bytes(
                "@{device_id},{report}@".format(device_id=device_id, report=report).encode('utf8')
            )
        )


async def refresh(*args):
    while True:
        for i in args:
            i.refresh()
        await asyncio.sleep(0)


async def multiple_tasks(stdscr):
    tcp_client = TCPClient()
    stream = await tcp_client.connect('localhost', 8889)

    display_window = stdscr.derwin(6, 60, 5, 0)
    command_window = stdscr.derwin(3, 30, 0, 0)
    # stdscr.keypad(1)
    # command_window.keypad(1)
    # display_window.keypad(1)

    display_window.border()
    command_window.border()

    # ioloop = asyncio.get_event_loop()
    #
    # ioloop.create_task(
    #     keyboard(stream, command_window)
    # )

    input_coroutines = [
        keyboard(stream, command_window),
        connect(stream, display_window),
        # refresh(
            # display_window,
            # command_window,
            # stdscr,
        # ),
    ]

    res = await asyncio.gather(*input_coroutines, return_exceptions=False)
    return res


def run(stdscr):
    curses.nocbreak()
    # curses.echo()

    # stdscr.keypad(False)
    stdscr.clear()

    ioloop = asyncio.get_event_loop()

    ioloop.run_until_complete(
        multiple_tasks(stdscr)
    )

    ioloop.close()
    stdscr.refresh()


if __name__ == "__main__":
    wrapper(run)
