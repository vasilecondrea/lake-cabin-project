# Plan

look through the processing bucket
extract all objects modified in the last 5min
convert the objects from parquet to SQL
load SQL tables into the OLAP database

2. list of tables to update - for that we need a load function


3. a convert function from parquet to SQL 
         Research:
             do we used a Panda dataframe? 
             to research how to store a table in python?
             
4.  upload a table to the OLAP database

5. get a the name of the process bucket name through a lambda handler 

Functions have to be 
    tested
    logs errors