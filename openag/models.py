"""
This file has an object model in it
"""
__all__ = [
    "Environment", "EnvironmentalDataPoint", "FirmwareModule",
    "FirmwareModuleType", "Recipe", "SoftwareModule", "SoftwareModuleType"
]

from voluptuous import Schema, Required, Any

Environment = Schema({
})
"""
An `Environment` represents a single homogenous controlled environment within a
system. A food computer usually consists of a single `Environment`, but larger
systems will often contain more than one `Environment`.

`Environments` currently have no fields.
"""

EnvironmentalDataPoint = Schema({
    Required("environment"): Any(str, unicode),
    Required("variable"): Any(str, unicode),
    Required("is_desired"): bool,
    "value": object,
    Required("timestamp"): float,
})
"""
An `EnvironmentalDataPoint` represents a single measurement or event in an
`Environment`.

.. py:attribute:: environment
    (str, required) The ID of the environment for which this point was measured
.. py:attribute:: variable
    (str, required) The type of measurement of event this represents (e.g.
    "air_temperature")
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

FirmwareModule = Schema({
    Required("type"): Any(str, unicode),
    "environment": Any(str, unicode),
    "arguments": list,
    "parameters": dict,
    "mappings": dict,
})
FirmwareModule.__doc__ = """
A `firmware module` typically drives a single physical peripheral (sensor or
actuator) in the system

.. py:attribute:: environment
    (str, required) The ID of the environment on which this peripheral acts
.. py:attribute:: type
    (str, required) The ID of the firmware module type of this object
.. py:attribute:: arguments
    (list) A list of argument values to pass to the module. There should be
    exactly as many items in this list as there are arguments in the firmware
    module type for this module that don't have a default value.
.. py:attribute:: parameters
    (dict) A dictionary mapping parameter name to parameter values. There must
    be an entry in this dictionary for every required parameter in the firmware
    module type of this firmware module.
.. py:attribute:: mappings
    (dict) A dictionary mapping ROS names to different ROS names. Keys are the
    names defined in the firmware module type and values are the names that
    should be used instead. This can be used, for example, to route the correct
    input into an actuator module with a generic input name such as `state`.
"""

FirmwareModuleType = Schema({
    "pio_id": int,
    Required("header_file"): Any(str, unicode),
    Required("class_name"): Any(str, unicode),
    "description": Any(str, unicode),
    Required("arguments", default=[]): list,
    Required("parameters", default={}): dict,
    Required("inputs", default={}): dict,
    Required("outputs", default={}): dict
})
FirmwareModuleType.__dic__ = """
A `firmware module type` represents a firmware library for interfacing with a
particular system peripheral. It is essentially a driver for a sensor or
actuator. The code itself should be registered with `platformio
<platformio.org>`_ and metadata about it should be stored in the OpenAg
database.

.. py:attribute:: pio_id
    (int) The platformio ID of the uploaded library
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
    dictionaries must contain the fields "name" and "type" (e.g. "int",
    "float") and can contain the fields "description" and "default".
.. py:attribute parameters
    (dict)
.. py:attribute:: inputs
    (dict) A nested dictionary mapping names of ROS topics to which
    this library subscribes to dictionaries containing information about those
    topics. The inner dictionary must contain the field "type", which is the
    ROS message type for the topic and can contain the field "description".
.. py:attribute:: outputs
    (dict) A nested dictionary mapping names of ROS topics to which this
    library publishes to dictionaries containing information about those
    topics. The inner dictionary must contain the field "type", which is the
    ROS message type for the topic and can contain the field "description".
"""

Recipe = Schema({
    Required("format"): Any(str, unicode),
    Required("operations"): object
})
Recipe.__doc__ = """
In order to allow for recipes to evolve, we have developed a very generic
recipe model. The idea behind the model is that the system runs a recipe
handler module which declares some list of recipe formats that it supports.
Recipes also declare what format they are. Thus, to define a new recipe format,
you can write a custom recipe handler module type that understands that format,
write recipes in the new format, and then use the rest of the existing system
as is.

.. py:attribute:: format
    (str, required) The format of the recipe
.. py:attribute:: operations
    (required) The actual content of the recipe, organized as specified for the
    format of this recipe
"""

SoftwareModule = Schema({
    "environment": Any(str, unicode),
    Required("type"): Any(str, unicode),
    "arguments": dict,
    "parameters": dict,
    "mappings": dict
})
SoftwareModule.__doc__ = """
A `software module` is an instance of an arbitrary program running on the
controller. It can listen to ROS topics, publish to ROS topics, and advertize
services.  Examples include the recipe handler and individual control loops.

.. py:attribute:: environment
    (str) The ID of the environment on which this software module acts.
.. py:attribute:: type
    (str, required) The ID of the software module type of this object
.. py:attribute:: arguments
    (dict) A dictionary mapping argument names to argument values. There
    should be an entry in this dictionary for every `argument` in the software
    module type of this software modules
.. py:attribute:: parameters
    (dict) A dictionary mapping ROS parameter names to parameter values. These
    parameters will be defined in the roslaunch XML file under the node for
    this software module.
.. py:attribute:: mappings
    (dict) A dictionary mapping ROS names to different ROS names. Keys are the
    names defined in the software module type and values are the names that
    should be used instead. This can be used, for example, to route the correct
    inputs into a control module with generic input names like `set_point` and
    `measured`.
"""

SoftwareModuleType = Schema({
    Required("package"): Any(str, unicode),
    Required("executable"): Any(str, unicode),
    Required("description"): Any(str, unicode),
    Required("arguments"): list,
    Required("parameters"): dict,
    Required("inputs"): dict,
    Required("outputs"): dict
})
SoftwareModuleType.__doc__ = """
A `software module type` is a program that can run on the controller. It can
listen to ROS topics, publish to ROS topics, and advertize services.  Examples
include the recipe handler and individual control loops. Software module types
are distributed as ROS packages.

.. py:attribute:: package
    (str, required) The name of the ROS package containing the code for this
    object
.. py:attribute:: executable
    (str, required) The name of the executable for this object
.. py:attribute:: description
    (str, required) Description of the library
.. py:attribute:: arguments
    (array, required) An array of dictionaries describing the command line
    arguments to be passed to this module. The dictionaries must contain the
    fields "name" and "type" (e.g. "int" or "float") and can contain the fields
    "description", "default", and "required".
.. py:attribute:: parameters
    (dict, required) A nested dictionary mapping names of ROS parameters read
    by this module to dictionaries describing those parameters. The inner
    dictionaries must contain the field "type" and can contain the fields
    "description" and "default".
.. py:attribute:: inputs
    (dict, required) A nested dictionary mapping names of ROS topics to which
    this library subscribes to dictionaries containing information about those
    topics. The inner dictionary must contain the field "type", which is the
    ROS message type for the topic and can contain the field "description".
.. py:attribute:: outputs
    (dict, required) A nested dictionary mapping names of ROS topics to which
    this library publishes to dictionaries containing information about those
    topics. The inner dictionary must contain the field "type", which is the
    ROS message type for the topic and can contain the field "description".
"""
