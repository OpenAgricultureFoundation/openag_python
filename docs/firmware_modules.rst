.. _writing-firmware-modules:

Writing Firmware Modules
========================

Overview
--------

Firmware modules should be subclasses of the :cpp:class:`Module` class defined
in the `OpenAg Firmware Module
<https://github.com/OpenAgInitiative/openag_firmware_module>`_ repository. They
must define a :cpp:func:`begin` function that initializes the module itself.
This :cpp:func:`begin` function will be called in the :cpp:func:`setup`
function of the Arduino sketch generated for the project. They must also define
an :cpp:func:`update` function that updates the module (e.g. reads from a
sensor at some rate). This :cpp:func:`update` function will be called in the
:cpp:func:`loop` function of the Arduino sketch generated for the project. The
:cpp:class:`Module` superclass defines a :cpp:member:`status_level` attribute
which the firmware module should use to report its current status. Valid value
for this attribute (all defined in the header file for the :cpp:class:`Module`
superclass) are :cpp:obj:`OK` (which means that the module is "ok"), WARN
(which means that there is some warning for the module), and ERROR (which means
that there is an error preventing the module from working as desired). The
superclass also defines a :cpp:member:`status_msg` attribute which is a
:cpp:class:`String` that the firmware module should use to describe the status
of the module. This is generally an empty string when the status level is "ok"
and an error message when the status level is "warn" or "error".

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

I/O Categories
--------------

Inputs and output can define a list of "categories" to which they belong. There
are currenty only 3 valid categories: "sensors" (for sensor outputs),
"actuators" (for actuator outputs), and "calibration". The "sensors" and
"actuators" categories should be fairly self explanatory. The "calibration"
category is for inputs or output that should only be active when the use is in
the process of calibrating their system. This allows the codegen system to
generate one Arduino sketch to use during normal operation with all of the
"actuators" and "sensors" inputs and outputs and a different sketch to use for
calibration with only the "calibration" inputs and outputs.

Examples
--------

The `Binary Actuator module
<https://github.com/OpenAgInitiative/openag_binary_actuator>`_ is an example of
a minimal firmware module and can be used for reference in writing your own.
