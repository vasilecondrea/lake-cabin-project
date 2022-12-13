import psycopg2
import datetime
import calendar

def connect_to_db(dbname, user, password, host, port):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port, sslmode='require')
    return conn

def extract_date(conn):
    
    print(dir(conn))
    print(conn.status)

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sales_order;")

    data = cursor.fetchone()

    print(data[1])

    #print(dir(datetime.datetime))

    # date id
    # year
    print("YEAR:", data[1].year)
    # month
    print("MONTH:", data[1].month)
    # day
    print("DAY:", data[1].day)
    # day of week
    print("DAY OF WEEK:", data[1].weekday())
    # day name
    print("DAY NAME:", calendar.day_name[data[1].weekday()])
    # month name

    # quarter