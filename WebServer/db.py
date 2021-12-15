'''
insert_data : 이미지 정보를 테이블에 입력
get_data : 이어서 작업할 수 있도록(아직 적용전) 가장 최근 inference된 이미지를 불러옴

'''
import toml
import mysql.connector


def _execute(qry, val, is_select=False):
    """ 쿼리 실행
    Args:
    - qry: SQL QUERY
    - val: COLUMN NAME
    - is_select : True이면 SELECT, False이면 INSERT
    """
    secrets = toml.load("WebServer/secret/secrets.toml")
    conn =  mysql.connector.connect(
        host=secrets['mysql']['host'],
        user=secrets['mysql']['user'],
        passwd=secrets['mysql']['password'],
        database=secrets['mysql']['database']
        )
    print(qry, val)
    
    with conn.cursor(dictionary=True) as cur: 
        cur.execute(qry, val)
        if is_select:
            result = cur.fetchall()
        else:
            conn.commit() #하나의 transaction이 정상적으로 끝났음을 관리자에게 알려주기 위해 commit해줘야함.
            result = cur.lastrowid # INSERT한 ROW
        print(result)

    conn.close()
    return result


def insert_data(inference_type, input_url, inference_url):
    qry = "INSERT INTO pictures (inference_type, input_url, inference_url) VALUES (%s, %s, %s)"
    val = (inference_type, input_url, inference_url)
    _ = _execute(qry, val, is_select=False)
    

def get_data(inference_type):
    """최근 저장된 하나의 inference 결과를 불러옴
    """
    qry = "SELECT * FROM pictures ORDER BY id DESC LIMIT 1"
    val = (inference_type, )
    return _execute(qry, val, is_select=True)