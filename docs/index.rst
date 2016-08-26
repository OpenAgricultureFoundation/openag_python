.. openag_python documentation master file, created by
   sphinx-quickstart on Fri Jul 15 11:48:42 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

openag_python
=============

This library is the core of OpenAg's backend software. The code and
accompanying documentation define many of the standards on which the rest of
the software is built. It defines the object model for the database, the
structure of Arduino modules, and a command line interface for interacting
setting up and interacting with a system.

There is also ROS package `openag_brain
<https://github.com/OpenAgInitiative/openag_brain.git>`_ which runs on the food
computer. It is built on top of this library and provides things like control
loops, data persistence, and taking images from a USB camera.

.. toctree::
   :maxdepth: 2

   cli
   object_model
   db_names
   database_queries
   variable_types
   recipes
   firmware_modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

