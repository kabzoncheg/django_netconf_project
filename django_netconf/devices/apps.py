from django.apps import AppConfig
from django.db.models.signals import post_save, pre_save, pre_init, pre_migrate

class DeviceConfig(AppConfig):
    name = 'devices'
    verbose_name = 'Devices'

    def ready(self):
        MyModel = self.get_model('Device')
        from .signals import SomeSignal
        post_save.connect(receiver=SomeSignal, sender=MyModel)
        pre_save.connect(receiver=SomeSignal, sender=MyModel)
        pre_init.connect(receiver=SomeSignal, sender=MyModel)
        pre_save.connect(receiver=SomeSignal, sender=MyModel)
        pre_migrate.connect(receiver=SomeSignal, sender=MyModel)