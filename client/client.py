#!/usr/bin/env python3

from ..signature_utility import generate_key_pair, generate_signature, verify_signature
import argparse
import json
import sys
import os
import secrets


def parser_func():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "P", nargs="*", help="either file paths or search terms")
    group.add_argument("-e", nargs="*", help="encrypt provided files")
    group.add_argument("-d", nargs="*", help="decrypt provided files")
    group.add_argument("-s", nargs="*", help="search files in current folder")
    parser.add_argument("-j", action="store_true",
                        help="output debug information to stdout")
    args = parser.parse_args()
    return args


def no_arg():
    a = """usage: fencrypt.py [-h] [-e [E ...]] [-d [D ...]] [-s [S ...]] [-j] [P ...]
            positional arguments:
            P     either file paths or search terms
            optional arguments:
            -h, --help  show this help message and exit
            -e [E ...]  encrypt provided files
            -d [D ...]  decrypt provided files
            -s [S ...]  search files in current folder
            -j          output debug information to stdout"""
    print(a)
    sys.exit(1)

def server_connect():
    return

def main():
    args = parser_func()

    if not len(sys.argv) > 1:
        no_arg()

    if args.P and not args.e:
        args.e = args.P
    
    if (args.e and args.d) or (args.e and args.s) or (args.d and args.s):
        no_arg()

    if args.e:
        print()

    if args.d:
        print()

    if args.s:
        print()

    return 0

if __name__ == "__main__":
    main()