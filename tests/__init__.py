from openag.cli.config import Config

def mock_config(new_config):
    """
    Modify the openag.cli.config.Config class so that commands that write to
    the global configuration don't actually persist their changes and write to
    a dictionary instead.

    :param dic new_config: A dictionary to use as the new config object
    """
    def new__getitem__(self, key):
        return new_config[key]
    def new__setitem__(self, key, val):
        raise NotImplementedError()

    Config.__getitem__ = new__getitem__
    Config.__setitem__ = new__setitem__
