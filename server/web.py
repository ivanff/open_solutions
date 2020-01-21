import asyncio
import json
import getopt
import sys
import functools
from time import sleep

import tornado.ioloop
import tornado.web
from aio_pika import connect_robust, IncomingMessage
from aiopg.sa import create_engine
from sqlalchemy.sql.ddl import CreateTable

from tornado.routing import Rule, PathMatches

import settings
from web_handlers.common import NotFoundHandler
from web_handlers.api_v1.device import ReportHandler, DeviceHandler

from models import reports, devices


async def on_message_input(engine, message: IncomingMessage):
    with message.process():
        # check exists and add to db
        data = json.loads(message.body)
        async with engine.acquire() as conn:
            rows = await conn.execute(
                devices.select().where(devices.c.id == data['id'])
            )
            id = await rows.scalar()
            if id:
                print(
                    'web on_message_input', data
                )
                await conn.execute(
                    reports.insert().values(
                        device_id=id,
                        report=data['report'][:36]
                    )
                )
            else:
                print(
                    'web on_message_{routing} UNKNOWN device_id {data}'.format(
                        routing=message.routing_key,
                        data=data
                    )
                )


async def db_prepair(engine):
    async with engine.acquire() as conn:
        print(
            "Recreate tables in db"
        )
        await conn.execute('DROP TABLE IF EXISTS reports')
        await conn.execute('DROP TABLE IF EXISTS devices')
        await conn.execute(CreateTable(devices))
        await conn.execute(CreateTable(reports))


async def make_amqp_connection(engine):
    amqp_connection = await connect_robust(host=settings.RABBIT_HOST)
    channel = await amqp_connection.channel()

    report_exchange = await channel.declare_exchange('report')

    queue = await channel.declare_queue()
    await queue.bind(report_exchange, routing_key='input')
    await queue.consume(functools.partial(on_message_input, engine))

    return amqp_connection


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "chd:", ["clean", "help", "delay="])
    except getopt.GetoptError as es:
        print(str(es))
        sys.exit(2)

    clean = False
    for currentArgument, currentValue in opts:
        if currentArgument in ("-h", "--help"):
            print(
                "-d --delay start up delay in seconds",
                "-c --clean for recreate tables in db",
                "-h --help print this message",
                sep='\n')
            sys.exit(2)
        if currentArgument in ("-c", "--clean"):
            clean = True
        if currentArgument in ("-d", "--delay"):
            sleep(int(currentValue))

    tornado.ioloop.IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
    io_loop = tornado.ioloop.IOLoop.current()
    asyncio.set_event_loop(io_loop.asyncio_loop)

    db_engine = io_loop.asyncio_loop.run_until_complete(
        create_engine(settings.DB_URI, loop=io_loop.asyncio_loop)
    )

    amqp_connection = io_loop.asyncio_loop.run_until_complete(
        make_amqp_connection(db_engine)
    )

    if clean:
        io_loop.asyncio_loop.run_until_complete(db_prepair(db_engine))

    application = tornado.web.Application([
        Rule(
            PathMatches("/api/v1/.*"),
            tornado.web.Application([
                (r"/api/v1/device/(?P<id>\d+)/reports", ReportHandler),
                (r"/api/v1/device", DeviceHandler),
            ], amqp_connection=amqp_connection, engine=db_engine),
            {},
            'api_v1'
        )
    ], default_handler_class=NotFoundHandler)
    application.listen(8888)

    try:
        io_loop.start()
    except KeyboardInterrupt:
        print(
            'STOP'
        )
        db_engine.close()
        io_loop.asyncio_loop.run_until_complete(
            db_engine.wait_closed()
        )
        io_loop.stop()
