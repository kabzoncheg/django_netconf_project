from django.db import models


class Parent(models.Model):
    def compare(self, obj):
        # Possible to overload  excluded_keys for each Child class
        excluded_keys = '_state'
        return self._compare(self, obj, excluded_keys)

    def _compare(self, obj1, obj2, excluded_keys):
        """
        FOR FUTURE USE!
        Compares two instances of same class

        :param obj1: class instance 1
        :param obj2: class instance 2
        :param excluded_keys: model fields to exclude, when comparing
        :return: True if equal else Tuple with difference in Dictionaries
        """
        d1, d2 = obj1.__dict__, obj2.__dict__
        old, new = {}, {}
        for k, v in d1.items():
            if k in excluded_keys:
                continue
            try:
                if v != d2[k]:
                    old.update({k: v})
                    new.update({k: d2[k]})
            except KeyError:
                old.update({k: v})
        if old == new == {}:
            return True
        else:
            return old, new

        class Meta:
            abstract = True
            app_label = 'devices'


class Device (Parent):
    """
    Device class.
    Represents network device.

    :attr ip_address
        Is a mandatory upon creation. All other will be set after connection.

    :attr fqdn
        *OPTIONAL* Will be resolved to ip_address if ip_address is not set by a user.

    :attr up_time
        Must be chosen as maximum of 2 RE up time (if system has 2 RE)
    """
    ip_address = models.GenericIPAddressField('Devices management IP-address:', primary_key=True)
    description = models.CharField('Device description', max_length=300, blank=True)
    poll_flag = models.BooleanField('True for regularly polling this device', default=True)
    hostname = models.CharField('Device name:', max_length=63, editable=False, default='unknown')
    fqdn = models.CharField('Device FQDN:', max_length=63, default='unknown')
    model = models.CharField('Device hardware model:', max_length=50, editable=False, default='unknown')
    version = models.CharField('Device software version:', max_length=50, editable=False, default='unknown')
    serialnumber = models.CharField('Device S/N:', max_length=50, editable=False, default='unknown')
    up_time = models.CharField('Device uptime:', max_length=50, editable=False, default='unknown')
    two_re = models.BooleanField('Device has 2 RE (True/False)', editable=False, default=False)
    last_checked_time = models.DateTimeField('Device last checked time:', auto_now=True, editable=False)
    last_checked_status = models.BooleanField('True for UP, False for DOWN:', editable=False, default=False)

    def __str__(self):
        return self.ip_address

class DeviceInstance(Parent):
    """
    DeviceInstance class.
    Represents devices routing instance.
    """
    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    instance_name = models.CharField(max_length=100, editable=False)
    instance_type = models.CharField(max_length=30, editable=False, blank=True)
    router_id = models.GenericIPAddressField(editable=False, blank=True, null=True)
    instance_state = models.CharField(max_length=30, editable=False, blank=True)

    class Meta:
        unique_together = ('related_device', 'instance_name')


class InstanceRIB(Parent):
    """
    InstanceRIB class.
    Represents RIBs for each routing instance.
    """
    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    related_instance = models.ForeignKey(DeviceInstance, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=100, editable=False)

    class Meta:
        unique_together = ('related_device', 'related_instance', 'table_name')


class InstanceArpTable(Parent):
    """
    InstanceArptable class.
    Represents device arp table.
    Be cautious! In Juniper terms VPN is not exactly routing instance!
    So there is special DB field - "vpn" for each entry.
    """
    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    related_instance = models.ForeignKey(DeviceInstance, on_delete=models.CASCADE)
    mac_address = models.CharField(max_length=17, editable=False)
    ip_address = models.GenericIPAddressField(editable=False, blank=True, null=True)
    interface_name = models.CharField(max_length=100, editable=False, blank=True)
    hostname = models.CharField(max_length=100, editable=False, blank=True)
    vpn = models.CharField(max_length=100, editable=False, blank=True)

    class Meta:
        unique_together = ('related_device', 'related_instance', 'mac_address')


class InstanceRouteTable(Parent):
    """
    InstanceRouteTable class.
    Represents device route table.
    """
    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    related_rib = models.ForeignKey(InstanceRIB, on_delete=models.CASCADE)
    rt_destination_ip = models.GenericIPAddressField(editable=False)
    rt_destination_prefix = models.PositiveSmallIntegerField(editable=False)
    active_tag = models.BooleanField('True for *, False for other:', editable=False)
    protocol_name = models.CharField(max_length=20, editable=False, blank=True)
    preference = models.PositiveSmallIntegerField(editable=False, null=True)
    nh_local_interface = models.CharField(max_length=100, editable=False, blank=True)
    nh_table = models.CharField(max_length=100, editable=False, blank=True)
    nh_type = models.CharField(max_length=100, editable=False, blank=True)
    via = models.CharField(max_length=100, editable=False, blank=True)

    class Meta:
        unique_together = ('related_device', 'related_rib', 'rt_destination_ip',
                           'rt_destination_prefix')


class InstancePhyInterface(Parent):
    """
    InstanceInterface class.
    Represents device physical interfaces (stores info about them).
    """
    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    related_instance = models.ForeignKey(DeviceInstance, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, editable=False)
    admin_status = models.BooleanField('True for UP, False for DOWN:', editable=False, default=False)
    oper_status = models.BooleanField('True for UP, False for DOWN:', editable=False, default=False)
    speed = models.CharField(max_length=20, editable=False, blank=True)
    mtu = models.CharField(max_length=20, editable=False, blank=True)
    link_mode = models.CharField(max_length=20, editable=False, blank=True)
    if_auto_negotiation = models.CharField(max_length=20, editable=False, default=False)
    link_level_type = models.CharField(max_length=20, editable=False, blank=True)
    current_physical_address = models.CharField(max_length=34, editable=False, blank=True)
    hardware_physical_address = models.CharField(max_length=34, editable=False, blank=True)

    class Meta:
        unique_together = ('related_device', 'related_instance', 'name')


class InstanceLogInterface(Parent):
    """
    InstanceInterface class.
    Represents device logical interfaces (stores info about them).
    """
    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    related_instance = models.ForeignKey(DeviceInstance, on_delete=models.CASCADE)
    related_interface = models.ForeignKey(InstancePhyInterface, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, editable=False)
    address_family_name = models.CharField(max_length=50, editable=False, blank=True)
    encapsulation = models.CharField(max_length=20, editable=False, blank=True)
    mtu = models.CharField(max_length=20, editable=False, blank=True)
    ifa_local = models.GenericIPAddressField(editable=False, blank=True, null=True)
    ifa_prefix = models.SmallIntegerField(editable=False,  blank=True, null=True)
    input_packets = models.IntegerField(editable=False, blank=True, null=True)
    output_packets = models.IntegerField(editable=False, blank=True, null=True)
    filter_information = models.CharField(max_length=100, editable=False, blank=True)
    logical_interface_zone_name = models.CharField(max_length=100, editable=False, blank=True)

    class Meta:
        unique_together = ('related_device', 'related_instance', 'related_interface', 'name')


def device_config_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/configs/device_<id>/filename
    return 'configs/device_{0}/{1}'.format(instance.related_device_id, filename)


class DeviceConfig (Parent):
    """
    Device Configuration class.
    Represents configuration files for each device
    """
    related_device = models.ForeignKey(Device, on_delete=models.CASCADE)
    upload_path = models.FileField(upload_to=device_config_path)
    upload_time = models.DateTimeField(editable=False, auto_now=True)
