from concurrent import futures
import time

import grpc

import collector_pb2
import collector_pb2_grpc

class Connection(collector_pb2_grpc.ConnectionServicer):

    def Open(self, reqs, context):
        for i in reqs:
            print(str(i).strip())
            yield i

    def Call(self, reqs, context):
        for i in reqs:
            print(str(i).strip())
            yield collector_pb2.Response(code=200)

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

if __name__ == '__main__':
    serve()
