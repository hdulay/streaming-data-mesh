import json
import typer

from ksql import KSQLAPI
from modules.models import Field
from modules.openlineage_help import DatasetHelper
from modules.schema_helper import SchemaHelper
from modules.openlineage_help import OpenLineage, TopicDataset
from modules.rest_helper import *
from modules.helpers import Helpers
import apicurioregistryclient
from apicurioregistryclient.api import artifacts_api
from apicurioregistryclient.model.if_exists import IfExists
from apicurioregistryclient.model.artifact_type import ArtifactType
from apicurioregistryclient.model.configuration_property import ConfigurationProperty
from apicurioregistryclient.model.error import Error
from apicurioregistryclient.model.log_configuration import LogConfiguration
from apicurioregistryclient.model.named_log_configuration import NamedLogConfiguration
from apicurioregistryclient.model.role_mapping import RoleMapping
from apicurioregistryclient.model.rule import Rule
from apicurioregistryclient.model.rule_type import RuleType
from apicurioregistryclient.model.update_configuration_property import UpdateConfigurationProperty
from apicurioregistryclient.model.update_role import UpdateRole

app = typer.Typer()


@app.command()
def list():
    """
    Lists all the domains in the data mesh
    """
    typer.echo(f"listing all domains")


@app.command()
def describe(domain_id: str):
    """
    Describes a domain including location, owners, and published data products and ids
    """
    typer.echo(f"describing item: {domain_id}")

@app.command()
def request(domain_id: str, data_product: str):
    """
    Requests access to a data product by the current (your) domain.
    """
    profile, config = Helpers.get_config()
    p = config['profiles'][profile]['prop']
    client = KSQLAPI(f"http://{p['ksql']['rest']}")
    desc = client.ksql(f'describe {data_product} extended')[0]

@app.command()
def link(domain_id:str, data_product:str):
    cl_resp, cluster_id = create_link(domain_id=domain_id)
    mirror_resp = mirror_topic(
        data_product=data_product, 
        domain_id=domain_id, 
        cluster_id=cluster_id)

    results = {
        "link": cl_resp,
        "mirror": mirror_resp
    }
    typer.echo(results)


def mirror_topic(data_product:str, domain_id:str, cluster_id:str):
    profile, config = Helpers.get_config()
    # Enter a context with an instance of the API client
    # configuration = apicurioregistryclient.Configuration(
    #     host = config['apicurio']
    # )
    # with apicurioregistryclient.ApiClient(configuration) as api_client:
    #     api_instance = artifacts_api.ArtifactsApi(api_client)
        
    #     try:
    #         search_response = api_instance.search_artifacts(name=data_product)
    #         # api_response = api_instance.create_artifact(
    #         #     group_id=profile, 
    #         #     body=yaml,
    #         #     x_registry_artifact_id=desc['sourceDescription']['topic'],
    #         #     if_exists=IfExists("RETURN_OR_UPDATE"),
    #         #     _content_type="application/x-yaml",
    #         #     x_registry_artifact_type=ArtifactType("ASYNCAPI"))
    #         typer.echo(search_response)
    #     except apicurioregistryclient.ApiException as e:
    #         print("Exception: %s\n" % e)
    

    data = {
        "source_topic_name": f"{data_product}",
        "configs": [
            {
                "name": "unclean.leader.election.enable",
                "value": "true"
            }
        ],
        "replication_factor": 1
    }
    headers = {"Content-Type": "application/json; charset=utf-8"}
    link_name = f"{domain_id}_{profile}"
    rest_proxy = config['profiles'][profile]['prop']['kafka']['rest.proxy']
    mirror_resp = post(url=f"http://{rest_proxy}/v3/clusters/{cluster_id}/links/{link_name}/mirrors",
        data=data,
        headers=headers)

    topic = data_product
    ol = OpenLineage(profile=profile, sdm_config=config)
    run = ol.get_run(facet={
        "name":f"link.{link_name}",
        "type":"source",
        "mirror":mirror_resp
    })
    job = ol.get_job(namespace=profile, name=link_name, facets={
        "name":f"link.{link_name}",
        "type":"source",
        "mirror":mirror_resp
    })

    fields = get_fields_from_apicurio(config['apicurio'], topic)
    
    src_facet = DatasetHelper.get_facet(fields=fields)

    src_topic_dataset:TopicDataset = TopicDataset(topic=topic, namespace=domain_id, name=f"topic.{topic}", facets=src_facet)
    dst_topic_dataset:TopicDataset = TopicDataset(topic=topic, namespace=profile, name=f"topic.{topic}", facets=src_facet)
    ol_response = ol.emit_run(inputs=[src_topic_dataset], outputs=[dst_topic_dataset], job=job, run=run)

    print(ol_response)
    
def get_fields_from_apicurio(apicurio_host:str, topic:str):
    # Enter a context with an instance of the API client
    configuration = apicurioregistryclient.Configuration(
        host = apicurio_host
    )
    with apicurioregistryclient.ApiClient(configuration) as api_client:
        api_instance = artifacts_api.ArtifactsApi(api_client)
        try:
            api_response = api_instance.get_content_by_global_id(
                global_id=1)
            data = json.loads(api_response.raw.read())
            props = data['components']['schemas'][topic]['properties']
            fields = [ { "name":k, "type":props[k]['type']} for k in props.keys()]
            typer.echo(fields)
            return fields
        except apicurioregistryclient.ApiException as e:
            print("Exception: %s\n" % e)
            raise e

def create_link(domain_id:str):
    profile, config = Helpers.get_config()
    rest_proxy = config['profiles'][profile]['prop']['kafka']['rest.proxy']
    cluster_id = json.loads(get(f'http://{rest_proxy}/v3/clusters').text)['data'][0]['cluster_id']
    control_plane_url = config['url']
    source_config = json.loads(get(f'{control_plane_url}/{domain_id}').text)
    source_clusters = json.loads(get(f"http://{source_config['prop']['kafka']['rest.proxy']}/v3/clusters").text)
    source_cluster_id = source_clusters['data'][0]['cluster_id']
    data = {
        "source_cluster_id": f"{source_cluster_id}",
        "configs": [
            {
                "name": "bootstrap.servers",
                "value": f"{source_config['prop']['kafka']['bootstrap.servers']}"
            },
            {
                "name": "acl.sync.enable",
                "value": "false"
            },
            {
                "name": "consumer.offset.sync.ms",
                "value": "30000"
            }
        ]
    }
    link_name = f"{domain_id}_{profile}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    rest_proxy = config['profiles'][profile]['prop']['kafka']['rest.proxy']
    create_resp = post(url=f'http://{rest_proxy}/v3/clusters/{cluster_id}/links?link_name={link_name}',
                        data=data,
                        headers=headers)
    return (create_resp, cluster_id)


if __name__ == "__main__":
    app()
