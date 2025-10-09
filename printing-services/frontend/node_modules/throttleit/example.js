
var throttle = require('./');

function onprogress(n) {
  console.log('progress %s%', n);
}

onprogress = throttle(onprogress, 500);

var n = 0;
setInterval(function(){
  if (n >= 100) return;
  onprogress(n++);
}, 50);
