#!/usr/bin/env python3.10

import argparse
import requests
import sys


def perform_request(target_url, post_data=False, cookie_data={}, connection_timeout=5):
    try:
        if post_data:
            response = requests.post(target_url, data=post_data, cookies=cookie_data, timeout=connection_timeout)
        else:
            response = requests.get(target_url, cookies=cookie_data, timeout=connection_timeout)

        return response.text

    except requests.exceptions.Timeout:
        return False


try:
    parser = argparse.ArgumentParser(description='Cypher Mapping Tool by sectroyer v0.1')
    parser.add_argument('-u', '--url', help='Target URL', required=True)
    parser.add_argument('-d', '--data', help='POST data', default=False)
    parser.add_argument('-c', '--cookie', help='Request cookie', default={})
    parser.add_argument('-s', '--string', help='Blind string')
    parser.add_argument('-t', '--timeout', help='Connection timeout', default=5)
    args = parser.parse_args()

    target_url = args.url
    post_data = args.data
    request_cookie = args.cookie
    blind_string = args.string
    connection_timeout = args.timeout
except:
    print('')
    sys.exit()

# Your code here
