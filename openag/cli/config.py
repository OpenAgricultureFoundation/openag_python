import os
import json
import errno

CONFIG_FOLDER = os.path.join(os.path.expanduser("~"), ".openag")
CONFIG_FILE = os.path.join(CONFIG_FOLDER, "config.json")

class PersistentObj(object):
    def __init__(self, data, parent):
        self._data = data
        self._parent = parent

    def __getitem__(self, attr):
        val = self._data.get(attr, dict())
        self._data[attr] = val
        if isinstance(val, dict):
            return PersistentObj(val, self)
        else:
            return val

    def __setitem__(self, attr, value):
        self._data[attr] = value
        self._save()

    def __delitem__(self, attr):
        del self._data[attr]
        self._save()

    def __nonzero__(self):
        return bool(self._data)

    def _save(self):
        self._parent._save()

class Config(PersistentObj):
    def __init__(self):
        try:
            os.makedirs(CONFIG_FOLDER)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(CONFIG_FOLDER):
                pass
            else:
                raise
        try:
            with open(CONFIG_FILE) as f:
                self._data = json.load(f)
        except IOError:
            self._data = {}

    def _save(self):
        with open(CONFIG_FILE, "w+") as f:
            json.dump(self._data, f)
