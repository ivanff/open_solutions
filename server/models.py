import sqlalchemy as sa

metadata = sa.MetaData()

reports = sa.Table(
    'reports', metadata,
    sa.Column('id', sa.Integer, autoincrement=True, primary_key=True),
    sa.Column('device_id', sa.Integer, sa.ForeignKey('devices.id'), nullable=False),
    sa.Column('report', sa.String(36)),
    sa.Column('created', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
)

devices = sa.Table(
    'devices', metadata,
    sa.Column('id', sa.Integer, primary_key=True)
)
