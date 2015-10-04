#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser(
    description='A comprehensive caller for somatic mosaic variations',
)

subparsers = parser.add_subparsers(help='commands')

# somatic_call cammand

smtcl_parser = subparsers.add_parser(
    'somatic_call', help='Run somatic callers')
smtcl_parser.add_argument(
    '--ref'
