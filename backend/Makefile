# Global targets
all: dependencies docker test
test: taskmanager-test downloadworker-test snowflake-test # test is for unit code tests
dependencies: taskmanager-dependencies downloadworker-dependencies
build: taskmanager-docker downloadworker-docker analysisworker-docker
check: cassandra-check # check is for checks at runtime
run: 
	docker-compose up
development:
	docker-compose up --build

# taskmanager targets
taskmanager: taskmanager-dependencies taskmanager-run
taskmanager-dependencies:
	$(MAKE) -C taskmanager dependencies
taskmanager-test:
	$(MAKE) -C taskmanager test
taskmanager-docker:
	$(MAKE) -C taskmanager docker
taskmanager-run:
	docker-compose up --build taskmanager

# downloadworker targets
downloadworker: downloadworker-dependencies downloadworker-run
downloadworker-clean:
	$(MAKE) -C downloadworker clean
downloadworker-dependencies:
	$(MAKE) -C downloadworker dependencies
downloadworker-test:
	$(MAKE) -C downloadworker test
downloadworker-docker:
	$(MAKE) -C downloadworker docker
downloadworker-run: downloadworker-dependencies
	docker-compose up --build --scale downloadworker=20 downloadworker

# analysisworker targets
analysisworker: analysisworker-run
analysisworker-docker:
	$(MAKE) -C analysisworker docker
analysisworker-run:
	docker-compose up --build analysisworker

credentialsmanager: credentialsmanager-run
credentialsmanager-docker:
	$(MAKE) -C credentialsmanager docker
credentialsmanager-run:
	docker-compose up --build credentialsmanager

# streamworker targets
streamworker: streamworker-run
streamworker-run:
	docker-compose up --build --scale streamworker=4 streamworker

# utils targets
snowflake: snowflake-test
snowflake-test:
	$(MAKE) -C snowflake test

# thirdparty services
cassandra-check:
	docker exec backend_cassandra_1 /opt/bitnami/cassandra/bin/nodetool status
cassandra-run:
	docker-compose up cassandra
cassandra-tablestatus:
	docker exec backend_cassandra_1 nodetool cfstats | sed -n -e '/Keyspace : twitter/,/----------------/ p'

rabbitmq-run:
	docker-compose up rabbitmq

redis-run:
	docker-compose up redis

push-to-server:
	rsync -rhv . firehose:/home/firehose/backend
push-to-server2:
	rsync -rhv . firehose2:/home/firehose2/backend