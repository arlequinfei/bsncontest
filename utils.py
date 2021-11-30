import uuid
import json
from pathlib import Path
import requests
from datetime import datetime
from pathvalidate import sanitize_filename
from pyecharts import options as opts
from pyecharts.globals import ChartType, SymbolType
from pyecharts.charts import Geo


BSN_URL = "http://192.168.50.98:8888"


def secure_filename(file):
    filename = sanitize_filename(file.filename)
    extension = Path(file.filename).suffix.lower()
    uid = str(uuid.uuid4())
    unique_filename = f"{uid}{extension}"
    return filename, unique_filename


def get_tpl_data(filepath):
    """从生产环境区块链读取贸易数据
    :param filepath 生产环境区块链存证路径
    """
    auth_url = "https://blockchain2021.swfu.edu.cn/api/auth/oauth2/v1/token"
    # auth_url = "http://183.224.221.221:60041/oauth2/v1/token"
    tdp_url = "http://183.224.221.221:60041/tdps"

    client_id = "c3a97ac41fcd4ec89e991282d53a70af"
    org_id = "a45650e4-2ce2-44ea-b5d7-83845690a4fc"

    tdp_id = "0f307499499c478089f874edfe389957"
    network_id = "b45c98348c7a405299e7255056beea8d"
    ledger_id = "66e9c3f73c294449a566eb9f667593a2"
    api_url_prefix = f"tdp/{tdp_id}/network/{network_id}/ledger/{ledger_id}"

    data = {
        "client_id": client_id,
        "client_secret": "34SFHRV4cnhlVyyurVBt8wGnEc7SSXxRlgf1pTqQpRk=",
        "username": "KT2-baoguanhang",
        "grant_type": "trusted_delegation_login",
    }

    r = requests.post(auth_url, data=data)

    rj = r.json()
    access_token = rj["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "client_id": client_id,
        "org_id": org_id,
    }

    # file = "plannerManifest/437/submitData_437.json"
    file_url = f"{tdp_url}/{api_url_prefix}/v1.0/file/{filepath}"

    r = requests.get(file_url, headers=headers)
    content = r.json()["data"]["content"]
    content = json.loads(content)

    tpl_data = {
        "cus_id": "",
        "receiver": content["declBusinessName1"],
        "sender": content["declForeignContactsName"],
        "consumer_unit": content["declBusinessName1"],
        "delivery_numbers": content["declBlNo"],
        "contract_id": content["declContractNo"],
        "entry_clearance": content["declEntryCustCategory"],
        "item_id": content["goods"][0]["goodsSerial"],
        "item_name": content["goods"][0]["goodsName"],
        "total_price": content["goods"][0]["goodsTotalPrice"][:-3],
    }
    return tpl_data


def get_tpl_data_export(filepath):
    """从生产环境区块链读取贸易数据
    :param filepath 生产环境区块链存证路径
    """
    auth_url = "https://blockchain2021.swfu.edu.cn/api/auth/oauth2/v1/token"
    # auth_url = "http://183.224.221.221:60041/oauth2/v1/token"
    tdp_url = "http://183.224.221.221:60041/tdps"

    client_id = "c3a97ac41fcd4ec89e991282d53a70af"
    org_id = "a45650e4-2ce2-44ea-b5d7-83845690a4fc"

    tdp_id = "0f307499499c478089f874edfe389957"
    network_id = "b45c98348c7a405299e7255056beea8d"
    ledger_id = "66e9c3f73c294449a566eb9f667593a2"
    api_url_prefix = f"tdp/{tdp_id}/network/{network_id}/ledger/{ledger_id}"

    data = {
        "client_id": client_id,
        "client_secret": "34SFHRV4cnhlVyyurVBt8wGnEc7SSXxRlgf1pTqQpRk=",
        "username": "KT2-baoguanhang",
        "grant_type": "trusted_delegation_login",
    }

    r = requests.post(auth_url, data=data)

    rj = r.json()
    access_token = rj["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "client_id": client_id,
        "org_id": org_id,
    }

    # file = "plannerManifest/437/submitData_437.json"
    file_url = f"{tdp_url}/{api_url_prefix}/v1.0/file/{filepath}"

    r = requests.get(file_url, headers=headers)
    content = r.json()["data"]["content"]
    content = json.loads(content)

    tpl_data = {
        "cus_id": "",
        "receiver": content["declForeignContactsName"],
        "sender": content["declBusinessName4"],
        "consumer_unit": content["declBusinessName4"],
        "delivery_numbers": content["declBlNo"],
        "contract_id": content["declContractNo"],
        "entry_clearance": content["declExitCustCategory"],
        "item_id": content["goods"][0]["goodsSerial"],
        "item_name": content["goods"][0]["goodsName"],
        "total_price": float(content["goods"][0]["goodsTotalPrice"]),
    }
    return tpl_data


