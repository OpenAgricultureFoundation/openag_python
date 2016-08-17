__all__ = ["EnvVars"]

class EnvVar:
    items = set()

    def __init__(self, name, description, units=None):
        self.name = name
        self.__doc__ = description
        self.units = units
        self.items.add(self)

    def __str__(self):
        return self.name

AIR_TEMPERATURE = EnvVar(
    "air_temperature", "Temperature of the air in degrees Celcius", "degrees C"
)
AIR_HUMIDITY = EnvVar(
    "air_humidity",
    "A measure of the concentration of water in the air relative to the "
    "maximum concentration at the current temperature", "percent relative"
)
WATER_TEMPERATURE = EnvVar(
    "water_temperature", "Temperature of the air in degrees Celcius",
    "degrees C"
)
WATER_POTENTIAL_HYDROGEN = EnvVar(
    "water_potential_hydrogen", "Potential Hydrogen of the water", "pH"
)
WATER_ELECTRICAL_CONDUCTIVITY = EnvVar(
    "water_electrical_conductivity",
    "Electrical conductivity of the water in uS/cm", "uS/cm"
)
RECIPE_START = EnvVar("recipe_start", "Represents the start of a recipe")
RECIPE_END = EnvVar("recipe_end", "Represents the end of a recipe")
MARKER = EnvVar("marker", "Marks some user-defined event")
AERIAL_IMAGE = EnvVar(
    "aerial_image", "Image from above the tray looking down on the plants",
    "png"
)
FRONTAL_IMAGE = EnvVar(
    "frontal_image", "Image from in front of the tray looking towards the "
    "plants", "png"
)
