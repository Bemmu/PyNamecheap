import sys
import time
import requests  # pip install requests
from xml.etree.ElementTree import fromstring, Element

inPy3k = sys.version_info[0] == 3

# http://developer.namecheap.com/docs/doku.php?id=overview:2.environments
ENDPOINTS = {
    # To use
    # 1) browse to http://www.sandbox.namecheap.com/
    # 2) create account, my account > manage profile > api access > enable API
    # 3) add your IP address to whitelist
    'sandbox': 'https://api.sandbox.namecheap.com/xml.response',
    'production': 'https://api.namecheap.com/xml.response',
}
NAMESPACE = "http://api.namecheap.com/xml.response"

# default values for the retry mechanism
DEFAULT_ATTEMPTS_COUNT = 1  # no retries
DEFAULT_ATTEMPTS_DELAY = 0.1  # in seconds


# https://www.namecheap.com/support/api/error-codes.aspx
class ApiError(Exception):
    def __init__(self, number, text):
        Exception.__init__(self, '%s - %s' % (number, text))
        self.number = number
        self.text = text


# noinspection PyPep8Naming
class Api(object):
    ENDPOINTS = ENDPOINTS
    
    # Follows API spec capitalization in variable names for consistency.
    def __init__(self, ApiUser, ApiKey, UserName, ClientIP,
                 sandbox=True, debug=True,
                 attempts_count=DEFAULT_ATTEMPTS_COUNT,
                 attempts_delay=DEFAULT_ATTEMPTS_DELAY):
        self.ApiUser = ApiUser
        self.ApiKey = ApiKey
        self.UserName = UserName
        self.ClientIP = ClientIP
        self.endpoint = ENDPOINTS['sandbox' if sandbox else 'production']
        self.debug = debug
        self.payload_limit = 10  # After hitting this lenght limit script will move payload from POST params to POST data
        self.attempts_count = attempts_count
        self.attempts_delay = attempts_delay

    # https://www.namecheap.com/support/api/methods/domains/create.aspx
    def domains_create(
        self,
        DomainName, FirstName, LastName,
        Address1, City, StateProvince, PostalCode, Country, Phone,
        EmailAddress, Address2=None, years=1, WhoisGuard=False,
        OrganizationName=None, JobTitle=None, PromotionCode=None,
        Nameservers=None, **user_payload
    ):
        # type: (str, str, str, str, str, str, str, str, str, str, str, int, bool, str, str, str, str or list, any) -> dict
        """
        Registers a domain name with the given contact info.
        Example of a working phone number: +81.123123123

        For simplicity assumes one person acts as all contact types.
        
        If you're registering a domain as a company/organisation, specify the company name in ``OrganizationName``,
        and specify the job role of the person named in ``FirstName`` / ``LastName`` in ``JobTitle``
        e.g. ``domains_create(FirstName='John', LastName='Doe', OrganizationName='ExampleCorp', JobTitle='Chief Technical Officer')``
        
        **Example Usage**::
        
            >>> api = Api('user', 'key', 'user', '12.34.56.78')
            >>> res = api.domains_create(
            ...     DomainName = 'somecooldomain.com',
            ...     FirstName = 'Jack',
            ...     LastName = 'Trotter',
            ...     Address1 = 'Ridiculously Big Mansion, Yellow Brick Road',
            ...     City = 'Tokushima',
            ...     StateProvince = 'Tokushima',
            ...     PostalCode = '771-0144',
            ...     Country = 'Japan',
            ...     Phone = '+81.123123123',
            ...     EmailAddress = 'jack.trotter@example.com'
            ... )
            >>> print(res)
            {
                'Domain': 'somecooldomain.com', 'Registered': 'true', 'ChargedAmount': '12.1600',
                'DomainID': '615026', 'OrderID': '2139371', 'TransactionID': '4139125',
                'WhoisguardEnable': 'true', 'FreePositiveSSL': 'false', 'NonRealTimeDomain': 'false'
            }
        
        **Automatically set nameservers on purchase**::
            
            >>> # For readability, we're not including the required contact information for these calls
            >>> # You can specify Nameservers as either a list [] of nameservers as strings
            >>> api.domains_create('anotherdomain.com', Nameservers=['ns1.example.com', 'ns2.example.com', 'ns3.example.com'])
            >>> # OR you can specify them as a comma separated string - it's up to your preference
            >>> # There is no difference in result whether you specify nameservers as a list or string
            >>> api.domains_create('anotherdomain.com', Nameservers='ns1.example.com,ns2.example.com,ns3.example.com')
        
        :raises ApiError: When ``<Error />`` in the result is non-empty.
        :return dict DomainCreateResult: The attributes of the result's ``<DomainCreateResult />`` as a dictionary
        """

        contact_types = ['Registrant', 'Tech', 'Admin', 'AuxBilling']

        extra_payload = {
            'DomainName': DomainName,
            'years': years
        }

        if WhoisGuard:
            extra_payload.update({
                'AddFreeWhoisguard': 'yes',
                'WGEnabled': 'yes',
            })
        if PromotionCode:
            extra_payload['PromotionCode'] = PromotionCode
        if Nameservers:
            if isinstance(Nameservers, (list, set, tuple)):
                Nameservers = ','.join(Nameservers)
            extra_payload['Nameservers'] = Nameservers
        
        for contact_type in contact_types:
            extra_payload.update({
                '%sFirstName' % contact_type: FirstName,
                '%sLastName' % contact_type: LastName,
                '%sAddress1' % contact_type: Address1,
                '%sCity' % contact_type: City,
                '%sStateProvince' % contact_type: StateProvince,
                '%sPostalCode' % contact_type: PostalCode,
                '%sCountry' % contact_type: Country,
                '%sPhone' % contact_type: Phone,
                '%sEmailAddress' % contact_type: EmailAddress,
            })
            if Address2:
                extra_payload['%sAddress2' % contact_type] = Address2
            if OrganizationName:
                extra_payload['%sOrganizationName' % contact_type] = OrganizationName
            if JobTitle:
                extra_payload['%sJobTitle' % contact_type] = JobTitle
        
        # Merge in any user payload key:value's on top of our generated payload dictionary
        extra_payload = {**extra_payload, **user_payload}
        
        xml = self._call('namecheap.domains.create', extra_payload)
        return self.get_element_dict(xml, 'DomainCreateResult')

    @staticmethod
    def get_element(element, element_name):
        # type: (Element, str) -> Element
        return element.find('.//{%(ns)s}%(el)s' % {'ns': NAMESPACE, 'el': element_name})

    @staticmethod
    def get_element_dict(element, element_name):
        # type: (Element, str) -> dict
        return dict(Api.get_element(element, element_name).items())

    def _payload(self, Command, extra_payload=None):
        # type: (str, dict) -> (dict, dict)
        """Make dictionary for passing to requests.post"""
        extra_payload = {} if extra_payload is None else extra_payload
        payload = {
            'ApiUser': self.ApiUser,
            'ApiKey': self.ApiKey,
            'UserName': self.UserName,
            'ClientIP': self.ClientIP,
            'Command': Command,
        }
        # Namecheap recommends to use HTTPPOST method when setting more than 10 hostnames
        # https://www.namecheap.com/support/api/methods/domains-dns/set-hosts.aspx
        if len(extra_payload) < self.payload_limit:
            payload.update(extra_payload)
            extra_payload = {}
        return payload, extra_payload

    def _fetch_xml(self, payload, extra_payload=None):
        # type: (dict, dict) -> Element
        """Make network call and return parsed XML element"""
        attempts_left = self.attempts_count
        while attempts_left > 0:
            if extra_payload:
                r = requests.post(self.endpoint, params=payload, data=extra_payload)
            else:
                r = requests.post(self.endpoint, params=payload)
            if 200 <= r.status_code <= 299:
                break
            if attempts_left <= 1:
                # Here we provide 1 error code which is not present in official docs
                raise ApiError('1', 'Did not receive 200 (Ok) response')
            if self.debug:
                print('Received status %d ... retrying ...' % (r.status_code))
            time.sleep(self.attempts_delay)
            attempts_left -= 1

        if self.debug:
            print("--- Request ---")
            print(r.url)
            print(extra_payload)
            print("--- Response ---")
            print(r.text)
        xml = fromstring(r.text)

        if xml.attrib['Status'] == 'ERROR':
            # Response namespace must be prepended to tag names.
            xpath = './/{%(ns)s}Errors/{%(ns)s}Error' % {'ns': NAMESPACE}
            error = xml.find(xpath)
            raise ApiError(error.attrib['Number'], error.text)

        return xml

    def _call(self, Command, extra_payload=None):
        # type: (str, dict) -> Element
        """Call an API command"""
        extra_payload = {} if extra_payload is None else extra_payload
        payload, extra_payload = self._payload(Command, extra_payload)
        xml = self._fetch_xml(payload, extra_payload)
        return xml

    class LazyGetListIterator(object):
        """When listing domain names, only one page is returned
        initially. The list needs to be paged through to see all.
        This iterator gets the next page when necessary."""
        def _get_more_results(self):
            xml = self.api._fetch_xml(self.payload)
            xpath = './/{%(ns)s}CommandResponse/{%(ns)s}DomainGetListResult/{%(ns)s}Domain' % {'ns': NAMESPACE}
            domains = xml.findall(xpath)
            for domain in domains:
                self.results.append(domain.attrib)
            self.payload['Page'] += 1

        def __init__(self, api, payload):
            self.api = api
            self.payload = payload
            self.results = []
            self.i = -1

        def __iter__(self):
            return self

        def __next__(self):
            self.i += 1
            if self.i >= len(self.results):
                self._get_more_results()

            if self.i >= len(self.results):
                raise StopIteration
            else:
                return self.results[self.i]
        next = __next__

    # https://www.namecheap.com/support/api/methods/domains-dns/set-default.aspx
    def domains_dns_setDefault(self, domain):
        # type: (str) -> dict
        sld, tld = domain.split(".")
        xml = self._call("namecheap.domains.dns.setDefault", {
            'SLD': sld,
            'TLD': tld
        })
        return self.get_element_dict(xml, 'DomainDNSSetDefaultResult')
    
    # https://www.namecheap.com/support/api/methods/domains/check.aspx
    def domains_check(self, domains):
        # type: (str or list) -> dict
        """Checks the availability of domains.

        For example
        api.domains_check(['taken.com', 'apsdjcpoaskdc.com'])

        Might result in
        {
            'taken.com' : False,
            'apsdjcpoaskdc.com' : True
        }
        """

        # For convenience, allow a single domain to be given
        if not inPy3k:
            if isinstance(domains, basestring):
                return self.domains_check([domains]).items()[0][1]
        else:
            if isinstance(domains, str):
                return list(self.domains_check([domains]).items())[0][1]

        extra_payload = {'DomainList': ",".join(domains)}
        xml = self._call('namecheap.domains.check', extra_payload)
        xpath = './/{%(ns)s}CommandResponse/{%(ns)s}DomainCheckResult' % {'ns': NAMESPACE}
        results = {}
        for check_result in xml.findall(xpath):
            results[check_result.attrib['Domain']] = check_result.attrib['Available'] == 'true'
        return results

    @classmethod
    def _tag_without_namespace(cls, element):
        return element.tag.replace("{%s}" % NAMESPACE, "")

    @classmethod
    def _list_of_dictionaries_to_numbered_payload(cls, l):
        """
        [
            {'foo' : 'bar', 'cat' : 'purr'},
            {'foo' : 'buz'},
            {'cat' : 'meow'}
        ]

        becomes

        {
            'foo1' : 'bar',
            'cat1' : 'purr',
            'foo2' : 'buz',
            'cat3' : 'meow'
        }
        """
        return dict(sum([
            [(k + str(i + 1), v) for k, v in d.items()] for i, d in enumerate(l)
        ], []))

    @classmethod
    def _elements_names_fix(self, host_record):
        """This method converts received message to correct send format.

        API answers you with this format:

        {
            'Name' : '@',
            'Type' : 'URL',
            'Address' : 'http://news.ycombinator.com',
            'MXPref' : '10',
            'TTL' : '100'
        }

        And you should convert it to this one in order to sync the records:

        {
            'HostName' : '@',
            'RecordType' : 'URL',
            'Address' : 'http://news.ycombinator.com',
            'MXPref' : '10',
            'TTL' : '100'
        }
        """

        conversion_map = [
            ("Name", "HostName"),
            ("Type", "RecordType")
        ]

        for field in conversion_map:
            # if source field exists
            if field[0] in host_record:
                # convert it to target field and delete old one
                host_record[field[1]] = host_record[field[0]]
                del(host_record[field[0]])

        return host_record

    # https://www.namecheap.com/support/api/methods/domains/get-contacts.aspx
    def domains_getContacts(self, DomainName):
        """Gets contact information for the requested domain.
        There are many categories of contact info, such as admin and billing.

        The returned data is like:
        {
            'Admin' : {'FirstName' : 'John', 'LastName' : 'Connor', ...},
            'Registrant' : {'FirstName' : 'Namecheap.com', 'PhoneExt' : None, ...},
            ...
        }
        """
        xml = self._call('namecheap.domains.getContacts', {'DomainName': DomainName})
        xpath = './/{%(ns)s}CommandResponse/{%(ns)s}DomainContactsResult/*' % {'ns': NAMESPACE}
        results = {}
        for contact_type in xml.findall(xpath):
            fields_for_one_contact_type = {}
            for contact_detail in contact_type.findall('*'):
                fields_for_one_contact_type[self._tag_without_namespace(contact_detail)] = contact_detail.text
            results[self._tag_without_namespace(contact_type)] = fields_for_one_contact_type
        return results

    # https://www.namecheap.com/support/api/methods/domains-dns/set-hosts.aspx
    def domains_dns_setHosts(self, domain, host_records):
        # type: (str, list) -> dict
        """Sets the DNS host records for a domain.

        Example:

        api.domains_dns_setHosts('example.com', [
            {
                'HostName' : '@',
                'RecordType' : 'URL',
                'Address' : 'http://news.ycombinator.com',
                'MXPref' : '10',
                'TTL' : '100'
            }
        ])"""

        extra_payload = self._list_of_dictionaries_to_numbered_payload(host_records)
        sld, tld = domain.split(".")
        extra_payload.update({
            'SLD': sld,
            'TLD': tld
        })
        return self.get_element_dict(self._call("namecheap.domains.dns.setHosts", extra_payload), 'DomainDNSSetHostsResult')

    # https://www.namecheap.com/support/api/methods/domains-dns/set-custom.aspx
    def domains_dns_setCustom(self, domain, host_records):
        # type: (str, dict) -> dict
        """Sets the domain to use the supplied set of nameservers.

        Example:

        api.domains_dns_setCustom('example.com', { 'Nameservers' : 'ns1.example.com,ns2.example.com' })"""

        extra_payload = host_records
        sld, tld = domain.split(".")
        extra_payload['SLD'] = sld
        extra_payload['TLD'] = tld
        return self.get_element_dict(self._call("namecheap.domains.dns.setCustom", extra_payload), 'DomainDNSSetCustomResult')

    # https://www.namecheap.com/support/api/methods/domains-dns/get-hosts.aspx
    def domains_dns_getHosts(self, domain):
        # type: (str) -> list
        """Retrieves DNS host record settings. Note that the key names are different from those
        you use when setting the host records."""
        sld, tld = domain.split(".")
        extra_payload = {
            'SLD': sld,
            'TLD': tld
        }
        xml = self._call("namecheap.domains.dns.getHosts", extra_payload)
        xpath = './/{%(ns)s}CommandResponse/{%(ns)s}DomainDNSGetHostsResult/*' % {'ns': NAMESPACE}
        results = []
        for host in xml.findall(xpath):
            results.append(host.attrib)
        return results

    def domains_dns_addHost(self, domain, host_record):
        """This method is absent in original API. The main idea is to let user add one record
        while having zero knowledge about the others. Method gonna get full records list, add
        single record and push it to the API.

        Example:

        api.domains_dns_addHost('example.com', {
            "RecordType": "A",
            "HostName": "test",
            "Address": "127.0.0.1",
            "MXPref": 10,
            "TTL": 1800
        })
        """
        host_records_remote = self.domains_dns_getHosts(domain)

        print("Remote: %i" % len(host_records_remote))

        host_records_remote.append(host_record)
        host_records_remote = [self._elements_names_fix(x) for x in host_records_remote]

        print("To set: %i" % len(host_records_remote))

        extra_payload = self._list_of_dictionaries_to_numbered_payload(host_records_remote)
        sld, tld = domain.split(".")
        extra_payload.update({
            'SLD': sld,
            'TLD': tld
        })
        return self.get_element_dict(self._call("namecheap.domains.dns.setHosts", extra_payload), 'DomainDNSSetHostsResult')

    def domains_dns_delHost(self, domain, host_record):
        # type: (str, dict) -> dict or bool
        """This method is absent in original API as well. It executes non-atomic
        remove operation over the host record which has the following Type,
        Hostname and Address.

        Example:

        api.domains_dns_delHost('example.com', {
            "RecordType": "A",
            "HostName": "test",
            "Address": "127.0.0.1"
        })
        """
        host_records_remote = self.domains_dns_getHosts(domain)

        print("Remote: %i" % len(host_records_remote))

        host_records_new = []
        for r in host_records_remote:
            cond_type = r["Type"] == host_record["Type"]
            cond_name = r["Name"] == host_record["Name"]
            cond_addr = r["Address"] == host_record["Address"]

            if cond_type and cond_name and cond_addr:
                # skipping this record as it is the one we want to delete
                pass
            else:
                host_records_new.append(r)

        host_records_new = [self._elements_names_fix(x) for x in host_records_new]

        print("To set: %i" % len(host_records_new))

        # Check that we delete not more than 1 record at a time
        if len(host_records_remote) != len(host_records_new) + 1:
            sys.stderr.write(
                "Something went wrong while removing host record, delta > 1: %i -> %i, aborting API call.\n" % (
                    len(host_records_remote),
                    len(host_records_new)
                )
            )
            return False

        extra_payload = self._list_of_dictionaries_to_numbered_payload(host_records_new)
        sld, tld = domain.split(".")
        extra_payload.update({
            'SLD': sld,
            'TLD': tld
        })
        return self.get_element_dict(self._call("namecheap.domains.dns.setHosts", extra_payload), 'DomainDNSSetHostsResult')

    # https://www.namecheap.com/support/api/methods/domains-dns/get-list.aspx
    def domains_getList(self, ListType=None, SearchTerm=None, PageSize=None, SortBy=None):
        """Returns an iterable of dicts. Each dict represents one
        domain name the user has registered, for example
        {
            'Name': 'coolestfriends.com',
            'Created': '04/11/2012',
            'Expires': '04/11/2018',
            'ID': '8385859',
            'AutoRenew': 'false',
            'IsLocked': 'false',
            'User': 'Bemmu',
            'IsExpired': 'false',
            'WhoisGuard': 'NOTPRESENT'
        }
        """

        # The payload is a dict of GET args that is passed to
        # the lazy-loading iterator so that it can know how to
        # get more results.
        extra_payload = {'Page': 1}
        if ListType:
            extra_payload['ListType'] = ListType
        if SearchTerm:
            extra_payload['SearchTerm'] = SearchTerm
        if PageSize:
            extra_payload['PageSize'] = PageSize
        if SortBy:
            extra_payload['SortBy'] = SortBy
        payload, extra_payload = self._payload('namecheap.domains.getList', extra_payload)
        return self.LazyGetListIterator(self, payload)
