.. _writing-firmware-modules:

Writing Firmware Modules
========================

Firmware modules should be subclasses of the :cpp:class:`Module` class defined
in the `OpenAg Firmware Module
<https://github.com/OpenAgInitiative/openag_firmware_module>`_ repository. They
must define a :cpp:func:`begin` function that initializes the module itself.
This :cpp:func:`begin` function will be called in the :cpp:func:`setup`
function of the Arduino sketch generated for the project. They must also define
an :cpp:func:`update` function that updates the module (e.g. reads from a
sensor at some maximum rate). This :cpp:func:`update` function
will be called in the :cpp:func:`loop` function of the Arduino sketch generated
for the project. The module must also define a :cpp:member:`status_level`
attibute which is an 8-bit integer that can take on any of the values 0 (which
means that the module is "ok"), 1 (which means that there is some warning for
the module), or 2 (which means that there is an error preventing the module
from working as desired). Finally, it must define a :cpp:member:`status_msg`
which is a :cpp:class:`String` describing the status of the sensor. This is
generally an empty string when the status level is "ok" and an error message
when the status level is "warn" or "error".

In addition to these standard functions and attributes (which are all defined
in the header file for the :cpp:class:`Module` class), the module must define a
get function for each of its outputs and a set function for each of its inputs.
In particular, it must define a get function of the following form for each
output.

.. cpp:function:: bool get_OUTPUT_NAME(OUTPUT_TYPE &msg)

The function takes as argument an object of the desired message type, populates
the object with the current value of the output and returns True if and only if
the message should be published on the module output.

The module must also define a set function of the following form for each
input.

.. cpp:function:: void set_INPUT_NAME(INPUT_TYPE msg)

The function takes as argument an object of the desired message type populated
with the value being passed in as input and should immediately process the
message.

In addition the module should define a `module.json` file containing all of the
metadata about the firmware module. In particular, it should be an instance of
the :py:class:`openag.models.FirmwareModuleType` schema encoded as JSON.
