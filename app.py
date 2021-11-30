# encoding utf-8
from pathlib import Path
from datetime import timedelta
import easyocr
import hashlib
import json
from flask import Flask, render_template, redirect, url_for, flash, jsonify
from playhouse.flask_utils import get_object_or_404
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from utils import (
    secure_filename,
    get_tpl_data,
    get_tpl_data_export,
    get_chain,
    update_chain,
    insert_chain,
    get_tx_count,
    bar_base,
    get_block_info,
)
from forms import LoginForm, UploadImageForm, CustomForm, TransferForm
from models import User, Customs, flask_db, Transfer

THIS_FILE = Path(__file__).resolve()
THIS_DIR = THIS_FILE.parent
UPLOADS_DIR = THIS_DIR.joinpath("static", "uploads")

app = Flask(__name__)
app.config["DATABASE"] = "mysql://root:1@192.168.50.154:3306/test"
app.config["SECRET_KEY"] = "12345"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(seconds=1)
# 设置静态文件缓存过期时间
app.send_file_max_age_default = timedelta(seconds=1)

flask_db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = ""
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    """加载当前登录用信息
    :param user_id 数据库中银行柜员id
    """
    user = User.get(user_id == User.id)
    return user


@app.route("/", methods=["POST", "GET"])
def login():
    """登录视图
    LoginForm接受用户名和密码
    :param 无
    """
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        try:
            user = User.get(User.username == username)
        except User.DoesNotExist:
            flash("用户名或密码错误。", category="error")
            return render_template("login.html", form=form)

        if user.check(password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("用户名或密码错误。", category="error")
            return render_template("login.html", form=form)

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    """账号登出
    :param 无
    """
    logout_user()
    return redirect(url_for("login"))


@app.route("/upload", methods=["POST", "GET"])
@login_required
def upload():
    """上传进口付汇报关单视图
    设置图片名称，保存用户上传的进口付汇报关单
    :param 无
    """
    form = UploadImageForm()
    if form.validate_on_submit():
        file = form.file.data
        _, filename = secure_filename(file)
        save_file = UPLOADS_DIR.joinpath(filename)
        file.save(str(save_file))

        return redirect(url_for("ocr", img=filename))

    return render_template("upload.html", form=form)


@app.route("/upload/export", methods=["POST", "GET"])
@login_required
def upload_export():
    """上传出口收汇报关单视图
    设置图片名称，保存用户上传的出口收汇报关单
    :param 无
    """
    form = UploadImageForm()
    if form.validate_on_submit():
        file = form.file.data
        _, filename = secure_filename(file)
        save_file = UPLOADS_DIR.joinpath(filename)
        file.save(str(save_file))

        return redirect(url_for("ocr_export", img=filename))

    return render_template("upload_export.html", form=form)


@app.route("/ocr/<img>", methods=("GET", "POST"))
@login_required
def ocr(img):
    """OCR识别视图
    进口付汇报关单OCR识别，CustomForm接受报关单信息，custom存入数据库
    :param img 图片路径
    """
    form = CustomForm()
    if form.validate_on_submit():
        try:
            customs = Customs.get(Customs.cus_id == form.cus_id.data)
        except Customs.DoesNotExist:
            customs = Customs(
                cus_id=form.cus_id.data,
                receiver=form.receiver.data,
                sender=form.sender.data,
                consumer_unit=form.consumer_unit.data,
                delivery_numbers=form.delivery_numbers.data,
                contract_id=form.contract_id.data,
                entry_clearance=form.entry_clearance.data,
                item_id=form.item_id.data,
                item_name=form.item_name.data,
                total_price=form.total_price.data,
                surplus=form.total_price.data,
                contract_type="进口",
            )
            customs.save()
        return redirect(url_for("transfer", cus_id=customs.id))
    return render_template("ocr.html", img=img, form=form)


@app.route("/ocr/export/<img>", methods=("GET", "POST"))
@login_required
def ocr_export(img):
    """OCR识别视图
    出口收汇报关单OCR识别，CustomForm接受报关单信息，custom存入数据库
    :param img 图片路径
    """
    form = CustomForm()
    if form.validate_on_submit():
        try:
            customs = Customs.get(Customs.cus_id == form.cus_id.data)
        except Customs.DoesNotExist:
            customs = Customs(
                cus_id=form.cus_id.data,
                receiver=form.receiver.data,
                sender=form.sender.data,
                consumer_unit=form.consumer_unit.data,
                delivery_numbers=form.delivery_numbers.data,
                contract_id=form.contract_id.data,
                entry_clearance=form.entry_clearance.data,
                item_id=form.item_id.data,
                item_name=form.item_name.data,
                total_price=form.total_price.data,
                surplus=form.total_price.data,
                contract_type="出口",
            )
            customs.save()
        return redirect(url_for("transfer_export", cus_id=customs.id))
    return render_template("ocr_export.html", img=img, form=form)


@app.route("/api/ocr/<img>")
@login_required
def api_ocr(img):
    """区块链校验
    返回json数据类型的识别文本
    :param img 图片路径
    """
    img_file = UPLOADS_DIR.joinpath(img)
    reader = easyocr.Reader(["ch_sim", "en"])
    result = reader.readtext(str(img_file), detail=0)
    head = [
        "cus_id",
        "receiver",
        "sender",
        "consumer_unit",
        "delivery_numbers",
        "contract_id",
        "entry_clearance",
        "item_id",
        "item_name",
        "total_price",
    ]
    content = [
        result[3].split(":")[1].strip(),
        result[10],
        result[19],
        result[10],
        result[22],
        "",
        result[11],
        result[72],
        result[73],
        result[75],
    ]
    ret = dict(zip(head, content))
    return jsonify(ret)


@app.route("/api/ocr/export/<img>")
@login_required
def api_ocr_export(img):
    """区块链校验
    返回json数据类型的识别文本
    :param img 图片路径
    """
    img_file = UPLOADS_DIR.joinpath(img)
    reader = easyocr.Reader(["ch_sim", "en"])
    result = reader.readtext(str(img_file), detail=0)
    head = [
        "cus_id",
        "receiver",
        "sender",
        "consumer_unit",
        "delivery_numbers",
        "contract_id",
        "entry_clearance",
        "item_id",
        "item_name",
        "total_price",
    ]
    content = [
        result[3].split(":")[1].strip(),
        result[17],
        result[10],
        result[10],
        result[20],
        result[34],
        result[11],
        result[66],
        result[67],
        float(result[75]),
    ]
    ret = dict(zip(head, content))
    return jsonify(ret)


@app.route("/api/tpl")
@login_required
def api_tpl():
    """链上信息获取
    返回区块链上数据
    :param 无
    """
    filepath = "plannerManifest/434/submitData_434.json"
    tpl_data = get_tpl_data(filepath)
    return jsonify(tpl_data)


@app.route("/api/tpl/export")
@login_required
def api_tpl_export():
    """链上信息获取
    返回区块链上数据
    :param 无
    """
    filepath = "plannerManifest/437/submitData_437.json"
    tpl_data = get_tpl_data_export(filepath)
    return jsonify(tpl_data)


@app.route("/transfer/<int:cus_id>", methods=("GET", "POST"))
@login_required
def transfer(cus_id):
    """填写付汇申请视图
    用户填写付汇申请
    :param cus_id 付汇报关单id
    """
    form = TransferForm()
    custom = get_object_or_404(Customs, (Customs.id == cus_id))
    print(custom.surplus)
    if form.validate_on_submit() and custom.surplus >= form.rmb_equ.data:
        transfer = Transfer(
            cus_id=cus_id,
            bop_no=form.bop_no.data,
            trans_no=form.trans_no.data,
            receiver=form.receiver.data,
            amount=form.amount.data,
            amount_fx=form.amount_fx.data,
            remitter=form.remitter.data,
            unit_code=form.unit_code.data,
            bene_bank_no=form.bene_bank_no.data,
            bene_bank=form.bene_bank.data,
            rate=form.rate.data,
            rmb_equ=form.rmb_equ.data,
            commission=form.commission.data,
            total_charge=form.total_charge.data,
            maker=form.maker.data,
            checker=form.checker.data,
        )
        transfer.save()
        custom.surplus = custom.surplus - form.rmb_equ.data
        custom.save()
        transfer_json = {
            "id": transfer.id,
            "cus_id": cus_id,
            "bop_no": transfer.bop_no,
            "trans_no": transfer.trans_no,
            "receiver": transfer.receiver,
            "amount": transfer.amount,
            "amount_fx": transfer.amount_fx,
            "remitter": transfer.remitter,
            "unit_code": transfer.unit_code,
            "bene_bank_no": transfer.bene_bank_no,
            "bene_bank": transfer.bene_bank,
            "rate": transfer.rate,
            "rmb_equ": transfer.rmb_equ,
            "commission": transfer.commission,
            "total_charge": transfer.total_charge,
            "maker": transfer.maker,
            "checker": transfer.checker,
        }

        ret1 = insert_chain(transfer_json)
        transfer.block_number = ret1["block_number"]
        transfer.block_hash = ret1["block_hash"]
        transfer.tx_id = ret1["tx_id"]
        transfer.save()

        return redirect(url_for("transfer_list", cus_id=cus_id))
    return render_template("transfer.html", form=form, cus_id=cus_id)
    # return "余额不足"


@app.route("/list/custom")
@login_required
def list_custom():
    """报关单视图
    查看所有报关单
    :param 无
    """
    customs = Customs.select()
    return render_template("list_custom.html", customs=customs)


@app.route("/list/<int:cus_id>")
@login_required
def transfer_list(cus_id):
    """付汇详情视图
    查看报关单对应的所有付汇记录
    :param cus_id 报关单id
    """
    transfers = (
        Transfer.select().where(Transfer.cus_id == cus_id).order_by(Transfer.dt.desc())
    )
    custom = get_object_or_404(Customs, (Customs.id == cus_id))
    return render_template("list.html", transfers=transfers, custom=custom)


@app.route("/api/verify/<int:trans_id>")
@login_required
def api_verify(trans_id):
    """付汇校验
    返回链上存储的信息转为字符串，对字符串进行HASH
    对数据库的信息进行HASH比对
    :param trans_id 付汇申请单id
    """
    transfer = get_object_or_404(Transfer, (Transfer.id == trans_id))
    returned = get_chain(trans_id)
    returned = json.dumps(returned)
    returned_sha = hashlib.sha3_256(returned.encode("utf-8")).hexdigest()
    transfer_json = {
        "id": transfer.id,
        "cus_id": transfer.cus_id.id,
        "bop_no": transfer.bop_no,
        "trans_no": transfer.trans_no,
        "receiver": transfer.receiver,
        "amount": transfer.amount,
        "amount_fx": transfer.amount_fx,
        "remitter": transfer.remitter,
        "unit_code": transfer.unit_code,
        "bene_bank_no": transfer.bene_bank_no,
        "bene_bank": transfer.bene_bank,
        "rate": transfer.rate,
        "rmb_equ": transfer.rmb_equ,
        "commission": transfer.commission,
        "total_charge": transfer.total_charge,
        "maker": transfer.maker,
        "checker": transfer.checker,
    }
    transfer_json = json.dumps(transfer_json)
    transfer_json_sha = hashlib.sha3_256(transfer_json.encode("utf-8")).hexdigest()
    verify_ret = {"status": returned_sha == transfer_json_sha}
    return jsonify(verify_ret)


@app.route("/api/bc_info/<int:trans_id>")
@login_required
def api_bc_info(trans_id):
    transfer = get_object_or_404(Transfer, (Transfer.id == trans_id))
    ret = {
        "block_number": transfer.block_number,
        "block_hash": transfer.block_hash,
        "tx_id": transfer.tx_id,
    }
    return jsonify(ret)


@app.route("/view")
def index():
    """BSN可视化首页
    :param 无
    """
    tx_sum = get_tx_count()
    block_number = tx_sum + 1
    data = []
    for i in range(tx_sum, tx_sum - 15, -1):
        dic = get_block_info(i)
        data.append(dic)

    return render_template(
        "view.html", tx_sum=tx_sum, block_number=block_number, data=data
    )


@app.route("/Chart")
def get_bar_chart():
    """BSN可视化地图区域
    :param 无
    """
    c = bar_base()
    return c.dump_options_with_quotes()


@app.route("/create")
def create_tables():
    db = flask_db.database
    with db:
        db.create_tables([Transfer])
    return "create tables done"


@app.route("/transfer/detail/<int:id>", methods=["GET"])
def transfer_detail(id):
    transfer = get_object_or_404(Transfer, (Transfer.id == id))
    return render_template("transfer_detail.html", transfer=transfer)


if __name__ == "__main__":
    app.run()
