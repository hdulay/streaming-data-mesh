# save this as app.py
from flask import Flask, request
import os
import sys
from helpers import Helpers
root_folder = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_folder)
import json
from peewee import *
from playhouse.shortcuts import model_to_dict
import datetime


db = SqliteDatabase('cp.db')

class BaseModel(Model):
    class Meta:
        database = db

class Access_Request(BaseModel):
    domain_requestor = CharField(unique=True)
    domain_dp_owner = CharField(unique=True)
    data_product_id = IntegerField(unique=True)
    approved = BooleanField()

is_conn = db.connect()
db.create_tables([Access_Request])

app = Flask(__name__)

@app.get("/")
def desc():
    return {
        "app":"self-services for domains"
    }

@app.post('/login')
def login():
    data = request.data
    print(data.decode('utf8'))
    config = Config(data.decode('utf8'))
    return json.dumps(config, cls=Encoder)

@app.post('/request/<domain_requestor>/<domain_owner>/<data_product_id>')
def request_dp(domain_requestor:str, domain_owner:str, data_product_id:int):
    ar = Access_Request.create(approved=False, 
        domain_requestor=domain_requestor, 
        domain_dp_owner=domain_owner, 
        data_product_id=data_product_id)
    return json.dumps(model_to_dict(ar))

@app.post('/request/<id>/<approved>')
def approve(id:int, approved:bool=False):
    ar:Access_Request = Access_Request.get_by_id(pk=id)
    ar.approved = approved
    ar.save()
    return json.dumps(model_to_dict(ar))

@app.get("/requests")
def get_requests():
    query = Access_Request.select()
    return json.dumps([model_to_dict(r) for r in query])

@app.delete('/request/<id>')
def delete_request(id:int):
    Access_Request.delete_by_id(pk=id)
    return "success"

@app.get("/<domain>")
def get_domain(domain:str):
    profile, config = Helpers.get_config()
    return json.dumps(config['profiles'][domain])
