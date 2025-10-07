// src/thenable.ts
import { noop } from "./utils.js";
function pendingThenable() {
  let resolve;
  let reject;
  const thenable = new Promise((_resolve, _reject) => {
    resolve = _resolve;
    reject = _reject;
  });
  thenable.status = "pending";
  thenable.catch(() => {
  });
  function finalize(data) {
    Object.assign(thenable, data);
    delete thenable.resolve;
    delete thenable.reject;
  }
  thenable.resolve = (value) => {
    finalize({
      status: "fulfilled",
      value
    });
    resolve(value);
  };
  thenable.reject = (reason) => {
    finalize({
      status: "rejected",
      reason
    });
    reject(reason);
  };
  return thenable;
}
function tryResolveSync(promise) {
  let data;
  promise.then((result) => {
    data = result;
    return result;
  }, noop)?.catch(noop);
  if (data !== void 0) {
    return { data };
  }
  return void 0;
}
export {
  pendingThenable,
  tryResolveSync
};
//# sourceMappingURL=thenable.js.map