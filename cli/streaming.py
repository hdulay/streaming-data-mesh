import typer
import sys
from jinja2 import Template
import udf
import SQL
from modules.helpers import Helpers
from ksql import KSQLAPI
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
app.add_typer(udf.app, name="udf", help="Tool to manage UDFs")
app.add_typer(SQL.app, name="sql", help="Tool to manage SQL statements")

@app.command()
def publish(stream_name:str, description:str=""):
    """
    Publishes an append/change stream or stream/table as a streaming data product
    """

    profile, config = Helpers.get_config()
    p = config['profiles'][profile]['prop']
    client = KSQLAPI(f"http://{p['ksql']['rest']}")
    desc = client.ksql(f'describe {stream_name} extended')[0]

    f = open("cli/templates/dp.ksqldb.j2", "r")
    t = Template(f.read())
    yaml = t.render(dp=desc, kafka=p['kafka'], profile=profile, config=config)
    typer.echo(yaml)

    # Enter a context with an instance of the API client
    configuration = apicurioregistryclient.Configuration(
        host = config['apicurio']
    )
    with apicurioregistryclient.ApiClient(configuration) as api_client:
        api_instance = artifacts_api.ArtifactsApi(api_client)
        try:
            api_response = api_instance.create_artifact(
                group_id=profile, 
                body=yaml,
                x_registry_artifact_id=desc['sourceDescription']['topic'],
                if_exists=IfExists("RETURN_OR_UPDATE"),
                _content_type="application/x-yaml",
                x_registry_artifact_type=ArtifactType("ASYNCAPI"))
            typer.echo(api_response)
        except apicurioregistryclient.ApiException as e:
            print("Exception: %s\n" % e)

@app.command()
def link(source_domain:str, data_product:str):
    pass