import mysql.connector
import sshtunnel


class Database:
    sshtunnel.SSH_TIMEOUT = 5.0
    sshtunnel.TUNNEL_TIMEOUT = 5.0

    SSH_HOSTNAME = 'ssh.pythonanywhere.com'
    PYTHON_ANYWHERE_USERNAME = 'apihub'
    PYTHON_ANYWHERE_PASSWORD = 'Pass123'
    PYTHON_ANYWHERE_DATABASE_HOSTNAME = 'apihub.mysql.pythonanywhere-services.com'
    DATABASE_NAME = 'apihub$sessions'  # database is also hosted on pythonanywhere
    PORT = 3306  # default port

    def __init__(self, ssh_timeout=sshtunnel.SSH_TIMEOUT, tunnel_timeout=sshtunnel.TUNNEL_TIMEOUT,
                 ssh_hostname=SSH_HOSTNAME, username=PYTHON_ANYWHERE_USERNAME, password=PYTHON_ANYWHERE_PASSWORD,
                 database_hostname=PYTHON_ANYWHERE_DATABASE_HOSTNAME, database_name=DATABASE_NAME, port=PORT):
        self.ssh_timeout = ssh_timeout
        self.ssh_tunnel = tunnel_timeout
        self.ssh_hostname = ssh_hostname
        self.username = username
        self.password = password
        self.database_hostname = database_hostname
        self.database_name = database_name
        self.port = port

    def connect_db(self):
        with sshtunnel.SSHTunnelForwarder(
                (self.ssh_hostname),
                ssh_username=self.username, ssh_password=self.password,
                remote_bind_address=(self.database_hostname, self.port)
        ) as tunnel:
            mydb = mysql.connector.connect(
                user=self.username, password=self.password,
                host='127.0.0.1', port=tunnel.local_bind_port,
                database=self.database_name
            )
            return mydb

    def create_db(self):
        with sshtunnel.SSHTunnelForwarder(
                (self.ssh_hostname),
                ssh_username=self.username, ssh_password=self.password,
                remote_bind_address=(self.database_hostname, self.port)
        ) as tunnel:
            mydb = mysql.connector.connect(
                user=self.username, password=self.password,
                host='127.0.0.1', port=tunnel.local_bind_port,
                database=self.database_name
            )
            mycursor = mydb.cursor()
            mycursor.execute('CREATE TABLE report ('
                             'requestdate DATETIME,'
                             'externaluserid VARCHAR(60),'  # NVARCHAR(N)
                             'count_useraccounts INT,'
                             'SessionStatus VARCHAR(30),'
                             'Stage VARCHAR(30),'
                             'SessionSource VARCHAR(30),'
                             'failuremessageid VARCHAR(60),'
                             'accountsfetchedcount INT,'
                             'accountsprocessedcount INT,'
                             'Name VARCHAR(60),'
                             'AspspResponseContent VARCHAR(360),'
                             'AspspResponseStatus VARCHAR(30),'
                             'ConsentId VARCHAR(60),'
                             'ErrorMessage VARCHAR(360),'
                             'ErrorType VARCHAR(60),'
                             'ExecutionId VARCHAR(60),'
                             'TransactionStatus INT,'
                             'TransactionStatusTimestamp DATETIME,'
                             'Id VARCHAR(90),'
                             'unique_id VARCHAR(90) PRIMARY KEY,'
                             'ecosystem VARCHAR(30))')
            mydb.close()

    def insert_to_db(self):
        pass

    def select_from_db(self):
        pass


db = Database()
print(db.SSH_HOSTNAME)
print(db.database_name)
db.connect_db()
db.create_db()
