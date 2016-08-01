Command Line Interface
======================

This package provides a command line interface for performing all major
functions required for setting up and managing a food computer instance.

Cloud
-----

The subcommand :code:`openag cloud` provides tools for selecting a cloud server
to use.

.. program-output:: openag cloud init --help

.. program-output:: openag cloud show --help

.. program-output:: openag cloud deinit --help

User
----

The subcommand :code:`openag user` provides tools for managing your user
account on the selected cloud server.

.. program-output:: openag user register --help

.. program-output:: openag user login --help

.. program-output:: openag user show --help

.. program-output:: openag user logout --help

Farm
----

The subcommand :code:`openag farm` provides tools for managing the cloud mirror
of your data. Essentially, you can create a "farm" on the server that
represents your food computer and then mirror your instance's data into it.

.. program-output:: openag farm create --help

.. program-output:: openag farm list --help

.. program-output:: openag farm init --help

.. program-output:: openag farm show --help

.. program-output:: openag farm deinit --help

DB
--

The subcommand :code:`openag db` provides tools for managing your local CouchDB
instance.

.. program-output:: openag db init --help

.. program-output:: openag db load_fixture --help
