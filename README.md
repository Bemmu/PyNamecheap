PyNamecheap
===========

Namecheap API client in Python.

Supports:
 - Registering a domain
 - Checking domain name availability
 - Listing domains you have registered
 - Getting contact information for a domain
 - Setting DNS info to default values
 - Set DNS host records

### How to sign up to start using the API

The API has two environments, production and sandbox. Since this API will spend real money when registering domains, start with the sandbox by going to http://www.sandbox.namecheap.com/ and creating an account. Accounts between production and sandbox are different, so even if you already have a Namecheap account you will need a new one.

After you have an account, go to "manage profile".

![Profile](https://raw.github.com/Bemmu/PyNamecheap/master/img/profile.png "Profile")

From there, select "API Access" menu.

![API menu](https://raw.github.com/Bemmu/PyNamecheap/master/img/apimenu.png "API menu")

You'll get to your credentials page. From here you need to take note of your api key, username and add your IP to the whitelist of IP addresses that are allowed to access the account. You can check your public IP by searching "what is my ip" on Google and add it here. It might take some time before it actually starts working, so don't panic if API access doesn't work at first.

![Credentials](https://raw.github.com/Bemmu/PyNamecheap/master/img/credentials.png "Credentials")

### How to access the API from Python

Copy namecheap.py to your project. In Python you can access the API as follows:

	from namecheap import Api
    api = Api(username, api_key, username, ip_address, sandbox = True)

The fields are the ones which appear in the credentials screen above. The username appears twice, because you might be acting on behalf of someone else.

### Registering a domain name using the API

Unfortunately you need a bunch of contact details to register a domain, so it is not as easy as just providing the domain name. In the sandbox, the following contact details are acceptable. Trickiest field is the phone number, which has to be formatted as shown.

	api.domains_create(
		DomainName = 'registeringadomainthroughtheapiwow.com',
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

This call should succeed in the sandbox, but if you use the API to check whether this domain is available after registering it, the availability will not change. This is normal.

### More

Look at namecheap_tests.py to see more examples of things you can do.