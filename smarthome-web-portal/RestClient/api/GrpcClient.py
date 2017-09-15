# -*- coding: utf-8 -*-
"""
gRPC Client
"""
from concurrent import futures
import logging
import socket
import select
import pickle
import struct
import json
import time
import multiprocessing

from RestClient.api import ApiClient, IoTResponse
from RestClient import __version__
from iotError import IoTConnectionError, IoTRequestError

logger = logging.getLogger(__name__)

import grpc

import collector_pb2
import collector_pb2_grpc

STRUCT_FMT = '!Q'

def qr(res, code, payload):
    res.code = code
    res.payload = payload
    return res

def lenpickle(writer, res):
    w = getattr(writer, 'sendall', getattr(writer, 'send'))
    msg = pickle.dumps(res)
    length = struct.pack(STRUCT_FMT, len(msg))
    return length + msg

def lenunpickle(reader):
    r = getattr(reader, 'recv', getattr(reader, 'read'))
    length = struct.unpack(STRUCT_FMT, i.recv(8))
    response = collector_pb2.Response()
    response.xid = i.xid
    response.code = 200
    response.headers = ''
    response.payload = pickle.loads(i.read(length))
    msg = pickle.dumps(res)
    length = struct.pack(struct_fmt, len(msg))
    return length + msg

class Message(object):

    def __init__(self, data, recv_next=False, **kwargs):
        self.data = data
        self.recv_next = recv_next
        self.kwargs = kwargs

class Connection(collector_pb2_grpc.ConnectionServicer):

    queue_class = multiprocessing.Queue().__class__

    def __init__(self, *args, **kwargs):
        collector_pb2_grpc.ConnectionServicer.__init__(self, *args, **kwargs)
        self.clients = {}

    def send(self, client, data, **kwargs):
        if not client in self.clients:
            raise ValueError('Client not connected')
        self.clients[client][0].put(Message(data, **kwargs))

    def recv(self, client, data):
        if not client in self.clients:
            raise ValueError('Client not connected')
        return self.clients[client][1].get()

    def Open(self, reqs, context):
        recv_next = False
        from_client = None
        for i in reqs:
            res = collector_pb2.Response()
            res.xid = i.xid
            res.code = 200
            res.headers = ''
            res.payload = ''
            data = {}
            if len(i.payload):
                try:
                    data = json.loads(i.payload)
                except Exception as e:
                    res.code = 400
                    res.payload = str(e)
                    yield res
                    continue
            if i.method.startswith('handle_'):
                res.code = 400
                res.payload = 'Invalid Method'
                yield res
                continue
            try:
                if recv_next:
                    recv_next = False
                    from_client.put(i)
                res = getattr(self, 'handle_{}'.format(i.method))(i,
                        res, data)
                if isinstance(res, tuple) and isinstance(res[0], self.queue_class):
                    to_client, from_client = res
                    res = to_client.get()
                    if res.recv_next:
                        recv_next = True
                        continue
                    res = res.data
                yield res
                continue
            except AttributeError as e:
                res.code = 501
                res.payload = 'Not Implemented' + ' ERROR: ' + str(e)
                yield res
                continue
            except Exception as e:
                res.code = 500
                res.payload = str(e)
                yield res
                continue

    def handle_connect(self, req, res, data):
        return res

    def handle_wait(self, req, res, data):
        if not 'name' in data:
            return qr(res, 400, 'Missing name')
        if data['name'] in self.clients:
            self.send(data['name'], 'ping')
            try:
                r = self.recv(data['name'])
                print('self.recv(', data['name'], ')')
                if r == 'pong':
                    return qr(res, 500, 'Name already waiting')
            except: pass
        r, w = self.clients[data['name']] = (multiprocessing.Queue(),
                multiprocessing.Queue())
        return (r, w)

SERVER = Connection()
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
    collector_pb2_grpc.add_ConnectionServicer_to_server(SERVER, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            i = raw_input(">>> ")
            print('Got:', i)
            i = i.split(' ')
            client = i[0]
            msg = ' '.join(i[1:])
            SERVER.send(client, msg)
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
