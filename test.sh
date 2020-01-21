#!/bin/bash
#sudo rabbitmqadmin --user guest --password guest  delete exchange  name='report'

echo "CREATE DEVICES"
curl -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"id": 123}' http://localhost:8888/api/v1/device
echo
curl -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"id": 456}' http://localhost:8888/api/v1/device
echo

sleep 2

echo "SAVE REPORTS"
curl -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"id": 123,"report": "name"}' http://localhost:8888/api/v1/device/123/reports
echo
curl -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"id": 456,"report": "name"}' http://localhost:8888/api/v1/device/456/reports
echo

sleep 2

echo "GET REPORTS"
curl -H "Accept: application/json" -X GET http://localhost:8888/api/v1/device/123/reports
echo
curl -H "Accept: application/json" -X GET http://localhost:8888/api/v1/device/456/reports
echo

sleep 2

echo "REDIS TEST"
redis-cli get 123
redis-cli get 456