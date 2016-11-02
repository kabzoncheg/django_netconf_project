import os
import sys

from django import setup as django_setup
from django.core.management import settings
# from django.core.exceptions import ObjectDoesNotExist


class ModelUpdater:

    def updater(self):

        model_inst = self.ModelClass()
        updater_name = '_' + self.model_name.lower() + '_updater'
        if updater_name in ModelUpdater.__dict__:
            updater_result = getattr(ModelUpdater, updater_name)(self, model_inst)
        # else:
            # print('TESTING. No specific updaters')
        # print('self.ModelClass.__dict__ OUTPUT:', model_inst.__dict__)
        for key in model_inst.__dict__.keys():
            if key in self.data.keys():
                setattr(model_inst, key, self.data[key])
                model_inst.save()
                print(key)

    def _device_updater(self, model_inst):
        setattr(model_inst, 'ip_address', self.host)
        setattr(model_inst, 'last_checked_status', True)
        return model_inst

    def _deviceinstance_updater(self):
        print('TESTING. Specific Device Instance Updater')

    def _instancearptable_updater(self):
        print('TESTING. Specific ARP Table Updater')

    def _instanceroutetable_updater(self):
        print('TESTING. Specific instance Route Table Updater')

    def _instancephyinterface_updater(self):
        print('TESTING. Specific Instance Physical Interface Updater')

    def _instanceloginterface_updater(self):
        print('TESTING. Specific Instance logical Interface Updater')

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        :attr: self.ModelClass. Class from Django devices app's models
                Relative import issue, beware!
                Doesn't work: from django_netconf.devices.models import ModelName.
                So it hast a form of: from devices.models import ModelName
                Possibly it is a Django bug! FIGURE IT OUT!

        :param args: Tuple, contains dictionary with data, that shoud be passed to Django model,
                    and Django model name as string.
        :param kwargs: String, with JunosDevice IP-address
        """
        self.data = args[0][0]
        self.model_name = args[0][1]
        self.host = kwargs.get('host')
        # configure Django settings and import model class
        self._settings_setter()
        mod = __import__('devices.models', fromlist=[self.model_name])
        self.ModelClass = getattr(mod, self.model_name)

    @staticmethod
    def _settings_setter():
        """
        Staticmethod.
        Adds django_netconf project to sys.path (PATH) if it is not already there

        :return: None
        """
        if not settings.configured:
            project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(project_path)
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_netconf.config.settings')
            django_setup()

if __name__ == '__main__':
    from django_netconf.devices.jdevice import JunosDevice
    host = '10.0.1.1'
    device = JunosDevice(host=host, password='Password12!', user='django', db_flag=True)
    device.connect()
    facts = device.get_facts()
    inst = device.get_route_instance_list()
    arp_t = device.get_arp_table()
    route_t = device.get_route_table()
    int_l = device.get_log_interface_list()
    int_p = device.get_phy_interface_list()
    device.disconnect()

    print(facts)

    facts_updater = ModelUpdater(facts, host=host).updater()
    # arp_updater = ModelUpdater(arp_t, host=host).updater()