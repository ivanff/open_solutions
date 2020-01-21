import json
import time

from aio_pika import Message
from aiopg.sa import create_engine
from sqlalchemy import desc
from tornado.web import RequestHandler

from models import devices, reports


class ReportHandler(RequestHandler):
    async def get(self, id):
        results = []
        async with self.settings['engine'].acquire() as conn:
            rows = await conn.execute(
                reports.select().where(reports.c.device_id == id).order_by(desc(reports.c.created))
            )
            async for row in rows:
                results.append(
                    {
                        'timestamp': int(time.mktime(row.created.timetuple())),
                        'report': row.report,
                    }
                )

        self.write({
            'reports': results
        })

    async def post(self, id):
        async with self.settings['engine'].acquire() as conn:
            rows = await conn.execute(
                devices.select().where(devices.c.id == id)
            )
            id = await rows.scalar()
            if id:
                amqp_connection = self.settings['amqp_connection']
                channel = await amqp_connection.channel()
                report_exchange = await channel.declare_exchange('report')
                try:
                    await report_exchange.publish(
                        Message(body=self.request.body),
                        routing_key='output',
                    )
                finally:
                    await channel.close()

                await self.finish("OK")
            else:
                await self.finish("device is UNKNOWN")


class DeviceHandler(RequestHandler):
    async def post(self):
        data = json.loads(self.request.body)
        async with self.settings['engine'].acquire() as conn:
            rows = await conn.execute(
                devices.select().where(devices.c.id == data['id'])
            )
            id = await rows.scalar()
            if not id:
                await conn.execute(
                    devices.insert().values(id=data['id'])
                )

        await self.finish("OK")
