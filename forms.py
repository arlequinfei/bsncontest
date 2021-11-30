# encoding utf-8
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    ValidationError,
    SubmitField,
    PasswordField,
    IntegerField,
    FloatField,
)
from wtforms.validators import DataRequired, Length

from flask_wtf.file import FileField, FileAllowed, FileRequired


class LoginForm(FlaskForm):
    username = StringField("用户名：", validators=[DataRequired(), Length(min=1, max=20)])
    password = PasswordField("密码：", validators=[DataRequired()])
    submit = SubmitField("登陆")


class UploadImageForm(FlaskForm):
    file = FileField(
        "文件",
        validators=[
            FileRequired("必须上传文件"),
            FileAllowed(
                [
                    "jpg",
                    "png",
                ],
                "不允许上传此类文件",
            ),
        ],
    )


class CustomForm(FlaskForm):
    cus_id = StringField("海关编号")
    receiver = StringField("境内收货人")
    sender = StringField("境外发货人")
    consumer_unit = StringField("消费使用单位")
    delivery_numbers = StringField("提运单号")
    contract_id = StringField("合同协议号")
    entry_clearance = StringField("进境关别")
    item_id = StringField("商品编号")
    item_name = StringField("商品名称")
    total_price = FloatField("总价")


class UploadImageForm(FlaskForm):
    file = FileField(
        "文件",
        validators=[
            FileRequired("必须上传文件"),
            FileAllowed(
                [
                    "jpg",
                    "png",
                ],
                "不允许上传此类文件",
            ),
        ],
    )


class TransferForm(FlaskForm):
    bop_no = StringField()
    trans_no = StringField()
    receiver = StringField()
    amount = FloatField()
    amount_fx = FloatField()
    remitter = StringField()
    unit_code = StringField()
    bene_bank_no = StringField()
    bene_bank = StringField()
    rate = FloatField()
    rmb_equ = FloatField()
    commission = FloatField()
    total_charge = FloatField()
    maker = StringField()
    checker = StringField()
