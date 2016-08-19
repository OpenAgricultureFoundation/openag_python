__all__ = [
    "Environment", "EnvironmentalDataPoint", "FirmwareModule",
    "FirmwareModuleType", "Recipe", "SoftwareModule", "SoftwareModuleType"
]

from voluptuous import Schema, Required, Any, Extra, REMOVE_EXTRA

Environment = Schema({
    "name": Any(str, unicode),
}, extra=REMOVE_EXTRA)
Environment.__doc__ = """
An :class:`Environment` abstractly represents a single homogenous
climate-controlled volume within a system. A food computer usually consists of
a single :class:`Environment`, but larger systems will often contain more than
one :class:`Environment`.
"""

EnvironmentalDataPoint = Schema({
    Required("environment"): Any(str, unicode),
    Required("variable"): Any(str, unicode),
    Required("is_manual", default=False): bool,
    Required("is_desired"): bool,
    "value": object,
    Required("timestamp"): float,
}, extra=REMOVE_EXTRA)
EnvironmentalDataPoint.__doc__ = """
An `EnvironmentalDataPoint` represents a single measurement or event in an
`Environment`, such as a single air temperature measurement or the start of a
recipe.

.. py:attribute:: environment

    (str, required) The ID of the environment for which this point was measured

.. py:attribute:: variable

    (str, required) The type of measurement of event this represents (e.g.
    "air_temperature"). The class
    :class:`~openag.var_types.EnvironmentalVariable` contains all valid
    variable names.

.. py:attribute:: is_manual

    (bool) This should be true if the data point represents a manual reading
    performed by a user and false if it represents an automatic reading from a
    firmware or software module. Defaults to false.

.. py:attribute:: is_desired

    (bool, required) This should be true if the data point represents the
    desired state of the environment (e.g. the set points of a recipe) and
    false if it represents the measured state of the environment.

.. py:attribute:: value

    The value associated with the measurement or event. The exact use of this
    field may very depending on the `variable` field.

.. py:attribute:: timestamp

    (float, required) A UNIX timestamp reflecting when this data point was
    generated.
"""

Recipe = Schema({
    "name": Any(str, unicode),
    "description": Any(str, unicode),
    Required("format"): Any(str, unicode),
    Required("operations"): object
}, extra=REMOVE_EXTRA)
Recipe.__doc__ = """
In order to allow for recipes to evolve, we have developed a very generic
recipe model. The idea behind the model is that the system runs a recipe
handler module which declares some list of recipe formats that it supports.
Recipes also declare what format they are. Thus, to define a new recipe format,
you can write a custom recipe handler module type that understands that format,
write recipes in the new format, and then use the rest of the existing system
as is. See :ref:`writing-recipes` for information on existing recipe formats
and how to write recipes with them.

.. py:attribute:: format

    (str, required) The format of the recipe

.. py:attribute:: operations

    (required) The actual content of the recipe, organized as specified for the
    format of this recipe
"""


FirmwareInput = Schema({
    Required("type"): Any(str, unicode),
    Required("categories", default=["actuators"]): ["actuators", "calibration"],
    "description": Any(str, unicode),
})
FirmwareOutput = Schema({
    Required("type"): Any(str, unicode),
    Required("categories", default=["sensors"]): ["sensors", "calibration"],
    "description": Any(str, unicode),
    "accuracy": float,
})

