__all__ = ["all_dbs", "global_dbs", "per_farm_dbs"]

all_dbs = set()
global_dbs = set()
per_farm_dbs = set()

def global_db(db):
    all_dbs.add(db)
    global_dbs.add(db)
    return db

def per_farm_db(db):
    all_dbs.add(db)
    per_farm_dbs.add(db)
    return db

RECIPE = global_db("recipes")
SOFTWARE_MODULE_TYPE = global_db("software_module_type")
SOFTWARE_MODULE = per_farm_db("software_module")
FIRMWARE_MODULE_TYPE = global_db("firmware_module_type")
FIRMWARE_MODULE = per_farm_db("firmware_module")
ENVIRONMENT = per_farm_db("environment")
ENVIRONMENTAL_DATA_POINT = per_farm_db("environmental_data_point")
