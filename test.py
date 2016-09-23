#!/usr/bin/env python

from namecheap import Api, ApiError

try:
    from credentials import api_key, username, ip_address
except:
    pass

domain = "roxottech.com"
api = Api(username, api_key, username, ip_address, sandbox=False)
record = {
    "Type": "A",
    "Name": "test",
    "Address": "127.0.0.1",
    "TTL": 1800,
    "MXPref": 10
}
api.domains_dns_addHost(domain, record)
