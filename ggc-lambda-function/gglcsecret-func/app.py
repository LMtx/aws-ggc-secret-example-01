import greengrasssdk
import mysql.connector
import json
from time import time

sm_client = greengrasssdk.client('secretsmanager')
iot_client = greengrasssdk.client('iot-data')

def lambda_handler(event, context):

    resp = ''
    try:
        # receive secret from Secrets Manager
        resp = sm_client.get_secret_value(SecretId='greengrass-local-db')
        secret = resp.get('SecretString')
    except Exception as e:
        iot_client.publish(topic='sql/res', payload=json.dumps({
            'ERROR': '{}'.format(e)
        }))
        return
    
    message = {}
    
    if secret is None:
        message['ERROR'] = 'Failed to retrieve secret.'
    else:

        sec = json.loads(secret)

        # connect to local DB using obtained secret
        cnx = mysql.connector.connect(user='root',password=sec["db_pass"], host='db',port=3306, database='sys')

        cursor = cnx.cursor()

        # query local DB
        query = "select user, command from session"

        cursor.execute(query)

        sql_res = []
        for (user, command) in cursor:
            sql_res.append({
                'user': user, 
                'command': command,
                'time': time()
            })

        message['SQL'] = sql_res
        cursor.close()
        cnx.close()

    # return obtained data to AWS IoT
    iot_client.publish(topic='sql/res', payload=json.dumps(message))
