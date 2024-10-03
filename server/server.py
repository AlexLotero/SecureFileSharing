#!/usr/bin/env python3

from signature_utility import generate_key_pair, generate_signature, verify_signature
from socket import *
import concurrent.futures
from pathlib import Path
import ntpath

import argparse
import json
import sys
import os
import secrets
import random
from datetime import date
import threading

PORT = 8084 #random.randint(1000, 1200)
FILE_LOCATION = "server/files/"
valid = [False]

SHUTOFF = False

# response_dict = {1: 'r',
#                  2: 'sd',
#                  3: 'cb',
#                  4: 'cl'}

# FILE_ALREADY_EXISTS = {1: replace_file,2: save_different_name, 3: combine_files, 4: keep_existing}

# function to test whether the requested file exists on the server - repurposed from fencrypt
def file_exists(file):#, type):
     return os.path.exists(file)

def duplicate_file(connection_socket):
     connection_socket.send('''\n
                            The file you are attampting to upload already exists on the server.
                            Please type and submit:
                            1 to replace the existing file with the new one,
                            2 to save this new file under a different name,
                            3 to append the new file onto the end of the existing one, or
                            4 to keep the existing file and not upload the new one
                            \n'''.encode('utf-8'))
     response = connection_socket.recv(4096)
     response = response.split()
     response = [field.decode('utf-8') for field in response]
     response_command = int(response[0])
    #  response_new_name = response[1]
     return response_command #, response_new_name

def save_file(file_name, new_data):
    with open(file_name, "w") as f:
            f.write(new_data)
            f.close()
    return

def replace_file(new_file, new_data):
    os.remove(new_file)
    save_file(new_file, new_data)
    return

def save_different_name(different_name, new_data):
    head, sep, tail = different_name.partition('.')
    if tail:
        new_name = head + date.today().strftime('%Y-%m-%d') + sep + tail
    else:
        new_name = different_name + date.today().strftime('%Y-%m-%d')
    save_file(new_name, new_data)
    return

def combine_files(file_to_append, new_data):
    with open(file_to_append, "a") as f:
        f.write(new_data)
        f.close()
    return

def keep_existing():
    print("No changes made to existing file.")
    return

# Wrapper function to set valid[0] = True when any function is called
def wrap_with_valid(operation_function):
    def wrapper(*args, **kwargs):
        valid[0] = True  # Set valid[0] to True
        return operation_function(*args, **kwargs)    # Call the original function
    return wrapper

def invalid_case():
    valid[0] = False  # Update the value of 'valid'
    print("Invalid value")

FILE_ALREADY_EXISTS = {1: wrap_with_valid(replace_file), 
                       2: wrap_with_valid(save_different_name), 
                       3: wrap_with_valid(combine_files), 
                       4: wrap_with_valid(keep_existing)
                       }

def send_file(connection_socket, file_name):
    # Open the file in read-binary mode
    with open(file_name, 'rb') as file:
        # Read and send the file in chunks
        while True:
            chunk = file.read(4096)  # Read up to 4096 bytes
            if not chunk:
                break  # End of file reached
            connection_socket.sendall(chunk) # Send the chunk
    print(f"File '{file_name}' sent successfully.")

def connection_handler(connection_socket, addr, e_admin_shutoff):
    print("On port %s", PORT)

    # *INTEGRATE LOGIN CODE BEFORE SENDING/RECEIVING FILES*

    # try:
    while True:
        message = connection_socket.recv(4096)               # found in Python "socket" documentation, "the value of bufsize should be a relatively small power of 2, for example, 4096"
        
        if not message:
            break
        
        message = message.split()
        message = [field.decode('utf-8') for field in message]
        filename = FILE_LOCATION + message[1]
        file_contents = "\n" + ' '.join(message[2:]) + "\n"
        request_type = message[0]

        # Pull code from fencrypt to check if the requested file exists
        file_already = file_exists(filename)

        if request_type == "SHUTOFF":
            e_admin_shutoff.set()
            SHUTOFF = True
            break 
        
        if file_already and request_type == "PUT":
            to_do = duplicate_file(connection_socket)
            # FIGURE OUT HOW TO HANDLE EACH SCENARIO IN THE CASE OF A DUPLICATE FILE UPLOAD
            FILE_ALREADY_EXISTS.get(to_do, invalid_case)(filename, file_contents) 
            # break

        elif request_type == "PUT" and not file_already:
            save_file(filename, file_contents)
            # break

        elif request_type == "GET":
            send_file(connection_socket, filename)
            # break
        
        elif request_type == "END":
            break
        
        # elif request_type == "SHUTOFF": #and admin:
        #     e_admin_shutoff.set()
        #     SHUTOFF = True
        #     break

        #Fill in start
    connection_socket.close()                            # found in Python "socket" documentation
        #Fill in end
    return #e_admin_shutoff

def web_server(port):
    e_admin_shutoff = threading.Event()
    
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=100)

    serverSocket = socket(AF_INET, SOCK_STREAM)
    
    #Prepare a sever socket
    serverSocket.bind(("", port))
    serverSocket.listen(1)
    print("Server listening...")

    while not SHUTOFF:#e_admin_shutoff.is_set():
        #Establish the connection
        print('Ready to serve...')
        connection_socket, client_addr = serverSocket.accept()
        print("connection initiated  with: %s", client_addr)
        
        pool.submit(connection_handler, connection_socket, client_addr, e_admin_shutoff)
        # e_admin_shutoff = pool.submit(connection_handler(connection_socket, client_addr))
    
    pool.shutdown(wait=True)
    serverSocket.close()
    sys.exit()  # Terminate the program after 
    # pool.shutdown(wait=True)

def main():
    print("Server starting...")
    web_server(PORT)
    return 0

if __name__ == "__main__":
    main()