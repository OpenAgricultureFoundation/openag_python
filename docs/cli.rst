Command Line Interface
======================

This package provides a command line interface for performing all major
functions required for setting up and managing a food computer instance.

Cloud
-----

The subcommand :code:`openag cloud` provides tools for selecting a cloud server
to use, managing your user account on that server, and managing a farm instance
on the server which serves as a mirror for your local instance.

.. program-output:: openag cloud init --help

.. program-output:: openag cloud show --help

.. program-output:: openag cloud deinit --help

.. program-output:: openag cloud register --help

.. program-output:: openag cloud login --help

.. program-output:: openag cloud show --help

.. program-output:: openag cloud logout --help

.. program-output:: openag cloud create_farm --help

.. program-output:: openag cloud list_farms --help

.. program-output:: openag cloud init_farm --help

.. program-output:: openag cloud deinit_farm --help

DB
--

The subcommand :code:`openag db` provides tools for managing your local CouchDB
instance.

.. program-output:: openag db init --help

.. program-output:: openag db show --help

.. program-output:: openag db load_fixture --help

.. program-output:: openag db deinit --help

.. program-output:: openag db clear --help

Firmware
--------

The subcommand :code:`openag firmware` provides tools for generating and
compiling code to run on the microcontroller of the system.

.. program-output:: openag firmware init --help

.. program-output:: openag firmware run --help

.. program-output:: openag firmware run_module --help
