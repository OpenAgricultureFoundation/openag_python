.. _writing-recipes:

Writing Recipes
===============

There is currently only 1 supported recipe format, but the system is designed
to allows new formats to be developed over time.

Simple Recipes
--------------

The "simple" recipe format conceptualizes recipes as a sequential list of set
points for environmental variables. It doesn't take into account the expression
of the plants being grown at all.

In particular, a "simple" recipe is a list of 3-element lists with the
following structure::

    [<offset>, <variable_type>, <value>]

Where `<offset>` is the number of seconds since the start of the recipe at
which this set point should take effect, `<variable_type>` is the variable type
to which the set point refers (e.g. "air_temperature"), and `<value>` is the
value of the set point. The set point stays in effect until a new set point for
that variable type is reached.

The list of set points must be ordered by offset.
