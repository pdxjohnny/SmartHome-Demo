#!/bin/sh

dir="$(basename `pwd`)"
while [ "$dir" != "/" ] && [ "$dir" != "SmartHome-Demo" ]; do
  cd ..
  dir="$(basename `pwd`)"
done

python \
  -m grpc_tools.protoc \
  -Iprotos \
  --python_out=collector/ \
  --grpc_python_out=collector/ \
  protos/collector.proto
cp collector/*_pb2* smarthome-web-portal/RestClient/api/
