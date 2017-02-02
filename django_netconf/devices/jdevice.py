# TO DO: Error handling; Tests
import os
import re
from lxml import etree

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
                entry = dict((elt.tag.replace('-', '_'), elt.text) for elt in route.iter()
                             if not len(elt) and elt.text is not None)
                # entry['rt_destination_ip'], entry['rt_destination_prefix']
                # and entry['active_tag'] for database normalization
                entry['rt_destination_ip'], entry['rt_destination_prefix'] = entry['rt_destination'].split('/')
                entry['rt_destination_prefix'] = int(entry['rt_destination_prefix'])
                entry['table_name'] = table_name
                entry['active_tag'] = True if entry['active_tag'] == '*' else False
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
                (elt.tag.replace('-', '_'), elt.text.strip()) for elt in phy_int.findall('./')
                if not len(elt) and elt.text is not None)
            entry['int_type'] = 'physical-interface'
            # For database normalization
            entry['oper_status'] = True if entry['oper_status'] == 'up' else False
            entry['admin_status'] = True if entry['admin_status'] == 'up' else False
            table.append(entry)

        # Binding instance name to interface
        route_instance = self.get_route_instance_list()[0] if self.db_flag else self.get_route_instance_list()
        int_to_inst = {}
        for elt in route_instance:
            if 'instance_interface_list' in elt:
                entry = dict((int_name, elt['instance_name']) for int_name in elt['instance_interface_list'])
                int_to_inst.update(entry)
        for entry in table:
            for elt in int_to_inst.keys():
                if elt == entry['name']:
                    entry['instance_name'] = int_to_inst[elt]
                    break
                else:
                    entry['instance_name'] = 'master'

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
            parent_int_name = phy_int.findall('name')[0].text.strip('\n')
            for log_int in phy_int.findall('logical-interface'):
                entry = dict(
                    (elt.tag.replace('-', '_'), elt.text.strip()) for elt in log_int.iter()
                    if not len(elt) and elt.text is not None)
                if 'ifa_destination' in entry and entry['ifa_destination'].__contains__('/'):
                    unparsed_prefix = entry['ifa_destination']
                    entry['ifa_prefix'] = unparsed_prefix.split('/').pop()
                entry['parent_int_name'] = parent_int_name
                entry['admin_status'] = False if log_int.findall('*/iff-down') else True
                table.append(entry)

        # Binding instance name to interface
        route_instance = self.get_route_instance_list()[0]
        int_to_inst = {}
        for elt in route_instance:
            if 'instance_interface_list' in elt:
                entry = dict((int_name, elt['instance_name']) for int_name in elt['instance_interface_list'])
                int_to_inst.update(entry)
        for entry in table:
            for elt in int_to_inst.keys():
                if elt == entry['name']:
                    entry['instance_name'] = int_to_inst[elt]
                    break
                else:
                    entry['instance_name'] = 'master'

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
            entry['instance_interface_list'] = []
            entry['instance_rib_list'] = []
            for int_name in route_inst.iter('interface-name'):
                entry['instance_interface_list'].append(int_name.text)
            for int_name in route_inst.iter('irib-name'):
                entry['instance_rib_list'].append(int_name.text)
            table.append(entry)
        return table, model

    @_CheckModel
    def get_instance_rib_list(self):
        """
        A list of routing instances RIB names

        :returns: list of routing instances RIB names
        :rtype: list
        """
        model = 'InstanceRIB'
        table = []
        route_instance = self.get_route_instance_list()[0] if self.db_flag else self.get_route_instance_list()
        for elt in route_instance:
            while elt['instance_rib_list']:
                entry = {elt['instance_name']: elt['instance_rib_list'].pop()}
                table.append(entry)

        return table, model

    @_CheckModel
    def get_facts(self):
        """
        device
        :return: dict with Device facts
        """
        model = 'Device'
        table = []
        self._facts['last_checked_status'] = True
        table.append(self._facts)
        return table, model

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
        self.auto_probe = kwargs.get('auto_probe', 0)

    @classmethod
    def all_get_methods(cls):
        """
        Returns tuple with correct order of get_methods names.
        It can be used later by worker.py module

        :return: tuple
        """
        meth_tuple = ('get_facts', 'get_route_instance_list', 'get_instance_rib_list',
                    'get_arp_table', 'get_phy_interface_list', 'get_log_interface_list',
                    'get_route_table')
        for key in cls.__dict__.keys():
            if re.match('^get_', key):
                if key not in meth_tuple:
                    err_text = '{} class get-method name {} ' \
                               'is not in meth_tuple: {}'.format(cls.__name__, key, meth_tuple)
                    raise KeyError(err_text)
        for key in meth_tuple:
            if key not in cls.__dict__.keys():
                err_text = 'meth_tuple contains bogus {} class get-method name {}'.format(cls.__name__, key)
                raise KeyError(err_text)
        return meth_tuple

    def connect(self):
        dev = Device(host=self.hostname, user=self.user, passwd=self.password, auto_probe=self.auto_probe)
        dev.open()
        dev.timeout = self.timeout
        self._connection = dev
        self._facts = dev.facts
        return self

    def disconnect(self):
        if self._connection:
            self._connection.close()

    def xml(self, request):
        return self._connection.execute(request)

    def rpc(self, rpc_meth, kwarg_name=None, kwarg_value=None):
        if kwarg_name:
            response = getattr(self._connection.rpc, rpc_meth)(**{kwarg_name: kwarg_value})
            print(response)
        else:
            response = getattr(self._connection.rpc, rpc_meth)()
        return response

    def cli(self, request):
        return self._connection.cli(request)


if __name__ == '__main__':
    # TEMP. While normal tests not implemented
    raw_xml = '<get-chassis-inventory>' \
                     '    <detail/>' \
                     '</get-chassis-inventory>'

    rpc_method_name = 'get_interface_information'
    rpc_kwarg_key = 'terse'
    rpc_kwarg_value = True

    cli_show_cmd = 'show route'

    device = JunosDevice(host='10.0.1.1', password='Password12!', user='django', db_flag=True, auto_probe=5)
    device.connect()

    facts = device.get_facts()
    inst = device.get_route_instance_list()
    inst_rib = device.get_instance_rib_list()
    arp_t = device.get_arp_table()
    route_t = device.get_route_table()
    int_l = device.get_log_interface_list()
    int_p = device.get_phy_interface_list()
    all_methods = device.all_get_methods()

    xml_request = device.xml(raw_xml)
    rpc_request = device.rpc(rpc_method_name, rpc_kwarg_key, rpc_kwarg_value)
    cli_request = device.cli(cli_show_cmd)

    device.disconnect()

    # print(arp_t)
    # print(facts)
    # print(inst)
    # print(inst_rib)
    # print(int_l)
    # print(int_p)
    # print(all_methods)

    # xml_request
    etree.dump(rpc_request)
    # print(cli_request)
