#!/usr/bin/env python3
import socket
import time
import sys


def check_port(host, port, timeout=2):
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except (socket.timeout, socket.error):
        return False


def wait_for_service(host, port, name, max_retries=30):
    retry = 0
    while retry < max_retries:
        if check_port(host, port):
            print(f"✓ {name} is ready on {host}:{port}!")
            return True
        retry += 1
        print(f"  Attempt {retry}/{max_retries} - Waiting for {name}...")
        time.sleep(2)
    print(f"✗ {name} failed to start within timeout")
    return False


def main():
    ok = True
    ok &= wait_for_service('api-service', 8000, 'API service')
    ok &= wait_for_service('postgres', 5432, 'Database service')
    if not ok:
        sys.exit(1)
    print('✓ All services are ready!')


if __name__ == '__main__':
    main()