FirmwareArgument = Schema({
    Required("name"): Any(str, unicode),
    "type": Any("int", "float", "bool", "str"),
    "description": Any(str, unicode),
    "default": object,
}, extra=REMOVE_EXTRA)
CodeRepo = Schema({
    Required("type"): "git",
    Required("url"): Any(str, unicode)
})
FirmwareModuleType = Schema({
    "pio_id": int,
    "repository": CodeRepo,
    Required("header_file"): Any(str, unicode),
    Required("class_name"): Any(str, unicode),
    "description": Any(str, unicode),
    Required("arguments", default=[]): [FirmwareArgument],
    Required("inputs", default={}): {Extra: FirmwareInput},
    Required("outputs", default={}): {Extra: FirmwareOutput},
}, extra=REMOVE_EXTRA)
FirmwareModuleType.__doc__ = """
A :class:`FirmwareModuleType` represents a firmware library for interfacing
with a particular system peripheral. It is essentially a driver for a sensor or
actuator. The code itself should be registered with `PlatformIO
<http://platformio.org>`_ and metadata about it should be stored in the OpenAg
database. See :ref:`writing-firmware-modules` for information on how to write
firmware modules.

.. py:attribute:: pio_id

    (int) The PlatformIO ID of the uploaded library

.. py:attribute:: header_file

    (str, required) The name of the header file containing the top-level class
    in the library

.. py:attribute:: class_name

    (str, required) The name of the top-level class in the library

.. py:attribute:: description

    (str) Description of the library

.. py:attribute:: arguments

    (list) An array of dictionaries describing the arguments to be
    passed to the constructor of the top-level class of this module. The
    dictionaries must contain the fields "name" (the name of the argument) and
    "type" (one of "int", "float", "bool", and "str") and can contain the
    fields "description" (a short description of what the argument is for) and
    "default" (a default value for the argument in case no value is supplied).
    All arguments with a default value should be at the end of the list.

.. py:attribute:: inputs

    (dict) A nested dictionary mapping names of topics to which this library
    subscribes to dictionaries containing information about those topics. The
    inner dictionaries must contain the field "type" (the ROS message type
    expected for messages on the topic) and can contain the fields "categories"
    (a list of categories to which this input belongs. Must be a subset of
    ["actuators", "calibration"] and defaults to ["actuators"]) and
    "description" (a short description of what the input is for).

.. py:attribute:: outputs

    (dict) A nested dictionary mapping names of topics to which this library
    publishes to dictionaries containing information about those topics. The
    inner dictionary must contain the field "type" (the ROS message type
    expected for messages on the topic) and can contain the fields "categories"
    (a list of categories to which this output belongs. Must be a subset of
    ["sensors", "calibration"] and defaults to ["sensors"]) a "description" (a
    short description of what the output is for), and an "accuracy" (a float
    representing the maximum error of the output values).
"""

FirmwareModule = Schema({
    Required("type"): Any(str, unicode),
    "environment": Any(str, unicode),
    "arguments": [object],
    "mappings": dict,
}, extra=REMOVE_EXTRA)
FirmwareModule.__doc__ = """
A :class:`FirmwareModule` is a single instance of a
:class:`~openag.models.FirmwareModuleType` usually configured to control a
single physical sensor or actuator.

.. py:attribute:: type

    (str, required) The ID of the :class:`~openag.models.FirmwareModuleType` of
    this object

.. py:attribute:: environment

    (str, required) The ID of the :class:`~openag.models.Environment` on which
    this peripheral acts

.. py:attribute:: arguments

    (list) A list of argument values to pass to the module. There should be
    at least as many items in this list as there are arguments in the
    :class:`~openag.models.FirmwareModuleType` for this module that don't have
    a default value.

.. py:attribute:: mappings

    (dict) A dictionary mapping input/output names to different input/output
    names. Keys are the names defined in the firmware module type and values
    are the names that should be used instead. This can be used, for example,
    to route the correct input into an actuator module with a generic input
    name such as `state`.
"""

