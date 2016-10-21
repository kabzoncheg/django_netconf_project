from os import getenv

from jnpr.junos import Device


class JunosDevice:

    """Base class for Junos devices.

    :attr:`hostname`: router hostname
    :attr:`user`: user for logging into `hostname`
    :attr:`password`: password for logging into `hostname`
    :attr:`timeout`: time to wait for a response
    :attr:`connection`: connection to `hostname`
    """

    @property
    def arp_table(self):
        """
        A list of ARP entries.

        :returns: ARP entries
        :rtype: list
        """
        table = []
        old_table = self._connection.rpc.get_arp_table_information(vpn=self.vpn)
        for old_entry in old_table:
            if old_entry.tag != 'arp-table-entry':
                continue
            entry = dict(ip_address=old_entry.findtext('ip-address').strip(),
                         interface=old_entry.findtext('interface-name').strip(),
                         hostname=self.hostname.strip(), vpn=self.vpn,
                         mac_address=old_entry.findtext('mac-address').strip())
            table.append(entry)
        return table

    @property
    def route_table(self):
        """
        A list of routes bound to current route-tables

        :return: list
        """
        table = []
        root = self._connection.rpc.get_route_information(all=True)
        for route_table in root:
            table_name = route_table.findtext('table-name')
            route_list = route_table.findall('rt')
            for route in route_list:
                entry = dict((attr.tag, attr.text) for attr in route.iter() if not len(attr) and attr.text is not None)
                entry['table_name'] = table_name
                table.append(entry)
        return table

    def __init__(self, *args, **kwargs):
        self.hostname = args[0] if len(args) else kwargs.get('host')
        self.user = kwargs.get('user', getenv('USER'))
        self.password = kwargs.get('password')
        self.timeout = kwargs.get('timeout')
        self.vpn = kwargs.get('vpn', 'default')

    def connect(self):
        """Connect to a device.
        :returns: a connection to a Juniper Networks device.
        :rtype: ``Device``
        """
        dev = Device(host=self.hostname, user=self.user, passwd=self.password)
        dev.open()
        dev.timeout = self.timeout
        self._connection = dev
        return self

    def disconnect(self):
        if self._connection:
            self._connection.close()

if __name__ == '__main__':
    dev = JunosDevice(host='10.0.1.1', user='django', password='Password12!')
    dev.connect()
    at = dev.arp_table
    rt = dev.route_table
    print('ROUTE TABLE', rt)
    #print('ARP TABLE', at)
    dev.disconnect()