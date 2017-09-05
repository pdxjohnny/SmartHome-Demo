var PROTO_PATH = __dirname + '/../protos/collector.proto';

var grpc = require('grpc');
var collector = grpc.load(PROTO_PATH).collector;

function main() {
  console.log(collector);
  var client = new collector.Connection('127.0.0.1:50051',
                                       grpc.credentials.createInsecure());

  var call = client.open();
  call.on('data', function(note) {
    console.log(note)
    console.log('Got message "' + note.message + '" at ' +
        note.location.latitude + ', ' + note.location.longitude);

		call.write(note);
  });

  call.on('end', function(note) {
    console.log('Got message "' + note.message + '" at ' +
        note.location.latitude + ', ' + note.location.longitude);

		call.write(note);
  });
  call.end();
}

main();
