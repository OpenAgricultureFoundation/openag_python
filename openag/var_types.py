class EnvVar:
    items = {}

    def __init__(self, name, description, units=None, groups=None):
        self.name = name
        self.__doc__ = description
        self.units = units
        self.items[self.name] = self
        # Assign one or more groups to this environmental variable.
        # Can be used to create collections of related variables.
        self.groups = groups or []

    def __str__(self):
        return self.name

GROUP_ENVIRONMENT = "environment"
GROUP_USER = "user"
GROUP_RECIPE = "recipe"
GROUP_CAMERA = "camera"

AIR_TEMPERATURE = EnvVar(
    "air_temperature", "Temperature of the air in degrees Celcius", "degrees C",
    groups=[GROUP_ENVIRONMENT]
)
AIR_HUMIDITY = EnvVar(
    "air_humidity",
    "A measure of the concentration of water in the air relative to the "
    "maximum concentration at the current temperature", "percent relative",
    groups=[GROUP_ENVIRONMENT]
)
AIR_CARBON_DIOXIDE = EnvVar(
    "air_carbon_dioxide", "The amount of Carbon Dioxide in the air",
    units="ppm",
    groups=[GROUP_ENVIRONMENT]
)
AIR_FLUSH_ON = EnvVar(
    "air_flush_on", "Turn on air flush (off by default)",
    groups=[GROUP_ENVIRONMENT]
)
WATER_TEMPERATURE = EnvVar(
    "water_temperature", "Temperature of the water in degrees Celcius",
    units="degrees C",
    groups=[GROUP_ENVIRONMENT]
)
WATER_POTENTIAL_HYDROGEN = EnvVar(
    "water_potential_hydrogen", "Potential Hydrogen of the water",
    units="pH",
    groups=[GROUP_ENVIRONMENT]
)
WATER_ELECTRICAL_CONDUCTIVITY = EnvVar(
    "water_electrical_conductivity", "Electrical conductivity of the water",
    units="uS/cm",
    groups=[GROUP_ENVIRONMENT]
)
WATER_OXIDATION_REDUCTION_POTENTIAL = EnvVar(
    "water_oxidation_reduction_potential",
    "Oxidation-reduction potential of the water",
    units="mV",
    groups=[GROUP_ENVIRONMENT]
)
WATER_DISSOLVED_OXYGEN = EnvVar(
    "water_dissolved_oxygen", "A measure of the amount of oxygen in the water",
    units="mg/L",
    groups=[GROUP_ENVIRONMENT]
)
WATER_LEVEL_HIGH = EnvVar(
    "water_level_high", "Is water above threshold?",
    groups=[GROUP_ENVIRONMENT]
)
NUTRIENT_FLORA_DUO_A = EnvVar(
    "nutrient_flora_duo_a", "FloraDuo nutrient A",
    groups=[GROUP_ENVIRONMENT]
)
NUTRIENT_FLORA_DUO_B = EnvVar(
    "nutrient_flora_duo_b", "FloraDuo nutrient B",
    groups=[GROUP_ENVIRONMENT]
)
LIGHT_ILLUMINANCE = EnvVar(
    "light_illuminance", "The intensity of light falling at the plants",
    units="lux",
    groups=[GROUP_ENVIRONMENT]
)
LIGHT_INTENSITY_RED = EnvVar(
    "light_intensity_red", "The intensity setting for light panel",
    units="percent relative",
    groups=[GROUP_ENVIRONMENT]
)
LIGHT_INTENSITY_BLUE = EnvVar(
    "light_intensity_blue", "The intensity setting for light panel",
    units="percent relative",
    groups=[GROUP_ENVIRONMENT]
)
LIGHT_INTENSITY_WHITE = EnvVar(
    "light_intensity_white", "The intensity setting for light panel",
    units="percent relative",
    groups=[GROUP_ENVIRONMENT]
)
RECIPE_START = EnvVar(
    "recipe_start", "Represents the start of a recipe",
    groups=[GROUP_RECIPE]
)
RECIPE_END = EnvVar(
    "recipe_end", "Represents the end of a recipe",
    groups=[GROUP_RECIPE]
)
MARKER = EnvVar(
    "marker", "Marks some user-defined event",
    groups=[GROUP_USER]
)
AERIAL_IMAGE = EnvVar(
    "aerial_image", "Image from above the tray looking down on the plants",
    units="png",
    groups=[GROUP_CAMERA]
)
FRONTAL_IMAGE = EnvVar(
    "frontal_image", "Image from in front of the tray looking towards the "
    "plants",
    units="png",
    groups=[GROUP_CAMERA]
)
