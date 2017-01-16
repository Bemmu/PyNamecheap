#!/usr/bin/env python

import argparse

from namecheap import Api, ApiError

try:
    from credentials import api_key, username, ip_address
except:
    pass


def get_args():
    parser = argparse.ArgumentParser(description="CLI tool to manage NameCheap.com domain records")

    parser.add_argument("--debug", action="store_true", help="If set, enables debug output")
    parser.add_argument("--sandbox", action="store_true", help="If set, forcing usage of Sandbox API, see README.md for details")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add", action="store_true", help="Use to add a record")
    group.add_argument("--delete", action="store_true", help="Use to remove a record")
    group.add_argument("--list", action="store_true", help="List existing records")

    parser.add_argument("--domain", type=str, default="example.org", help="Domain to manage, default is \"example.org\", don't forget to override")

    parser.add_argument("--type", type=str, default="A", help="Record type, default is \"A\"")
    parser.add_argument("--name", type=str, default="test", help="Record name, default is \"test\"")
    parser.add_argument("--address", type=str, default="127.0.0.1", help="Address for record to point to, default is \"127.0.0.1\"")
    parser.add_argument("--ttl", type=int, default=300, help="Time-To-Live, in seconds, default is 300")

    args = parser.parse_args()

    return args


def list_records():
    return api.domains_dns_getHosts(domain)


def record_delete(hostname, address, record_type="A", ttl=300):
    record = {
        "Type": record_type,
        "Name": hostname,
        "Address": address,
        "TTL": str(ttl)
    }
    api.domains_dns_delHost(domain, record)


def record_add(record_type, hostname, address, ttl=300):
    record = {
        "Type": record_type,
        "Name": hostname,
        "Address": address,
        "TTL": str(ttl)
    }
    api.domains_dns_addHost(domain, record)

args = get_args()

domain = args.domain
print("domain: %s" % domain)

api = Api(username, api_key, username, ip_address, sandbox=args.sandbox, debug=args.debug)

if args.add:
    record_add(
        args.type,
        args.name,
        args.address,
        args.ttl
    )
elif args.delete:
    record_delete(
        args.name,
        args.address,
        args.type
    )
elif args.list:
    for line in list_records():
        print("\t%s \t%s\t%s -> %s" % (line["Type"], line["TTL"], line["Name"], line["Address"]))