SoftwareInput = Schema({
    Required("type"): Any(str, unicode),
    "description": Any(str, unicode),
})
SoftwareOutput = Schema({
    Required("type"): Any(str, unicode),
    "description": Any(str, unicode),
})
SoftwareArgument = Schema({
    Required("name"): Any(str, unicode),
    "type": Any("int", "float", "bool", "str"),
    "description": Any(str, unicode),
    "default": object,
    Required("required", default=False): bool
})
Parameter = Schema({
    "type": Any("int", "float", "bool", "str"),
    "description": Any(str, unicode),
    "default": object,
    Required("required", default=False): bool
})
SoftwareModuleType = Schema({
    Required("package"): Any(str, unicode),
    Required("executable"): Any(str, unicode),
    "description": Any(str, unicode),
    Required("arguments", default=[]): [SoftwareArgument],
    Required("parameters", default={}): {Extra: Parameter},
    Required("inputs", default={}): {Extra: SoftwareInput},
    Required("outputs", default={}): {Extra: SoftwareOutput}
}, extra=REMOVE_EXTRA)
SoftwareModuleType.__doc__ = """
A :class:`SoftwareModuleType` is a ROS node that can be run on the controller
for the farm (e.g. Raspberry Pi). It can listen to ROS topics, publish to ROS
topics, and advertize services.  Examples include the recipe handler and
individual control loops. Software module types are distributed as ROS
packages.

.. py:attribute:: package

    (str, required) The name of the ROS package containing the code for this
    object

.. py:attribute:: executable

    (str, required) The name of the executable for this object

.. py:attribute:: description

    (str) Description of the library

.. py:attribute:: arguments

    (array, required) An array of dictionaries describing the command line
    arguments to be passed to this module. The inner dictionaries must contain
    the field "name" (the name of the argument)  and can contain the fields
    "type" (one of "int", "float", "bool", and "str"), "description" (a short
    description of what the argument is for), "required" (a boolean indicating
    whether or not this argument is required to be passed to the module.
    defaults to False) and "default" (a default value for the argument in case
    no value is supplied).  An argument should only have a default value if it
    is required.

.. py:attribute:: parameters

    (dict, required) A nested dictionary mapping names of ROS parameters read
    by this module to dictionaries describing those parameters. The inner
    dictionaries can contain the fields "type" (one of "int", "float", "bool",
    and "str") "description" (a short description of what the parameter is
    for), "required" (a boolean indicating whether or not this parameter is
    required to be defined), and "default" (a default value for the parameter
    in case no value is supplied). A parameter should only have a default value
    if it is required.

.. py:attribute:: inputs

    (dict) A nested dictionary mapping names of topics to which this library
    subscribes to dictionaries containing information about those topics. The
    inner dictionaries must contain the field "type" (the ROS message type
    expected for messages on the topic) and can contain the field "description"
    (a short description of what the input is for).

.. py:attribute:: outputs

    (dict) A nested dictionary mapping names of topics to which this library
    publishes to dictionaries containing information about those topics. The
    inner dictionary must contain the field "type" (the ROS message type
    expected for messages on the topic) and can contain the field "description"
    (a short description of what the output is for).
"""

SoftwareModule = Schema({
    Required("type"): Any(str, unicode),
    "namespace": Any(str, unicode),
    "environment": Any(str, unicode),
    "arguments": [object],
    "parameters": dict,
    "mappings": dict
}, extra=REMOVE_EXTRA)
SoftwareModule.__doc__ = """
A :class:`SoftwareModule` is a single instance of a
:class:`~openag.models.SoftwareModuleType`.

.. py:attribute:: type

    (str, required) The ID of the :class:`~openag.models.SoftwareModuleType` of
    this object

.. py:attribute:: namespace

    (str) The name of the ros namespace that should contain the ROS node for
    this software module. If no value is provided, the environment field is
    used instead. If no environment is provided, the module is placed in the
    global namespace.

.. py:attribute:: environment

    (str) The ID of the :class:`~openag.models.Environment` on which this
    :class:`SoftwareModule` acts.

.. py:attribute:: arguments

    (array) A list of argument values to pass to the module. there should be at
    least as many items in this list as there are arguments in the
    :class:`~openag.models.SoftwareModuleType` for this module that don't have
    a default value.

.. py:attribute:: parameters

    (dict) A dictionary mapping ROS parameter names to parameter values. These
    parameters will be defined in the roslaunch XML file under the node for
    this software module.

.. py:attribute:: mappings

    (dict) A dictionary mapping ROS names for topics or parameters to different
    ROS names. Keys are the names defined in the software module type and
    values are the names that should be used instead. This can be used, for
    example, to route the correct inputs into a control module with generic
    input names like `set_point` and `measured`.
"""

