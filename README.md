Network Management System (NMS) for Juniper Networks equipment.
Based on Django and junos-eznc.

Alpha version 1.0.0.

NMS consists of three major django-apps: devices, get and set.
    1) devices. Can connect to Junos-based network devices and perform predefined in devices/jdevice.py NETCONF get
    requests, parse results and store them in database. Works very slow with large amount of data (e.g routing tables
    with more than 100k entries). All device logic (connect to device/ get some output/parse results/ update database)
    implemented in following modules: devices/jdevice.py; devices/worker.py; devices/mupdater.py.
    Simultaneous device updates implemented with Threading.
    Django interaction with device logic implemented with RabbitMQ.
    2) get. Can connect to Junos-based network devices and perform user defined NETCONF get requests. Output is provided
    in .zip archives.
    Simultaneous device requests implemented with Threading.
    Django interaction with device logic implemented with RabbitMQ.
    3) set. Can connect to Junos-based network devices and perform user defined NETCONF set requests. Output is provided
    in .zip archives. Also provides storage for user configuration files.
    Simultaneous device requests implemented with Threading.
    Django interaction with device logic implemented with RabbitMQ.

TO DO for future releases:
    1) Automated tests fore core functionality.
    2) Add additional options for Device password/keys. Now system connects to all devices with single account.
    3) Implement software upgrade functionality.
    4) Optimise devices/mupdater.py
    5) Implement single error codes file.
    6) Add Option for log storage in seperate file. Now all logs are console only.
    7) Apply Daemon (common/daemon.py) for all workers.
    8) Implement view in devices app for adding multiple new devices.
    9) Implement option to dynamically disable/enable DB update with required information form devices/jdevice.py
    (meth_tuple).
