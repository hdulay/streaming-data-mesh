# save this as app.py
from flask import Flask, request
import json
import sys
# setting path
sys.path.append('..')
from modules.rest_helper import *
from modules.helper import *
from modules.models import *

app = Flask(__name__)

@app.get("/")
def desc():
    return {
        "app":"domain agent"
    }

@app.post('/cluster-link')
def link():
    data = json.loads(request.data)
    destination_cluster_id = data['destination_cluster_id']
    link_name = data['link_name']
    cl_config = data['config']

    profile, config = get_config()

    destination_kafka = config['profiles'][profile]['kafka'][destination_cluster_id]

    cluster_id = json.loads(
        get(f"{destination_kafka['bootstrap.servers']}/v3/clusters?link_name={link_name}")
    )['data']['cluster_id']

    # data = {
    #     "source_cluster_id": source_cluster_id,
    #     "configs": [
    #         {
    #             "name": "bootstrap.servers",
    #             "value": "cluster-1-bootstrap-server"
    #         },
    #         {
    #             "name": "acl.sync.enable",
    #             "value": "false"
    #         },
    #         {
    #             "name": "consumer.offset.sync.ms",
    #             "value": "30000"
    #         }
    #     ]
    # }
    
    post(f"/clusters/{cluster_id}/links", data=cl_config)

