#!/usr/bin/env python3.10

import argparse
import sys

try:
    parser = argparse.ArgumentParser(description='Cypher Mapping Tool by sectroyer v0.1')
    parser.add_argument('-u', '--url', help='Target URL', required=True)
    parser.add_argument('-d', '--data', help='POST data')
    parser.add_argument('-c', '--cookie', help='Request cookie')
    parser.add_argument('-s', '--string', help='Blind string')
    args = parser.parse_args()

    target_url = args.url
    post_data = args.data
    request_cookie = args.cookie
    blind_string = args.string

except:
    print("Usage: python3 cyphermap.py -u <target_url> [-d <post_data>] [-c <request_cookie>] [-s <blind_string>]")
    sys.exit()

# Your code here
