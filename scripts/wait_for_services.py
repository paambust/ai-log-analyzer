#!/usr/bin/env python3
import socket
import time
import sys
import logging


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    return logging.getLogger("wait_for_services")


logger = setup_logger()


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
            logger.info("✓ %s is ready on %s:%s!", name, host, port)
            return True
        retry += 1
        logger.info("Attempt %s/%s - Waiting for %s...", retry, max_retries, name)
        time.sleep(2)
    logger.error("✗ %s failed to start within timeout", name)
    return False


def main():
    ok = True
    ok &= wait_for_service('api-service', 8000, 'API service')
    ok &= wait_for_service('postgres', 5432, 'Database service')
    if not ok:
        sys.exit(1)
    logger.info('✓ All services are ready!')


if __name__ == '__main__':
    main()
