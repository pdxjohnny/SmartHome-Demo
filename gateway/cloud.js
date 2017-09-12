var grpc = require('grpc');
var rest = require('iot-rest-api-server');
var Client = require('./client.js');

function main() {
    var client = new Client('127.0.0.1:50051', grpc.credentials.createInsecure());
    client.connect().then(function(data) {
        console.log('Connected', data);
        client.wait({'name': 'test'}).then(function(data) {
            console.log('Got wait', data);
            client.end();
        }).catch(function(data) {
            console.log('Failed to wait', data);
            client.end();
        });
    }).catch(function(data) {
        console.log('Failed to connect', data);
    });
}

main();
