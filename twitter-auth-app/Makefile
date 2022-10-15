run-build-production:
	docker-compose up --build

run-production:
	docker-compose up

# You need to use -j2 flag with make (to execute both commands parallel)
run-development: server-run client-run

run-server:
	$(MAKE) -C server run
 
run-client:
	$(MAKE) -C client run
