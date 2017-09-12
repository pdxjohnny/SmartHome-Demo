# -*- coding: utf-8 -*-
"""
gRPC Client
"""
from concurrent import futures
import logging
import socket
import select
import pickle
import json
import time

from RestClient.api import ApiClient, IoTResponse
from RestClient import __version__
from iotError import IoTConnectionError, IoTRequestError

logger = logging.getLogger(__name__)

import grpc

import collector_pb2
import collector_pb2_grpc

_CLIENTS = {}

def qr(res, code, payload):
    res.code = code
    res.payload = payload
    return res

class Connection(collector_pb2_grpc.ConnectionServicer):

    def Open(self, reqs, context):
        for i in reqs:
            response = collector_pb2.Response()
            response.xid = i.xid
            response.code = 200
            response.headers = ''
            response.payload = ''
            data = {}
            if len(i.payload):
                try:
                    data = json.loads(i.payload)
                except Exception as e:
                    response.code = 400
                    response.payload = str(e)
                    yield response
                    continue
            if i.method.startswith('handle_'):
                response.code = 400
                response.payload = 'Invalid Method'
                yield response
                continue
            try:
                response = getattr(self, 'handle_{}'.format(i.method))(i,
                        response, data)
                if hasattr(response, 'fileno'):
                    r, w, e = select.select([response], [], [])
                    for i in r:
                        length = int.from_bytes(i.recv(8), byteorder='big')
                        response = collector_pb2.Response()
                        response.xid = i.xid
                        response.code = 200
                        response.headers = ''
                        response.payload = pickle.loads(i.read(length))
                yield response
                continue
            except AttributeError:
                response.code = 501
                response.payload = 'Not Implemented'
                yield response
                continue
            except Exception as e:
                response.code = 500
                response.payload = str(e)
                yield response
                continue

    def handle_connect(self, req, res, data):
        return res

    def handle_wait(self, req, res, data):
        if not 'name' in data:
            return qr(res, 400, 'Missing name')
        if data['name'] in _CLIENTS:
            return qr(res, 500, 'Name already waiting')
        r, _CLIENTS[data['name']] = socket.socketpair()
        return r
'''
    {
        'name': 'lab',
        'url': 'http://172.17.0.2:8000/',
        'address': 'No. 880, Zi Xing Rd, Shanghai',
        'latitude': '31.020780',
        'longitude': '121.454648',
        'status': True
    },
'''

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    collector_pb2_grpc.add_ConnectionServicer_to_server(Connection(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)
    except KeyboardInterrupt:
        server.stop(0)

class GrpcClient(ApiClient):
    """
    A gRPC connection to a gateway.
    """

    def __init__(self, api_uri, proxy, ca_cert=None):
        """
        Create a RESTful API client.
        """
        self.api_uri = api_uri
        self.proxy = None
        self.auth = None
        self.verify = None
        if proxy:
            if isinstance(proxy, dict):
                self.proxy = proxy
            elif isinstance(proxy, str):
                self.proxy = {
                    'http': proxy,
                    'https': proxy
                }
        if ca_cert:
            self.verify = ca_cert

    def request(self, method, path, data={}, headers={}, stream=False):
        url = '{0}{1}'.format(self.api_uri, path)
        self._set_default_header()
        headers = self.merge_dicts(self.header, headers)
        print("url:" + url)

        if self.api_uri in _CLIENTS:
            data = pickle.dumps({
                'url': url,
                'method': method,
                'path': path,
                'headers': headers,
                'proxies': proxies,
                'data': data
                })
            _CLIENTS[self.api_uri].sendall(len(data).to_bytes(8,
                byteorder='big'), data)
            return GrpcIoTResponse(r, stream)
        else:
            raise IoTConnectionError('Client not connected')

class GrpcIoTResponse(IoTResponse):

    @property
    def json(self):
        """returns: response as JSON object."""
        return json.loads(self.response.text)

def main():
    serve()

if __name__ == '__main__':
    main()
