
alias sdm="./cli/sdm.py"

# init:
# 	python -m venv env
# 	astrocloud dev init

# doc:
# 	ag kafka-pubsub.yaml https://github.com/hdulay/html-template/tree/datamesh -o code/asyncapi/output-kafka-pubsub --force-write

# spring:
# 	ag code/asyncapi/kafka-pubsub.yaml @asyncapi/java-spring-template --force-write -o asyncapi/java

cp:
	cd confluent; docker compose -f docker-compose.yaml up -d

control.plane:
	cd control-plane; flask --debug run -p 7000

openlineage:
	cd marquez/; docker/up.sh --api-port 7002

apicurio:
	docker run -it -p 8080:8080 apicurio/apicurio-registry-mem:2.3.1.Final

onprem:
	make -j apicurio
	make -j control.plane
	make -j cp
	make -j openlineage

kill.all:
	-docker kill $(shell docker ps -q)
	docker system prune

flow:
	make cdc DB=postgresql
	echo "waiting 30 sec for connect cluster to restart"
	sleep 30
	make datagen DATA=clickstream
	make create.postgres
	echo "waiting 20 sec debezium to create topics"
	sleep 20
	make user.table
	echo "waiting 5 sec"
	sleep 5
	make join

cdc:
	./cli/sdm.py connect add debezium/debezium-connector-$(DB):1.9.3

create.postgres:
	./cli/sdm.py connect connector add users connect/debezium.json 

# list.plugins:
# 	./cli/sdm.py connect plugins connect  | jq

datagen:
	./cli/sdm.py connect connector add ${DATA} connect/${DATA}.json 

# create.product:
# 	./cli/sdm.py streaming sql add ./sql/create_product_stream.sql 

user.table:
	./cli/sdm.py streaming sql add ./confluent/ksql/users_materialized.sql 

join:
	./cli/sdm.py streaming sql add ./confluent/ksql/join.sql 


publish:
	./cli/sdm.py streaming publish CLICK_USERS


start.pulsar:
	curl -X POST http://localhost:3000/api/v1/lineage \
		-H 'Content-Type: application/json' \
		-d '@sample/start-pulsar.json'

complete.pulsar:
	curl -X POST http://localhost:3000/api/v1/lineage \
		-H 'Content-Type: application/json' \
		-d '@sample/complete-pulsar.json'

pulsar: start.pulsar complete.pulsar


start.postgres:
	curl -X POST http://localhost:3000/api/v1/lineage \
		-H 'Content-Type: application/json' \
		-d '@sample/start-pg-cdc.json'

complete.postgres:
	curl -X POST http://localhost:3000/api/v1/lineage \
		-H 'Content-Type: application/json' \
		-d '@sample/complete-pg-cdc.json'

postgres: start.postgres complete.postgres

start.join:
	curl -X POST http://localhost:3000/api/v1/lineage \
		-H 'Content-Type: application/json' \
		-d '@sample/start-join.json'

complete.join:
	curl -X POST http://localhost:3000/api/v1/lineage \
		-H 'Content-Type: application/json' \
		-d '@sample/complete-join.json'

join2: start.join complete.join

start.replicate:
	curl -X POST http://localhost:3000/api/v1/lineage \
		-H 'Content-Type: application/json' \
		-d '@sample/start-replicate.json'

complete.replicate:
	curl -X POST http://localhost:3000/api/v1/lineage \
		-H 'Content-Type: application/json' \
		-d '@sample/complete-replicate.json'

replicate: start.replicate complete.replicate
