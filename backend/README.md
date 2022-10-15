# brandslang

[/ˈbrɑnt.slɑŋ/]

# Setup Server

1. Install docker:
   - `sudo apt-get update`
   - `sudo apt-get install ca-certificates curl gnupg lsb-release`
   - `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg`
   - ```bash
     echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
     ```
   - `sudo apt-get update`
   - `sudo apt-get install docker-ce docker-ce-cli containerd.io`
   - Test Installation: `sudo docker run hello-world`
   - If you want to use docker (i.e deploy the product) without sudo, also do the following:
   - `sudo groupadd docker`
   - `sudo usermod -aG docker $USER`
   - `newgrp docker`
   - Now, the hello-world example should run without sudo: `docker run hello-world`
2. Install docker-compose:
   - `sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`
   - `sudo chmod +x /usr/local/bin/docker-compose`
   - Check installation: `docker-compose --version`

# Install brandslang

1. Create twitter app in your dev account if you haven't done son already for the authentication webapp, take note of the credentials.

2. Duplicate the .env.example file into a .env file. Insert all necessary configuration strings into it. Btw, this file is listed in the gitignore.

3. Transfer code to server, you can use rsync or scp.

4. Run #############TODO:############# makefile command to copy python packages around.

5. Run `make development` in the brandslang-backend folder. Everything should spin up and connect, but since timeouts of workers waiting for other components to start can increase exponentially, it might be faster to start them in three steps:
  1. `docker-compose up -d rabbitmq redis cassandra`
  2. Inspect output of `make cassandra-check` and wait until it says "UN" (Up Normal) for all nodes (only one currently)
  3. `docker-compose up -d --scale streamworker=2 --scale downloadworker=4 analysisworker credentialsmanager streamworker downloadworker taskmanager` (You can adjust the replication factors to your liking).

# Troubleshooting:

- Components fail because other containers are not ready yet:

  - The services are built in a resilient way and should handle container outages swiftly. In most cases, they will retry several times before exiting completely. If you see error messages in the logs output, search for occurences of "xyz exited with code 1" and check the output of `docker ps`. if the container is still runnning, most likely everything works fine.
  - If not, you can restart single services by putting the service name behind the command, i.e.: `docker-compose up --build backend_downloadworker`
  - The order to start things is:

    1. rabbit, cassandra1, cassandra2, redis
    2. analysisworker, credentialsmanager
    3. streamworker, downloadworker, taskmanager

    Since the dependencies are:

    - analysisworker: redis, rabbit
    - credentialsmanager: redis
    - workers: rabbit, cassandra, credentialsmanager
    - taskmanager: rabbit, credentialsmanager

- Workers regulary fail because of cassandra timeouts:
  - Increase the threshold in the cassandra.yaml config: `write_request_timeout_in_ms`
  - Increase the number of available CPUs
  - Decrease the number of workers
- Cassandra query statements fail because of errors regarding tombstones:
  - Make sure you don't overwrite tweets that you already saved. If you do, run frequent repairs on all cassandra nodes
  - Research how tombstones appear. (TLDR: overwriting, deletion, inserting None values and more)
  - If you only use a single Cassandra node, run `ALTER TABLE component_readings WITH GC_GRACE_SECONDS = 0;` (https://stackoverflow.com/a/37119894)

# Useful commands:

Most useful commands have their own entry in the Makefile in order to have more memorable names and also offer tab-completion, so definitely check that out. For convenience, some are listed below:
- Check if cassandra nodes are healthy: `make cassandra-check`
- Check twitter namespace of cassandra for stats and number of tweets without running an expensive `count` on the database: `docker exec -it backend_cassandra_1 nodetool cfstats | sed -n -e '/Keyspace : twitter/,/----------------/ p'`
- Restarting a service is the same as newly starting it: `docker-compose up --build backend_XYZworker`. If you don't want all the output in your current shell, use the `-d` flag to detach it.
- Reference on how to export cassandra data in a readable format: https://docs.datastax.com/en/cql-oss/3.1/cql/cql_reference/copy_r.html
- `COPY twitter.tweets (id) TO '/tmp/cassandra_dump_ids.csv' WITH HEADER = true;`

# Future work:

- Backup solutions for cassandra, redis and maybe even rabbitmq. Even though redis does not store any tweets, it is possibly the most valuable information because it cannot be brought back in the same way that tweets can be requeried. It stores the distribution of servers, datacenters & sequence ids which are derived from the live sampled stream and therefore cannot be rebuilt at a later time. With this information, efficient querying of the past becomes possible, so even without storing the tweets of the sampled stream, it might be wise to have the analysisworker running at all times.

- Since this data is so valuable, one might think about a replicated analysisworker, probably even on different servers with another bearer auth app token in order to combat possible timeouts and outages. That being said, the analysisworker has proven to be the most stable component in this whole system so far, so this won't really be necessary if the server is reliable.

- Implement proper authentication and SSL for all components.

- Implement the "archive" mode in the taskmanager in order to retrieve x% of a given timeframe that lays in the past.

- Implement cross-component logging into elk and implement kibana dashboards.

# Random

- use gelf driver for docker to export easily to logstash for elk: https://docs.docker.com/config/containers/logging/gelf/
  https://stackoverflow.com/questions/32479530/using-docker-compose-with-gelf-log-driver
  https://stackoverflow.com/questions/41846988/sending-docker-container-logs-to-elk-stack-by-configuring-the-logging-drivers
  https://ridwanfajar.medium.com/send-your-container-logs-to-elk-elasticsearch-logstash-and-kibana-with-gelf-driver-7995714fbbad
  https://logz.io/blog/docker-logging/
