#!/usr/bin/env python3
"""Deterministic per-process image for the development-session JSON-lines API."""
import json
import os
from pathlib import Path
import sys
import time


def send(value):
    data = (json.dumps(value, allow_nan=False) + '\n').encode()
    while data:
        data = data[os.write(3, data):]


def main():
    initial = json.loads(sys.stdin.readline(65537))
    generation = initial['generation']
    send({'type': 'ready', 'generation': generation})
    image = {}
    for line in sys.stdin:
        frame = json.loads(line)
        if frame['type'] != 'execute' or frame['generation'] != generation:
            return 1
        request = frame['request']
        print(json.dumps({'received_operation_id': request['operation_id']}), flush=True)
        expression = json.loads(request['payload']['expression'])
        if expression['op'] == 'set':
            result = expression['value']
            image[expression['name']] = result
        elif expression['op'] == 'get':
            result = image[expression['name']]
        elif expression['op'] == 'gate':
            while not Path(expression['release_path']).exists():
                time.sleep(.01)
            result = None
        else:
            return 1
        send({'type': 'result', 'operation_id': request['operation_id'],
              'generation': generation, 'status': 'completed', 'result': result,
              'image_consistent': True})
    return 0


if __name__ == '__main__':
    sys.exit(main())
