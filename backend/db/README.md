# DB

In order to be prepared for a scaling of brandslang (250GB/day), we decided to use the Apache Cassandra database, which offers super fast writing and is hugely scalable out of the box. However, data modelling and query patterns can be very different when coming from a traditional SQL viewpoint.

The most effective queries read from few partitions, so a query like `SELECT X,Y,Z FROM tweets WHERE day = 19018 AND hour = 23 AND minute = 33` is very performant, since all columns can be found in the partition key. It can make sense to query all data of a timeslice first and filter it in a separate system in order to take load of the cassandra node if the system is ingesting tweets at the same time.

In our operation, the system typically has a write lateny of about 0.1-0.05ms while the read latency ranges in the 50ms range. Check your current stats with `nodetool cfstats | sed -n -e '/Keyspace : twitter/,/----------------/ p'`.