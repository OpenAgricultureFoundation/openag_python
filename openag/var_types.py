__all__ = ["env_vars"]

env_vars = set()

def env_var(var_name):
    env_vars.add(var_name)
    return var_name

AIR_TEMPERATURE = env_var("air_temperature")
AIR_HUMIDITY = env_var("air_humidity")
WATER_TEMPERATURE = env_var("water_temperature")
WATER_POTENTIAL_HYDROGEN = env_var("water_potential_hydrogen")
WATER_ELECTRICAL_CONDUCTIVITY = env_var("water_electrical_conductivity")
RECIPE_START = env_var("recipe_start")
RECIPE_END = env_var("recipe_end")
