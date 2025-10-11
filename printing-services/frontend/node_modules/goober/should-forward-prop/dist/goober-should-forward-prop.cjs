exports.shouldForwardProp=function(o){return function(r){for(let e in r)o(e)||delete r[e]}};
