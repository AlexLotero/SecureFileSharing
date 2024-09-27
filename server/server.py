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

PORT = 8085 #random.randint(1000, 1200)
FILE_LOCATION = "server/files/"
valid = [False]
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

def connection_handler(connection_socket, addr):
    print("On port %s", PORT)

    # *INTEGRATE LOGIN CODE BEFORE SENDING/RECEIVING FILES*

    try:
            message = connection_socket.recv(4096)               # found in Python "socket" documentation, "the value of bufsize should be a relatively small power of 2, for example, 4096"
            message = message.split()
            message = [field.decode('utf-8') for field in message]
            filename = FILE_LOCATION + message[1]
            file_contents = "\n" + ' '.join(message[2:]) + "\n"
            request_type = message[0]

            # Pull code from fencrypt to check if the requested file exists
            file_already = file_exists(filename)


            if file_already and request_type == "PUT":
                to_do = duplicate_file(connection_socket)
                # FIGURE OUT HOW TO HANDLE EACH SCENARIO IN THE CASE OF A DUPLICATE FILE UPLOAD
                FILE_ALREADY_EXISTS.get(to_do, invalid_case)(filename, file_contents) 
                return False
            
            if request_type == "TERM" and admin:
                 connection_socket.close()
                 return True

            elif request_type == "PUT" and not file_already:
                save_file(filename, file_contents)
                return False

            elif request_type == "GET":
                send_file(connection_socket, filename)
                return False

            # else:
            #      connection_socket.close()
            #      return False
            
            f = open(filename[1:])
            outputdata = f.read()                               # stack overflow: read a text file into a string variable

            #Send one HTTP header line into socket
            #Fill in start
            httpOK = "HTTP/1.1 200 OK\r\n"                       # taken from Wireshark lab (http4.pcapng), GET response output
            connection_socket.send(httpOK.encode('utf-8'))        # to alleviate TypeError: a bytes-like object is required, not 'str'
            #Fill in end

            #Send the content of the requested file to the client
            # for i in range(0, len(outputdata)):
            #     connectionSocket.send(outputdata[i].encode())
            connection_socket.send(outputdata.encode())
            connection_socket.send("\r\n".encode())
            connection_socket.close()
    except IOError:
        #Send response message for file not found (404)
        #Fill in start
        http_not_found = "HTTP/1.1 404 Not Found\r\n"         # taken from Wireshark lab (http4.pcapng), GET response output
        connection_socket.send(http_not_found.encode('utf-8')) # to alleviate TypeError: a bytes-like object is required, not 'str'
        #Fill in end

        #Close client socket
        #Fill in start
        connection_socket.close()                            # found in Python "socket" documentation
        #Fill in end
    return

def web_server(port):
    e_admin_shutoff = False
    
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=100)

    serverSocket = socket(AF_INET, SOCK_STREAM)
    
    #Prepare a sever socket
    serverSocket.bind(("", port))
    serverSocket.listen(1)
    print("Server listening...")

    while not e_admin_shutoff:
        #Establish the connection
        print('Ready to serve...')
        connection_socket, client_addr = serverSocket.accept()
        print("connection initiated  with: %s", client_addr)

        e_admin_shutoff = pool.submit(connection_handler(connection_socket, client_addr))
    
    pool.shutdown(wait=True)
    serverSocket.close()
    sys.exit()  # Terminate the program after 
    pool.shutdown(wait=True)

def main():
    print("Server starting...")
    web_server(PORT)
    return 0

if __name__ == "__main__":
    main()