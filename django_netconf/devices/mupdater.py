import os
import sys

from django import setup as django_setup
from django.core.management import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError


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

        :return: True or error
        """
        for entry in self.data:
            updater_name = '_' + self.model_name.lower() + '_updater'
            if updater_name in ModelUpdater.__dict__:
                model_inst, cascade_model_inst = getattr(ModelUpdater, updater_name)(self, entry=entry)
            else:
                model_inst = self.ModelClass()
                cascade_model_inst = None
            for key in model_inst.__dict__.keys():
                if key in entry.keys():
                    setattr(model_inst, key, entry[key])
            model_inst.save()
            if cascade_model_inst:
                for inst in cascade_model_inst:
                    inst.save()
        return True

    def _device_updater(self, entry):
        """
        Modifies model_inst

        :return: None
        """
        model_inst = self.ModelClass()
        setattr(model_inst, 'ip_address', self.host)
        up_time = []
        for key in entry.keys():
            if key.startswith('RE'):
                up_time.append(entry[key]['up_time'])
        setattr(model_inst, 'up_time', max(up_time))
        return model_inst, None

    def _deviceinstance_updater(self, entry):
        """
        Modifies model_inst and cascade_model_inst

        :return: None
        """
        from devices.models import Device
        model_inst = self.ModelClass.objects.get_or_create(related_device=Device.objects.get(ip_address=self.host),
                                                           instance_name=entry['instance_name'])[0]
        cascade_model_inst = []
        if 'instance_rib_list' in entry:
            from devices.models import InstanceRIB
            for rib in entry['instance_rib_list']:
                rib_inst = InstanceRIB.objects.get_or_create(related_instance=model_inst, table_name=rib)[0]
                cascade_model_inst.append(rib_inst)
        return model_inst, cascade_model_inst

    @staticmethod
    def _instancearptable_updater(self, model_inst):
        print('TESTING. Specific ARP Table Updater')

    @staticmethod
    def _instanceroutetable_updater(self, model_inst):
        print('TESTING. Specific instance Route Table Updater')

    @staticmethod
    def _instancephyinterface_updater(self, model_inst):
        print('TESTING. Specific Instance Physical Interface Updater')

    @staticmethod
    def _instanceloginterface_updater(self, model_inst):
        print('TESTING. Specific Instance logical Interface Updater')

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        :attr: self.ModelClass. Class from Django devices app's models
                Relative import issue, beware!
                Doesn't work: from django_netconf.devices.models import ModelName.
                So it hast a form of: from devices.models import ModelName
                Possibly it is a Django bug! FIGURE IT OUT!

        :param args: Tuple, contains list with dictionary(s) with data, that
                    shoud be passed to Django model, and Django model name as string.
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
    hostn = '10.0.3.2'
    device = JunosDevice(host=hostn, password='Password12!', user='django', db_flag=True)
    device.connect()
    facts = device.get_facts()
    inst = device.get_route_instance_list()
    arp_t = device.get_arp_table()
    route_t = device.get_route_table()
    int_l = device.get_log_interface_list()
    int_p = device.get_phy_interface_list()
    device.disconnect()

    # print(facts)
    # print(inst)
    # print(route_t)

    facts_updater = ModelUpdater(facts, host=hostn).updater()
    instance_updater = ModelUpdater(inst, host=hostn).updater()
    # arp_updater = ModelUpdater(arp_t, host=hostn).updater()