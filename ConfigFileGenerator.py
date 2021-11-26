import boto3
import base64
from botocore.exceptions import ClientError
import os
import re

serverRegex = "(?<=Server=)(.*)(?=;D)"
databaseRegex = "(?<=Database=)(.*)(?=;Ui)"
userRegex = "(?<=Uid=)(.*)(?=;Pwd)"
passwordRegex = "(?<=Pwd=)(.*)(?=;)"

def get_secret():
    secretName = os.getenv('SECRET_NAME')
    regionName = os.getenv('AWS_REGION')
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=regionName
    )
    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secretName
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary'])
            return decoded_binary_secret

def writeUserFile(secretString):
    userFile = open("userlist.txt", "w")
    userName = re.search(userRegex, secretString).group(1)
    password = re.search(passwordRegex, secretString).group(1)
    
    userFile.write("\"{}\" : \"{}\"".format(userName, password))
    userFile.close()

def setHostFile(secretString):
    hostName = re.search(serverRegex, secretString).group(1)
    databaseName = re.search(databaseRegex, secretString).group(1)
    hostFile = open("host.txt", "w")
    hostFile.write("\"host\" : \"{}\"\n".format(hostName))
    hostFile.write("\"name\" : \"{}\"".format(databaseName))
    hostFile.close()

def writeInitFile(secretString):
    userName = re.search(userRegex, secretString).group(1)
    password = re.search(passwordRegex, secretString).group(1)
    hostName = re.search(serverRegex, secretString).group(1)
    databaseName = re.search(databaseRegex, secretString).group(1)
    maxDbConnections = os.getenv('MAX_DB_CONNECTIONS')
    aplicationNameAddHost = os.getenv('APPLICATION_NAME_ADD_HOST')
    poolMode = os.getenv('POOL_MODE')
    listenPort=os.getenv('LISTEN_PORT')
    listenAddr = os.getenv('LISTEN_ADDR')
    startupParameters = os.getenv('IGNORE_STARTUP_PARAMETERS')
    userListFile = open("/etc/pgbouncer/userlist.txt", "w")
    userListFile.write("""
\"{userName}\" \"{password}\"

        """.format(
            userName=userName,
            password=password
        )
    )
    userListFile.close()

    initFile = open("/etc/pgbouncer/pgbouncer.ini", "w")
    initFile.write(
        """
[databases]
{dbName} = host={host} dbname={dbName} auth_user={user} password={password}

[pgbouncer]
listen_addr = {listenAddr}
listen_port = {listenPort}
unix_socket_dir =
user = {user}
auth_type = plain
auth_file = /etc/pgbouncer/userlist.txt
auth_user = {user}
ignore_startup_parameters = {startupParameters}
application_name_add_host = {aplicationNameAddHost}
max_db_connections = {maxDbConnections}
pool_mode={poolMode}

# Log settings
admin_users = postgres
verbose = 2
""".format(
            host = hostName,
            user = userName,
            password=password,
            dbName=databaseName,
            aplicationNameAddHost=aplicationNameAddHost,
            maxDbConnections=maxDbConnections,
            poolMode=poolMode,
            listenPort=listenPort,
            listenAddr=listenAddr,
            startupParameters=startupParameters
            )
        )   

    initFile.close()

# logfile = /var/log/pgbouncer/pgbouncer.log
# pidfile = /var/run/pgbouncer/pgbouncer.pid
def main():
    secret = get_secret()
    # writeUserFile(secret)
    # setHostFile(secret)
    writeInitFile(secret)

main()
