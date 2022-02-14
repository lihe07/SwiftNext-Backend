"""
数据模型
"""
from sanic import json

def echo(a):
    return a

def to_response(sth):
    return json(sth.to_json(), dumps=echo)