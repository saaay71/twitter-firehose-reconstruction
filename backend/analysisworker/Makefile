clean:
	if [ -a snowflake/*.py ]; then rm snowflake/*.py; fi;

dependencies:
	cp -fr ../snowflake/* ./src/snowflake/

test:
	python3 -m unittest discover -s src/ -p "*_test.py"

docker:
	docker build -t local/analysisworker -f Dockerfile .