def get_chain(ID):
    """获取信息
        :param ID 序列号
    """
    url = f"{BSN_URL}/api/chain/getChainInfo?key=" + str(ID)
    response = requests.get(url=url)
    # print(response.text)
    data = response.json()["data"]["queryInfo"]
    # data = data[0]
    data = json.loads(data)
    data = data[0]
    data = json.loads(data)
    return data


def insert_chain(value):
    """往区块链插入信息
        :param value 信息
    """
    ID = value["id"]
    value = json.dumps(value)
    payload = []
    payload.append(ID)
    payload.append(value)
    url = f"{BSN_URL}/api/chain/saveChain"
    payload = json.dumps(payload)
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    res = response.json()
    data = res["data"]
    data["block_number"] = int(data["block_number"])
    # print(data)
    return data


def update_chain(ID, value):
    """更新区块链信息
        :param ID 序号
        :param value 信息
    """
    value = json.dumps(value)
    payload = []
    payload.append(ID)
    payload.append(value)
    url = f"{BSN_URL}/api/chain/updateChain"
    payload = json.dumps(payload)
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    res = response.json()
    data = res["data"]
    data["block_number"] = int(data["block_number"])
    # print(data)
    return data


def get_tx_count():
    """获取交易信息
        :param 无
    """
    url = f"{BSN_URL}/api/chain/getTxCount"

    response = requests.request("GET", url)

    res = response.json()
    data = res["data"]["data"]
    dic_data = json.loads(data)
    tx_sum = dic_data["txSum"]
    # tx_sum = 2
    # print(tx_sum)

    return tx_sum


def get_block_info(key):
    """获取块内信息
        :param key 块号
    """
    url = f"{BSN_URL}/api/chain/getBlockInfo?key=" + str(key)

    response = requests.request("GET", url=url)

    res = response.json()
    transactions = res["data"]["transactions"]
    dic_data = json.loads(transactions)
    tx_id = dic_data[0]["txId"]
    timestamp = int(res["data"]["blockTime"])
    # print(timestamp)

    timestamp = datetime.fromtimestamp(timestamp / 1000)
    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    dic = {}
    dic["tx_id"] = tx_id
    dic["timestamp"] = timestamp
    return dic


def bar_base():
    """可视化视图
        c为构造的图片
        :param 无
    """
    c = (
        Geo(init_opts=opts.InitOpts())
        .add_schema(maptype="china")
        .add(
            "",
            [("石家庄", 1000), ("青岛", 1000), ("西安", 1000)],
            type_=ChartType.EFFECT_SCATTER,
            color="#031D6B",
        )
        .add(
            "",
            [
                ("银川", 800),
                ("武汉", 800),
                ("杭州", 800),
                ("深圳", 800),
                ("沈阳", 800),
                ("杭州", 800),
                ("海口", 800),
            ],
            type_=ChartType.EFFECT_SCATTER,
            color="#00cccc",
        )
        .add(
            "",
            [("云南", 1000)],
            type_=ChartType.EFFECT_SCATTER,
            color="#f10075",
        )
        .add(
            "geo",
            [
                ("石家庄", "青岛"),
                ("青岛", "石家庄"),
                ("石家庄", "西安"),
                ("西安", "石家庄"),
                ("青岛", "西安"),
                ("西安", "青岛"),
            ],
            type_=ChartType.LINES,
            effect_opts=opts.EffectOpts(
                symbol=SymbolType.ARROW,
                symbol_size=8,
                color="#f10075",
                period=10,
                trail_length=0,
                is_show=True,
            ),
            linestyle_opts=opts.LineStyleOpts(
                curve=0.2, color="#f10075", width=1, opacity=0.8
            ),
        )
        .add(
            "geo",
            [("云南", "西安"), ("西安", "云南")],
            type_=ChartType.LINES,
            effect_opts=opts.EffectOpts(
                symbol=SymbolType.ARROW,
                symbol_size=8,
                color="#031D6B",
                period=10,
                trail_length=0,
                is_show=True,
            ),
            linestyle_opts=opts.LineStyleOpts(
                curve=0.3, color="#031D6B", width=1, opacity=0.8
            ),
        )
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(title_opts=opts.TitleOpts(title=" "))
        .set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
    )
    return c


if __name__ == "__main__":
    key = get_tx_count()
    get_block_info(key)
    # block_number = tx_sum + 1
    # data = []
    # for i in range(tx_sum, tx_sum - 12, -1):
    #     dic = get_block_info(i)
    #     data.append(dic)
    # update_chain(6669, {"id": 6669, "value": "hh"})
