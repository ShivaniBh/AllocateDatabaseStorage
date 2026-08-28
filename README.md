# AllocateDatabaseStorage

This project is about efficiently allocating storage to a large number of MSSQL databases in an enterprise environment. The base data is being simulated. Daily growth is also simulated on each database based on predefined factors.
 - Category of database (defined in the database_types table)
 - Growth factor assigned to that category based on established bank data



ESTABLISHING A BASELINE
A baseline for this project is being established by simulating the current operating procedures. When a database hits >75% of the storage limit, an alert is generated to notify the DBAs that intervention is needed. Manual intervention is done by increasing the space allocated to the database to being it under the 75% threshold while taking other databases on the server into consideration. This is not an automated process and is done based on judgement calls.
The simulation for the baseline gives an idea of how many alerts are being generated and therefore how much time will be spent doing this task
