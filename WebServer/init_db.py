'''
database를 초기화한다.
'''
import toml
import mysql.connector

secrets = toml.load("WebServer/secret/secrets.toml")

# serving_database 데이터베이스 생성 
conn =  mysql.connector.connect(
    host=secrets['mysql']['host'],
    user=secrets['mysql']['user'],
    passwd=secrets['mysql']['password'],
)

with conn.cursor() as cur:
    try:
        cur.execute("DROP DATABASE serving_database")    
    except:
        pass
    cur.execute("CREATE DATABASE serving_database")

conn.close()

# serving_database 데이터베이스안에 pictures 테이블 생성
conn =  mysql.connector.connect(
    host=secrets['mysql']['host'],
    user=secrets['mysql']['user'],
    passwd=secrets['mysql']['password'],
    database=secrets['mysql']['database'],
)


with conn.cursor() as cur:
    try:
        sql = "DROP TABLE pictures"
        cur.execute(sql)
    except:
        pass
    cur.execute("""
    CREATE TABLE pictures 
    (
        id INT AUTO_INCREMENT PRIMARY KEY, 
        inference_type VARCHAR(50),
        input_url VARCHAR(255),
        inference_url VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)

conn.close()
    