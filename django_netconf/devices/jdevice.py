import os

from jnpr.junos import Device


class _CheckModel:

    """
    Class _CheckModel
    Decorator class. When JunosDevices class instance has self.db_flag set to True,
        this decorator performs check if the model name (if specified) refers to actual
        Django model from ".models.py".
    Works with class _Wrapper only. _Wrapper retains both instances _CheckModel and JunosDevice.
    """
    def __init__(self, cmeth):
        self.cmeth = cmeth

    def __call__(self, *args, **kwargs):
        cmeth_result = self.cmeth(*args, **kwargs)
        if isinstance(cmeth_result, tuple):
            pass
        else:
            return cmeth_result
        if self.db_flag:
            import pyclbr
            model_names = [md for md in pyclbr.readmodule('models')]
            if cmeth_result[1] in model_names:
                return cmeth_result
            else:
                raise KeyError('Django model {} doesnot exist!'.format(cmeth_result[1]))
        else:
            return cmeth_result[0]

    def __get__(self, instance, owner):
        return _Wrapper(self, instance)


class _Wrapper:
    def __init__(self, desc, subj):
        self.desc = desc
        self.subj = subj
        self.desc.db_flag = subj.db_flag

    def __call__(self, *args, **kwargs):
        return self.desc(self.subj, *args, **kwargs)


class JunosDevice:

    """
    Base class for Junos devices.

    :attr:`hostname`: router hostname
    :attr:`user`: user for logging into `hostname`
    :attr:`password`: password for logging into `hostname`
    :attr:`timeout`: time to wait for a response
    :attr:`connection`: connection to `hostname`
    :attr: 'db_flag': if set tries to resolve Django model name
    """

    @_CheckModel
    def get_route_table(self):
        """
        A list of routes bound to current route-tables

        :returns: list of routes
        :rtype: list
        """
        model = 'InstanceRouteTable'
        table = []
        root = self._connection.rpc.get_route_information(all=True)
        for route_table in root:
            table_name = route_table.findtext('table-name')
            for route in route_table.findall('rt'):
                entry = dict((elt.tag, elt.text) for elt in route.iter() if not len(elt) and elt.text is not None)
                entry['table_name'] = table_name
                table.append(entry)
        return table, model

    @_CheckModel
    def get_phy_interface_list(self):
        """
        A list of physical interfaces with thier parameters

        :returns: list of interface
        :rtype: list
        """
        model = 'InstancePhyInterface'
        table = []
        root = self._connection.rpc.get_interface_information()
        for phy_int in root:
            entry = dict(
                (elt.tag, elt.text.strip()) for elt in phy_int.findall('./') if not len(elt) and elt.text is not None)
            entry['int-type'] = 'physical-interface'
            table.append(entry)
        return table, model

    @_CheckModel
    def get_log_interface_list(self):
        """
        A list of logical interfaces with thier parameters

        :returns: list of interface
        :rtype: list
        """
        model = 'InstanceLogInterface'
        table = []
        root = self._connection.rpc.get_interface_information()
        for phy_int in root:
            for log_int in phy_int.findall('logical-interface'):
                entry = dict(
                    (elt.tag, elt.text.strip()) for elt in log_int.iter() if not len(elt) and elt.text is not None)
                try:
                    unparsed_prefix = entry['ifa-destination']
                except KeyError:
                    pass
                else:
                    parsed_prefix = unparsed_prefix.split('/').pop()
                    entry['ifa-prefix'] = parsed_prefix
                finally:
                    entry['int-type'] = 'logical-interface'
                    table.append(entry)
        return table, model

    @_CheckModel
    def get_route_instance_list(self):
        """
        A list of routing instances with parameters

        :returns: list of routing instances
        :rtype: list
        """
        model = 'DeviceInstance'
        table = []
        root = self._connection.rpc.get_instance_information(detail=True)
        for route_inst in root:
            entry = {}
            for elt in route_inst.findall('*'):
                if not len(elt):
                    entry[elt.tag.replace('-', '_')] = elt.text
                if elt.tag == 'instance-interface':
                    entry['instance_interface_list'] = list(int_elt.text for int_elt in elt)
                if elt.tag == 'instance-rib':
                    entry['instance_rib_list'] = list(rib_elt.text for rib_elt in elt if rib_elt.tag == 'irib-name')
            table.append(entry)
        return table, model

    @_CheckModel
    def get_facts(self):
        """
        device
        :return: dict with Device facts
        """
        model = 'Device'
        self._facts['last_checked_status'] = True
        return self._facts, model

    @_CheckModel
    def get_arp_table(self, vpn='default'):
        """
        A list of ARP entries.

        :returns: ARP entries
        :rtype: list
        """

        model = 'InstanceArpTable'
        table = []
        old_table = self._connection.rpc.get_arp_table_information(vpn=vpn)
        for old_entry in old_table:
            if old_entry.tag != 'arp-table-entry':
                continue
            entry = dict(ip_address=old_entry.findtext('ip-address').strip(),
                         interface_name=old_entry.findtext('interface-name').strip(),
                         hostname=old_entry.findtext('hostname').strip(),
                         vpn=vpn,
                         mac_address=old_entry.findtext('mac-address').strip())
            table.append(entry)
        return table, model

    def __init__(self, *args, **kwargs):
        self.hostname = args[0] if len(args) else kwargs.get('host')
        self.user = kwargs.get('user', os.getenv('USER'))
        self.password = kwargs.get('password')
        self.timeout = kwargs.get('timeout')
        self.db_flag = kwargs.get('db_flag', False)

    def connect(self):
        dev = Device(host=self.hostname, user=self.user, passwd=self.password)
        dev.open()
        dev.timeout = self.timeout
        self._connection = dev
        self._facts = dev.facts
        return self

    def disconnect(self):
        if self._connection:
            self._connection.close()

if __name__ == '__main__':
    device = JunosDevice(host='10.0.1.1', password='Password12!', user='django', db_flag=True)
    device.connect()
    facts = device.get_facts()
    inst = device.get_route_instance_list()
    arp_t = device.get_arp_table()
    route_t = device.get_route_table()
    int_l = device.get_log_interface_list()
    int_p = device.get_phy_interface_list()
    device.disconnect()
    # print(arp_t)
    # print(facts)
    # print(inst)
    # print(int_l)
    # print(int_p)
