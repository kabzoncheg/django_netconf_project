# TO DO: Error handling, Tests

from django_netconf.common.setsettings import set_settings


class ModelUpdater:

    """
    Base class for updating Django models
    """

    def updater(self):
        """
        Default updater method.

        On call can update multiple instances of one model class. Parameters for each instance
            should be passed as dictionaries within single list in :attr self.data.
        To successfully save results in database, specific Django model attributes must match
            dict keys. In other case specific static method must be created.
        If there is no entry in database for specific instance, it will be created on
            successful model save() method.
        Invokes one of specific  static methods (if defined).
        Specific static methods must follow naming convention, refer to :attr: updater_name.

        Some Django models cannot be updated before another, for example DeviceInstance cannot
            be updated if related Device entry does not exist! Handling this is purpose of
            another modules (worker.py)

        :return: True or error
        """
        if self.model_name != 'Device':
            old_db_snapshot = self.ModelClass.objects.filter(related_device_id=self.host)
        instances_to_save_snapshot = []
        for entry in self.data:
            updater_name = '_' + self.model_name.lower() + '_updater'
            if updater_name in ModelUpdater.__dict__:
                model_inst = getattr(self, updater_name)(entry=entry)
            else:
                model_inst = self.ModelClass()
            for key in model_inst.__dict__.keys():
                if key in entry.keys():
                    setattr(model_inst, key, entry[key])
            instances_to_save_snapshot.append(model_inst)
            model_inst.save()
        if self.model_name != 'Device' and old_db_snapshot:
            self._cleaner(old_db=old_db_snapshot, new_db=instances_to_save_snapshot)
        return True

    @staticmethod
    def _cleaner(old_db, new_db):
        """
        Deletes entries from database table, that are not passed with latest updates,
        e.g outdated entries (info about old routes, deleted interfaces, etc.)

        :param old_db: outdated entries in DB to check
        :param new_db: latest entries to be written in DB
        """
        for old_obj in old_db:
            if old_obj not in new_db:
                old_obj.delete()

    def _device_updater(self, entry):
        """
        Creates instance of Device model class.

        :return: Device instance
        """
        model_inst = self.ModelClass.objects.get_or_create(ip_address=self.host)[0]
        up_time = []
        for key in entry.keys():
            if key.startswith('RE'):
                up_time.append(entry[key]['up_time'])
        if up_time:
            setattr(model_inst, 'up_time', max(up_time))
        return model_inst

    def _deviceinstance_updater(self, entry):
        """
        Creates instance of DeviceInstance model class.

        :return: DeviceInstance instance
        """
        # related_device_id - is a Django 'magic'. Model argument is related_devices,
        #   if it is used, instance of Device class should be passed as parameter
        model_inst = self.ModelClass.objects.get_or_create(related_device_id=self.host,
                                                           instance_name=entry['instance_name'])[0]
        return model_inst

    def _instancerib_updater(self, entry):
        from devices.models import DeviceInstance
        related_instance_inst = DeviceInstance.objects.get(related_device_id=self.host, instance_name=list(entry)[0])
        model_inst = self.ModelClass.objects.get_or_create(related_device_id=self.host,
                                                           related_instance=related_instance_inst,
                                                           table_name=list(entry.values())[0])[0]
        return model_inst

    def _instancearptable_updater(self, entry):
        """
        Creates instance of InstanceArpTable model class.

        :return: InstanceArpTable instance
        """
        from devices.models import DeviceInstance
        if entry['vpn'] == 'default':
            instance_name = 'master'
        else:
            instance_name = entry['vpn']
        related_instance_inst = DeviceInstance.objects.get(related_device_id=self.host,
                                                           instance_name=instance_name)
        model_inst = self.ModelClass.objects.get_or_create(related_device_id=self.host,
                                                           related_instance=related_instance_inst,
                                                           mac_address=entry['mac_address'])[0]
        return model_inst

    def _instanceroutetable_updater(self, entry):
        """
        Creates instance of InstanceRouteTable model class.

        :return: InstanceRouteTable instance
        """
        from devices.models import InstanceRIB
        related_rib_inst = InstanceRIB.objects.get(related_device_id=self.host, table_name=entry['table_name'])
        model_inst = self.ModelClass.objects.get_or_create(related_device_id=self.host, related_rib= related_rib_inst,
                                                          rt_destination_ip=entry['rt_destination_ip'],
                                                          rt_destination_prefix=entry['rt_destination_prefix'],
                                                          active_tag=entry['active_tag'])[0]
        return model_inst

    def _instancephyinterface_updater(self, entry):
        """
        Creates instance of InstancePhyInterface model class.

        :return: InstancePhyInterface instance
        """
        from devices.models import DeviceInstance
        related_instance_inst = DeviceInstance.objects.get(related_device_id=self.host,
                                                           instance_name=entry['instance_name'])
        model_inst = self.ModelClass.objects.get_or_create(related_device_id=self.host, name=entry['name'],
                                                           related_instance=related_instance_inst)[0]
        return model_inst

    def _instanceloginterface_updater(self, entry):
        """
        Creates instance of InstanceLogInterface model class.

        :return: InstanceLogInterface instance
        """
        from devices.models import DeviceInstance, InstancePhyInterface
        related_instance_inst = DeviceInstance.objects.get(related_device_id=self.host,
                                                           instance_name=entry['instance_name'])
        related_phy_inst = InstancePhyInterface.objects.get(related_device_id=self.host, name=entry['parent_int_name'])
        model_inst = self.ModelClass.objects.get_or_create(related_device_id=self.host, name=entry['name'],
                                                           related_instance=related_instance_inst,
                                                           related_interface=related_phy_inst)[0]
        return model_inst

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        :attr: self.ModelClass. Class from Django devices app's models.
                Relative import issue, beware!
                Doesn't work: from django_netconf.devices.models import ModelName.
                So it hast a form of: from devices.models import ModelName.
                Possibly it is a Django bug! FIGURE IT OUT!

        :param args: Tuple, contains list with dictionary(s) with data, that
                    shoud be passed to Django model, and Django model name as string.
        :param kwargs: String, with JunosDevice IP-address
        """
        self.data = args[0][0]
        self.model_name = args[0][1]
        self.host = kwargs.get('host')
        # configure Django settings and import model class
        set_settings()
        mod = __import__('devices.models', fromlist=[self.model_name])
        self.ModelClass = getattr(mod, self.model_name)


if __name__ == '__main__':
    # TEMP. While normal tests not implemented
    from django_netconf.common.jdevice import JunosDevice
    hosts_list = ['10.0.1.1', '10.0.3.2']
    for hostn in hosts_list:
        device = JunosDevice(host=hostn, password='Password12!', user='django', db_flag=True)
        device.connect()
        facts = device.get_facts()
        instance = device.get_route_instance_list()
        inst_rib = device.get_instance_rib_list()
        arp_t = device.get_arp_table()
        route_t = device.get_route_table()
        int_l = device.get_log_interface_list()
        int_p = device.get_phy_interface_list()
        device.disconnect()

        print(facts)
        print('Instance:', instance)
        print('Instance RIB:', inst_rib)
        print('ARP Table for {}: {}'.format(hostn, arp_t))
        print('Route Table for {}: {}'.format(hostn, route_t))
        print('Physical interface for {}: {}'.format(hostn, int_p))
        print('Logical interface for {}: {}'.format(hostn, int_l))

        # Order of updating models is significant!!!
        facts_updater = ModelUpdater(facts, host=hostn).updater()
        instance_updater = ModelUpdater(instance, host=hostn).updater()
        instance_rib_updater = ModelUpdater(inst_rib, host=hostn).updater()
        arp_updater = ModelUpdater(arp_t, host=hostn).updater()
        route_updater = ModelUpdater(route_t, host=hostn).updater()
        phy_updater = ModelUpdater(int_p, host=hostn).updater()
        log_updater = ModelUpdater(int_l, host=hostn).updater()
