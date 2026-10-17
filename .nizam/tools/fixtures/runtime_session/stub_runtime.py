#!/usr/bin/env python3
"""Deterministic per-process image for the development-session JSON-lines API."""
import json
import os
from pathlib import Path
import select
import sys
import time


def send(value):
    data = (json.dumps(value, allow_nan=False) + '\n').encode()
    while data:
        data = data[os.write(3, data):]


def main():
    # One raw buffer avoids mixing select with TextIO's invisible read-ahead.
    buffer = bytearray()
    def receive(timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        while b'\n' not in buffer:
            remaining = None if deadline is None else max(0, deadline - time.monotonic())
            if not select.select([0], [], [], remaining)[0]:
                return None
            part = os.read(0, 65537 - len(buffer))
            if not part:
                raise EOFError
            buffer.extend(part)
            if len(buffer) > 65536:
                raise ValueError('oversized frame')
        end = buffer.index(b'\n') + 1
        raw = bytes(buffer[:end]); del buffer[:end]
        return json.loads(raw)
    generation = receive()['generation']
    send({'type': 'ready', 'generation': generation})
    image, last = {}, None
    while True:
        frame = receive()
        if frame['type'] == 'cancel' and frame == last:
            continue  # Completed work won the race; do not disturb new work.
        if frame['type'] != 'execute' or frame['generation'] != generation:
            return 1
        request = frame['request']
        last = {'type': 'cancel', 'session_id': request['session_id'],
                'operation_id': request['operation_id'], 'generation': generation,
                'lease_epoch': request['expected_lease_epoch']}
        print(json.dumps({'received_operation_id': request['operation_id']}), flush=True)
        expression = json.loads(request['payload']['expression'])
        cancelled = False
        if expression['op'] == 'set':
            result = expression['value']
            image[expression['name']] = result
        elif expression['op'] == 'get':
            result = image[expression['name']]
        elif expression['op'] == 'gate':
            while not Path(expression['release_path']).exists():
                control = receive(.01)
                if control is None:
                    continue
                if control != last:
                    return 1
                cancelled = True
                break
            result = None
        else:
            return 1
        response = {'type': 'result', 'operation_id': request['operation_id'],
                    'generation': generation, 'status': 'cancelled' if cancelled else 'completed',
                    'result': result, 'image_consistent': True}
        if cancelled:
            response.update(session_id=request['session_id'], lease_epoch=request['expected_lease_epoch'],
                            cancellation_confirmed=True)
        send(response)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except EOFError:
        sys.exit(0)
