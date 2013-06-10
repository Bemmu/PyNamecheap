# Run "nosetests" on command line to run these.
from namecheap import Api, ApiError
from nose.tools import * # pip install nose

api_key = '' # You create this on Namecheap site
username = ''
ip_address = '' # Your IP address that you whitelisted on the site

# If you prefer, you can put the above in credentials.py instead
try:
	from credentials import api_key, username, ip_address
except:
	pass

def random_domain_name():
	import random, time
	domain_name = "%s%s.com" % (int(time.time()), random.randint(0,10**16))
	return domain_name

def test_domain_taken():
	api = Api(username, api_key, username, ip_address, sandbox = True)
	domain_name = "google.com"
	assert_equal(api.domains_check(domain_name), False)

def test_domain_available():
	api = Api(username, api_key, username, ip_address, sandbox = True)
	domain_name = random_domain_name()
	assert_equal(api.domains_check(domain_name), True)

def test_register_domain():
	api = Api(username, api_key, username, ip_address, sandbox = True)

	# Try registering a random domain. Fails if exception raised.
	domain_name = random_domain_name()
	api.domains_create(
		DomainName = domain_name,
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
	return domain_name

def test_domains_getList():
	api = Api(username, api_key, username, ip_address, sandbox = True)
	api.domains_getList()

@raises(ApiError)
def test_domains_dns_setDefault_on_nonexisting_domain():
	api = Api(username, api_key, username, ip_address, sandbox = True)

	domain_name = random_domain_name()

	# This should fail because the domain does not exist
	api.domains_dns_setDefault(domain_name)	

def test_domains_dns_setDefault_on_existing_domain():
	api = Api(username, api_key, username, ip_address, sandbox = True)
	domain_name = test_register_domain()
	api.domains_dns_setDefault(domain_name)	

def test_domains_getContacts():
	# How would I test for this? This needs a known registered
	# domain to get the contact info for, but in sandbox won't
	# have any.
	pass

def test_domains_dns_setHosts():
	api = Api(username, api_key, username, ip_address, sandbox = True)
	domain_name = test_register_domain()
	api.domains_dns_setHosts(
		domain_name,
		[{
			'HostName' : '@',
			'RecordType' : 'URL',
			'Address' : 'http://news.ycombinator.com',
			'MXPref' : '10',
			'TTL' : '100'
		}]
	)

def test_list_of_dictionaries_to_numbered_payload():
	x = [
		{'foo' : 'bar', 'cat' : 'purr'},
		{'foo' : 'buz'},
		{'cat' : 'meow'}
	]

	result = Api._list_of_dictionaries_to_numbered_payload(x)

	expected_result = {
		'foo1' : 'bar',
		'cat1' : 'purr',
		'foo2' : 'buz',
		'cat3' : 'meow'
	}

	assert_equal(result, expected_result)
