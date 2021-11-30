from datetime import datetime
from flask_login import UserMixin


from peewee import *
from playhouse.flask_utils import FlaskDB

flask_db = FlaskDB()
# db = wrapper.database


class Customs(flask_db.Model):
    cus_id = CharField()
    receiver = CharField()
    sender = CharField()
    consumer_unit = CharField()
    delivery_numbers = CharField()
    contract_id = CharField()
    entry_clearance = CharField()
    item_id = CharField()
    item_name = CharField()
    total_price = FloatField()
    surplus = FloatField()
    img_path = CharField()
    contract_type = CharField()


class User(flask_db.Model, UserMixin):
    username = CharField(unique=True)
    password = CharField()
    name = CharField()
    role = CharField()

    def check(self, password):
        return self.password == password


class Transfer(flask_db.Model):
    cus_id = ForeignKeyField(Customs)
    bop_no = CharField()
    trans_no = CharField()
    receiver = CharField()
    amount = FloatField()
    amount_fx = FloatField()
    remitter = CharField()
    unit_code = CharField()
    bene_bank_no = CharField()
    bene_bank = CharField()
    rate = FloatField()
    rmb_equ = FloatField()
    commission = FloatField()
    total_charge = FloatField()
    maker = CharField()
    checker = CharField()
    dt = DateTimeField(default=datetime.now)
    block_number = IntegerField()
    block_hash = CharField()
    tx_id = CharField()
