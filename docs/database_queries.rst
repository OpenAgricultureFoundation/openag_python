Querying the Database
=====================

CouchDB has built in REST API that runs port 5984 that can be used to pull data
from the database. For many of the databases used by this project, the built in
API is sufficient because you usually want to retrieve all of the documents in
the database. This can be done by using the `_all_docs
<http://docs.couchdb.org/en/latest/api/database/bulk-api.html>`_ endpoint for
the database in question. For example::

    curl localhost:5984/<db_name>/_all_docs?include_docs=True

Environmental Data Points
-------------------------

For the `environmental_data_point` database, however, retreiving all of the
documents is typically far too expensive because data is constantly being added
to it. Because of this, the project defines a design document for this database
with a couple of views and a list function that should prove useful.

By Timestamp
~~~~~~~~~~~~

There is a `by_timestamp` view that sorts the data points by environment and
then by timestamp. In particular, each data point gets mapped to a key of the
format::

    [<environment_id>, <timestamp>]

Querying the `by_timestamp` view is especially useful for getting all of the
data points between a given time range for a specific environment. For
example::

    curl -g localhost:5984/environmental_data_point/_design/openag/_view/by_timestamp?startkey=[%22environment_1%22,<start_timestamp>]\&endkey=[%22environment_1%22,<end_timestamp>]

By Variable
~~~~~~~~~~~

There is also a `by_variable` view that sorts the data points by environment,
then by whether they are measured or desired, then by variable, then by
timestamp. In particular, each data point gets mapped to a key of the format::

    [<environment_id>, "desired"/"measured", <variable>, <timestamp>]

It also has a reduce function which returns the data point with the largest
timestamp.

The `by_variable` view can be used to get the most recent data point for each
variable::

    curl localhost:5984/environmental_data_point/_design/openag/_view/by_variable?group_level=3

It can also be used to get the history of a particular variable over time::

    curl -g localhost:5984/environmental_data_point/_design/openag/_view/by_variable?reduce=false\&startkey=[%22environment_1%22,%22measured%22,<variable>]\&endkey=[%22environment_1%22,%22measured%22,<variable>,{}]

CSV Dumps
~~~~~~~~~

There is a `csv` list function that can be used to output the results of a
query to any of these views as a csv file. It takes a GET parameter `cols`
which is a list of columns that should be included in the generated csv file.
By default there are columns for "timestamp", "variable", and "value". For
example, to output the history of a particular variable over time as a csv
file with only the columns "timestamp" and "value"::

    curl -g localhost:5984/environmental_data_point/_design/openag/_list/csv/by_variable?reduce=false\&startkey=[%22environment_1%22,%22measured%22,<variable>]\&endkey=[%22environment_1%22,%22measured%22,<variable>,{}]\&cols=[%22timestamp%22,%22value%22]
