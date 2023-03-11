import requests
import logging


log = logging.getLogger(__name__)

def post(url, data={}, headers={}):
    return requests.post(url, data=data, headers=headers)

def put(url, data={}, headers={}):
    return requests.put(url, data=data, headers=headers)

def get(url, headers={}):
    return requests.get(url, headers=headers)
