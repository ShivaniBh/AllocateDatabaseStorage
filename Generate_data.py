import pyodbc as odbc
import random
import numpy as np
from datetime import date, timedelta, datetime

DRIVER_NAME='ODBC Driver 18 for SQL Server'
SERVER_NAME='Shivani\SQLEXPRESS'
DATABASE_NAME='SimulateGrowth'



connection_string = f"""
    DRIVER={{{DRIVER_NAME}}};
    SERVER={SERVER_NAME};
    DATABASE={DATABASE_NAME};
    Trusted_Connection=yes;
    TrustServerCertificate=yes;
    Encrypt=no;
    uid=shivani_sql_login;
    pwd=shivani_sql_login;
"""

try:
   conn = odbc.connect(connection_string)
   print("Connection successful")
   print (conn)

   conn.autocommit=True
   cursor = conn.cursor()

   #Set initial sizes of databases on the first date 2018-01-01
   #We will be updating the growth_data table in the database for the date 2018-01-01 for all 1008 databases.

   #Function to generate a random size between min_mb and max_mb using a lognormal distribution. This is for initialising the database sizes on the first date 2018-01-01. 
   def generate_size(min_mb, max_mb):
    min_mb = float(min_mb)
    max_mb = float(max_mb)
    
    median = np.sqrt(min_mb * max_mb)
    #median = min_mb * 1.5 #this is a hardcoded value for now, but I need to experiment with this value
    mu = np.log(median)
    sigma = 0.8 #this is hardcoded here but I need to experiment with this value

    while True:
        size = np.random.lognormal(mu, sigma)
        if min_mb <= size <= max_mb:
            #return round(size, 2)
            return round(size) #whole num   
   # end  function


   size_range_query = "select a.database_id, b.min_range_mb, b.max_range_mb from ft_database a inner join ft_size_ranges b on a.database_type_id=b.database_type_id"
   cursor.execute(size_range_query)
   size_range_results = cursor.fetchall()

   for row in size_range_results:
       size_mb = generate_size(row.min_range_mb, row.max_range_mb)

      # cursor.execute("""INSERT INTO growth_data (database_id, date_code, size_mb_used) VALUES (?, ?, ?)""", row.database_id, '2018-01-01', size_mb)


   #update expected_annual_growth_mb for each db. A random number based on the range and the starting size
   growth_query = """
   SELECT
      a.database_id,
      d.min_annual_growth,
      d.max_annual_growth,
      b.size_mb_used
   FROM ft_database a
   INNER JOIN growth_data b
      ON a.database_id = b.database_id
      AND b.date_code = '2018-01-01'
   INNER JOIN database_types c
      ON c.database_type_id = a.database_type_id
   INNER JOIN growth_levels d
      ON d.growth_level_id = c.growth_level_id
   """

   cursor.execute(growth_query)
   growth_rows = cursor.fetchall()

   update_query = """
   UPDATE ft_database
   SET
      expected_annual_growth_pct = ?,
      expected_annual_growth_mb = ?
   WHERE database_id = ?
   """

   for row in growth_rows:

    database_id = row.database_id
    size_mb_used = float(row.size_mb_used)

    min_growth = float(row.min_annual_growth)
    max_growth = float(row.max_annual_growth)

    # Random annual growth %
    annual_growth_pct = round(random.uniform(min_growth, max_growth), 2)

    # Expected annual growth MB
    expected_annual_growth_mb = round(
        size_mb_used * (annual_growth_pct / 100)
    )

    cursor.execute(
        update_query,
        annual_growth_pct,
        expected_annual_growth_mb,
        database_id
    )


   #data has been initialised now we move on to simulating 10 yrs of data

   date_query = "SELECT min(date_code) FROM growth_data"
   cursor.execute(date_query)
   starting_date = cursor.fetchone()[0]
   print (f"Starting date: {starting_date}")

   # print(starting_date)
   # print(type(starting_date))
   end_date = date(2026, 7, 31)

   #starting_date = date(2025, 12, 31)

   while starting_date < end_date:
      next_date = starting_date + timedelta(days=1)

      query = """
      SELECT
         b.database_id,
         c.size_mb_used,
         b.expected_annual_growth_mb,
         a.noise_factor_variable_med
      FROM database_types a
      INNER JOIN ft_database b
         ON a.database_type_id = b.database_type_id
      INNER JOIN growth_data c
         ON c.database_id = b.database_id
      WHERE c.date_code = ?
      """

      cursor.execute(query, (starting_date,))

      rows = cursor.fetchall() #rows variable has the data
         #now for each row in rows, calculate the next days used_mb
      print(f"Date: {starting_date}, Rows returned: {len(rows)}")

      if not rows:
         print("No rows found!")
         break


         #formula : (day-1 used_mb) + expected_growth + noise

      for row in rows:
            database_id = row.database_id
            used_mb = float(row.size_mb_used)

            expected_annual_growth_mb = float(row.expected_annual_growth_mb)
            noise_factor = float(row.noise_factor_variable_med)
            noise_multiplier = random.uniform(1.0, 3.0)

            daily_average = expected_annual_growth_mb / 365

            std_deviation = daily_average*noise_factor*noise_multiplier

            # Generate today's new data
            daily_new_data = np.random.normal(daily_average,std_deviation )

            #Only positive growth
            daily_new_data = max(0, round(daily_new_data))

            # New database size
            size_after_growth = round(used_mb + daily_new_data)

            print(
               f"DB:{database_id} "
               f"Used:{used_mb} "
               f"Daily Avg:{daily_average:.2f} "
               f"New Data:{daily_new_data} "
               f"New Size:{size_after_growth}"
            )

            cursor.execute("""
               INSERT INTO growth_data
                     (database_id, date_code, size_mb_used)
               VALUES (?, ?, ?)
            """, database_id, next_date, size_after_growth)

      starting_date = next_date


# except odbc.Error as ex:
#    print("Connection failed")

except Exception as ex:
    print("Error:")
    print(type(ex))
    print(ex)