# -*- encoding: utf-8 -*-

# ========================================================================================================#
# |                                                                                                      |#
# |      >=>>=>                           >=>    >=>         >==>    >=>                       >=>       |#
# |    >=>    >=>                >>>    >>       >=>         >> >=>  >=>                       >=>       |#
# |     >=>        >=>      >=>       >=>>>>>  >=>>==>       >=> >=> >=>   >==>    >=>   >=> >=>>==>     |#
# |       >=>       >=>  >  >=>  >=>    >=>      >=>         >=>  >=>>=> >>   >=>    >> >=>    >=>       |#
# |          >=>    >=> >>  >=>  >=>    >=>      >=>         >=>   > >=> >>===>>=>    >>       >=>       |#
# |    >=>    >=>   >=>>  >=>=>  >=>    >=>      >=>         >=>    >>=> >>         >>  >=>    >=>       |#
# |      >=>>=>    >==>    >==>  >=>    >=>       >=>        >=>     >=>  >====>   >=>   >=>    >=>      |#
# |                                                                                                      |#
# |           ___   ___  __                                                ____          _ _ _           |#
# |          / _ \ / _ \/_ |                                              |  _ \        | (_| |          |#
# |   __   _| | | | | | || |                                              | |_) |_   _  | |_| |__   ___  |#
# |   \ \ / | | | | | | || |                                              |  _ <| | | | | | | '_ \ / _ \ |#
# |    \ V /| |_| | |_| _| |                                              | |_) | |_| | | | | | | |  __/ |#
# |     \_/  \___(_\___(_|_||                                             |____/ \__, | |_|_|_| |_|\___| |#
# |                                                                               __/ |                  |#
# |                                                                              |___/                   |#
# |                                                                                                      |#
# ========================================================================================================#
import json

import werkzeug.exceptions
from flask import Flask, request
from flask_cors import CORS
from flask_restful import Api, Resource
from urllib.parse import parse_qs
import config
import models
import utils
from icecream import ic

app = Flask(__name__)
CORS(app, origins=config.ORIGINS)
api = Api(app)


def p2p(call):
    def inner(*args):
        qs = parse_qs(request.query_string)
        qs = {k.decode(): v[0].decode() for k, v in qs.items()}
        if 'cid' in qs.keys():
            client = models.clients[qs['cid']]
            if isinstance(client, (models.Client,)):
                data = json.dumps(call(client, *args))
                data = client.encrypt_data(data)
                return {
                    'encrypted': True,
                    'data': data
                }
        # client 不合法
        raise models.ClientInvalid

    return inner


@app.after_request
def basic_api(rep):
    if isinstance(rep, (str,)):
        return rep
    else:
        try:
            return json.dumps(rep)
        except TypeError:
            raise models.ServerDataParsingError


@app.errorhandler(werkzeug.exceptions.HTTPException)
def errorhandler(err):
    """
    错误包装器 返回一个json的错误报告
    :param err: 错误
    :return: json报告
    """
    response = err.get_response()
    if hasattr(err, 'error'):
        response.data = json.dumps({
            'code': err.code,
            'description': err.description,
            'error': err.error
        })
    else:
        response.data = json.dumps({
            'code': err.code,
            'description': err.description,
        })
    response.content_type = "application/json"
    return response


class HelloWorld(Resource):
    def get(self) -> dict:
        return {
            'msg': 'Welcome to SwiftNext!',
            'ip': request.remote_addr
        }


api.add_resource(HelloWorld, '/')

"""
 | Part.1    /client         客户端类API
    | 1.1    /client     申请一个新的client
"""


class Client(Resource):
    def get(self) -> dict:
        return {
            'client_id': models.clients.create_new_client().client_id
        }


api.add_resource(Client, '/client')

"""
    | 1.2    /client/login   申请登录状态
"""


@app.route('/client/login', methods=['POST'])
@p2p
def clientLogin(client: models.Client):
    ic(request.form, request.data, request.get_data())
    # login_user = utils.parse_request_data(models.LoginUser, request.form)
    print(f'{client.client_id} 尝试登录!')
    return {
        'success': True
    }
