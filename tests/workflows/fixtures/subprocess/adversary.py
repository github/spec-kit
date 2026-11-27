"""Stdlib-only dishonest peer for testing the production controller boundary."""
import json
import struct
import sys


def receive():
    size, = struct.unpack('!I', sys.stdin.buffer.read(4))
    return json.loads(sys.stdin.buffer.read(size))


def send(message):
    data = json.dumps(message).encode()
    sys.stdout.buffer.write(struct.pack('!I', len(data)) + data)
    sys.stdout.buffer.flush()


start = receive()
base = {"version": 1, "identity": start["identity"], "revision": 0, "payload": {}, "kind": "ready"}
send(base)
mode = sys.argv[1]
if mode == 'early-outputs':
    send({**base, 'revision': 1, 'kind': 'transition', 'payload': {
        'position': [], 'operation': 'outputs', 'changes': {}, 'publish': False, 'announce': True, 'inputs': None}})
elif mode == 'final-only':
    send({**base, 'kind': 'finalize'})
    receive()
    send({**base, 'kind': 'result', 'payload': {'status': 'completed', 'error': None,
          'output': {'workflow': 'child', 'status': 'completed'}}})
else:
    payload = {'position': [0, 0], 'operation': 'begin', 'changes': {}, 'publish': True, 'announce': True, 'inputs': {}}
    message = {**base, 'revision': 1, 'kind': 'transition', 'payload': payload}
    if mode == 'escape':
        payload['position'] = [2, 0]
    elif mode == 'outer-finish':
        payload['position'] = []
        payload['operation'] = 'finish'
    elif mode == 'stale':
        message['revision'] = 0
    elif mode == 'nonce':
        message['identity'] = {**message['identity'], 'nonce': 'wrong'}
    elif mode == 'unknown-envelope':
        message['extra'] = True
    elif mode == 'invalid-fields':
        payload['changes'] = {'binding': {}}
    elif mode == 'forged-progress':
        payload['operation'] = 'expand'
        payload['changes'] = {'children': [{'source': '- id: forged', 'nodes': [{'phase': 'done'}]}]}
    send(message)
