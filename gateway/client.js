var grpc = require('grpc');
var collector = require('./collector.js');

class Client {
  constructor (server, creds) {
    this.callbacks = {};
    this.client = new collector.Connection(server, creds);
    this.s = this.client.open();
    this.s.on('data', this.ondata.bind(this));
    this.s.on('end', this.onend.bind(this));
  }

  ondata (data) {
    if (this.callbacks.hasOwnProperty(data.xid)) {
      if (data.code === 200 &&
        typeof this.callbacks[data.xid].resolve === 'function') {
        this.callbacks[data.xid].resolve(data);
      } else if (data.code !== 200 &&
        typeof this.callbacks[data.xid].reject === 'function') {
        this.callbacks[data.xid].reject(data);
      }
    } else {
      console.log('Unhandled data:', data);
    }
  }

  onend (err) {
    if (typeof err === 'undefined') {
      console.log('Done');
      return;
    }
    console.log('Error on end:', err)
  }

  write (method, data, resolve, reject) {
    var xid = Math.floor(Math.random() * 10000000);
    this.callbacks[xid] = {'resolve': resolve, 'reject': reject};
    return this.s.write(new collector.Request(xid, method, JSON.stringify(data)));
  }

  connect (data) {
    return new Promise(function(resolve, reject) {
      this.write('connect', data, resolve, reject);
    }.bind(this));
  }

  wait (data) {
    return new Promise(function(resolve, reject) {
      this.write('wait', data, resolve, reject);
    }.bind(this));
  }

  end () {
    return this.s.end();
  }
};

module.exports = Client;
