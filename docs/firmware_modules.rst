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
superclass) are :c:data:`OK` (which means that the module is "ok"),
:c:data:`WARN` (which means that there is some warning for the module), and
:c:data:`ERROR` (which means that there is an error preventing the module from
working as desired). The superclass also defines a :cpp:member:`status_msg`
attribute which is a :cpp:class:`String` that the firmware module should use to
describe the status of the module. This is generally an empty string when the
status level is "ok" and an error message when the status level is "warn" or
"error". Finally, the superclass defines a :cpp:member:`status_code` attribute
which is a :spp:class:`uint8_t` value that the firmware module should use to
describe the status of the module. This serves the same purpose as the 
:cpp:member:`status_msg` field. The `module.json` file (described in more
detail below) should contain a dictionary explaining the meaning of all valid
:cpp:member:`status_code` values for the module.

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

The system uses PlatformIO to compile Arduino sketches, so modules must also
define a `library.json` file meeting the PlatformIO specifications. To work
with our system, this file need only contain the fields `name` and `framework`.
The `name` field should be the name of the module, and the `framework` field
should have the value `arduino`.

Categories
==========

The OpenAg system defines a list of "categories" which can be used to describe
the functionality contained in a firmware/software module/input/output. For
example, the firmware module for the am2315 sensor itself belongs to the
"sensors" and "calibration" category because it outputs sensor data and has
inputs for calibration. The air temperature and air humidity outputs from this
firmware module belong to the "sensors" category because they represent sensor
readings, and the inputs to this module used for calibration belong to the
"calibration" category.

When flashing an Arduino, it is possible to specify a list of categories that
should be enabled. By default, all categories are enabled except for
"calibration". This allows the codegen system to generate one Arduino sketch to
use during normal operation and a different sketch to use for calibration that
enables the "calibration" inputs and disables the "actators", for example.

Examples
--------

The repository `openag_firmware_examples
<https://github.com/OpenAgInitiative/openag_firmware_examples>`_ provides some
examples of well-documented, simple firmware modules for reference.
