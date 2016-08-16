Database Names
==============

The CouchDB server has a single database for each type of object defined in the
object model.

:py:class:`~openag.models.Environment` objects are stored in the "environment"
database.

:py:class:`~openag.models.EnvironmentalDataPoint` objects are stored in the
"environmental_data_point" database.

:py:class:`~openag.models.Recipe` objects are stored in the "recipes" database.

:py:class:`~openag.models.FirmwareModuleType` objects are stored in the
"firmware_module_type" database.

:py:class:`~openag.models.FirmwareModule` objects are stored in the
"firmware_module" database.

:py:class:`~openag.models.SoftwareModuleType` objects are stored in the
"software_module_type" database.

:py:class:`~openag.models.SoftwareModule` objects are stored in the
"software_module" database.
