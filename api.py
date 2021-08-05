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

from flask import Flask
from flask-
import config
import models

api = FastAPI()
api.add_middleware(CORSMiddleware, **{
    'allow_origins': config.ORIGINS,
    'allow_credentials': True,
    'allow_methods': ['*'],
    'allow_headers': ['*']
})


# @api.middleware('http')
# async def check_p2p(req: Request, call_next):
#     req.query_params.keys()
#     if 'cid' in req.query_params.keys():
#         # P2P模式
#         client_id = req.query_params.get('cid')
#         client = models.clients[client_id]
#         if isinstance(client, (models.Client,)):
#             #  clientID有效
#             # params = req.query_params.__dict__
#             # params['client'] = client
#             # req.query_params = params
#             rep = await call_next(client, req)
#             print(rep)
#             return rep
#     else:
#         rep = await call_next(req)
#         return rep


@api.get('/')
def index(req: Request):
    return {
        'msg': 'Welcome to SwiftNext!',
        'ip': req.client.host
    }


"""
 | Part.1    /client         客户端类API
    | 1.1    /client/new     申请一个新的client
"""


@api.get('/client/new')
def clientNew() -> dict:
    return {
        'client_id': models.clients.create_new_client().client_id
    }


"""
    | 1.2    /client/login   申请登录状态
"""


@api.post('/client/login')
def clientLogin(login_user: models.LoginUser, client: models._Client = Query(None)):
    print(f'{client.client.client_id} 尝试登录!')
    print(login_user.dict())
    return {
        'success': True
    }
