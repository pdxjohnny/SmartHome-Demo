var startDate = new Date();
var grpc = require('grpc');
var rest = require('iot-rest-api-server');
var Client = require('./client.js');

function main() {
  var client = new Client();
  client.connect('127.0.0.1:50051', grpc.credentials.createInsecure()) .then(function(data) {
    console.log('Connected', data);
    client.wait({'name': 'test' + Math.floor(Math.random() * 10)}).then(function(data) {
      console.log('Got wait', data);
      client.end();
    }, function(err) {
      console.log('Failed to wait', err);
      client.end();
    });
  }, function(err) {
    console.log('Failed to connect', err);
  });
}

main();
