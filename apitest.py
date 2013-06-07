from namecheap import Api

api_key = '' # You create this on Namecheap site
username = ''
ip_address = '' # Your IP address that you whitelisted on the site
is_sandbox = True # Sandbox account creation: http://www.sandbox.namecheap.com/

# If you prefer, you can put the above in credentials.py instead
try:
	from credentials import api_key, username, ip_address, is_sandbox
except:
	pass

api = Api(username, api_key, username, ip_address, is_sandbox)

# Test checking if domain is available
print str(api.domains_check(['aksdopsakdcopaskdcpo.com']))

# Test getting list of domains
#domains = api.domains_getList()
#print list(domains)

# Test getting contact information for a domain
#print str(api.domains_getContacts(['coolestfriends.com']))

# Test registering a domain
api.domains_create(
	DomainName = 'aksdopsakdcopaskdcpo.com',
	FirstName = 'Jack',
	LastName = 'Trotter',
	Address1 = 'Ridiculously Big Mansion, Yellow Brick Road',
	City = 'Tokushima',
	StateProvince = 'Tokushima',
	PostalCode = '771-0144',
	Country = 'Japan',
	Phone = '+81.123123123',
	EmailAddress = 'jack.trotter@example.com'
)