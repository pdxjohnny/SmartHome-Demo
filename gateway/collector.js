var grpc = require('grpc');

var PROTO_PATH = __dirname + '/../protos/collector.proto';
var collector = grpc.load(PROTO_PATH).collector;

function NoPayload() {}

function MessageGen(col) {
  var MessageConstructor = col.Message;
  function Message(payload, band) {
    if (typeof payload === 'undefined') {
      throw new NoPayload();
    }
    if (typeof band === 'undefined') {
      band = 'main';
    }
    return new MessageConstructor(band, payload);
  }
  return Message;
}
collector.Message = MessageGen(collector);

module.exports = collector;
