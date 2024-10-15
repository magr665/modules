import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.types import *
from sqlalchemy import event
import pyodbc
import urllib
import json
import os

class DBConnect:
    """
    En klasse til at oprette og administrere forbindelser til en SQL Server-database ved hjælp af ODBC.

    Denne klasse tilbyder metoder til at oprette database-engine objekter, få en database-cursor 
    og udføre statistisk logging af databaseoperationer.

    Attributter:
    -----------
    database : str
        Navnet på SQL Server-databasen.
    server : str
        Navnet eller IP-adressen på SQL Serveren.
    username : str, valgfri
        Brugernavnet til SQL Server-godkendelse. Hvis ikke angivet, bruges Windows-godkendelse.
    password : str, valgfri
        Adgangskoden til SQL Server-godkendelse. Bruges kun, hvis et brugernavn er angivet.
    """

    def __init__(self, database, server, username=None, password=None):
        """
        Initialiserer DBConnect-objektet og opretter en forbindelse til SQL Server-databasen.

        Parametre:
        ----------
        database : str
            Navnet på SQL Server-databasen.
        server : str
            Navnet eller IP-adressen på SQL Serveren.
        username : str, valgfri
            Brugernavnet til SQL Server-godkendelse. Hvis ikke angivet, bruges Windows-godkendelse.
        password : str, valgfri
            Adgangskoden til SQL Server-godkendelse. Bruges kun, hvis et brugernavn er angivet.
        """
        module_dir = os.path.dirname(__file__)
        args_path = os.path.join(module_dir, 'DatabaseConnections_args.json')
        with open(args_path, 'r') as f:
            self.__args = json.load(f)
        self.database = database
        self.server = server
        self.username = username
        self.password = password
        self.__driver = 'ODBC Driver 17 for SQL Server'
        self.__params = 'DRIVER=' + self.__driver + ';SERVER=' + self.server + ';PORT=1433;DATABASE=' + self.database
        if self.username is None or self.password is None:
            self.__params += ';Trusted_Connection=yes'
        else:
            self.__params += ';UID=' + username + ';PWD=' + password
        self.__cnxn = pyodbc.connect(self.__params)
        self.__db_params = urllib.parse.quote_plus(self.__params)
        
    def engine(self):
        """
        Opretter og returnerer et SQLAlchemy engine-objekt til forbindelse med SQL Server-databasen.

        Returnerer:
        -----------
        sqlalchemy.engine.Engine
            Et SQLAlchemy engine-objekt, der kan bruges til at interagere med databasen.
        """
        return create_engine("mssql+pyodbc:///?odbc_connect={}".format(self.__db_params))

    def cursor(self):
        """
        Henter et cursor-objekt fra den etablerede ODBC-forbindelse.

        Returnerer:
        -----------
        pyodbc.Cursor
            Et cursor-objekt, der kan bruges til at udføre SQL-forespørgsler og hente resultater.
        """
        return self.__cnxn.cursor()
    
    def fast_engine(self):
        """
        Opretter og returnerer et SQLAlchemy engine-objekt med `fast_executemany` aktiveret til bulk-indlæsningsoperationer.

        Returnerer:
        -----------
        sqlalchemy.engine.Engine
            Et SQLAlchemy engine-objekt med hurtig indlæsningsfunktionalitet.
        """
        return create_engine("mssql+pyodbc:///?odbc_connect={}".format(self.__db_params), fast_executemany=True)

    def conn(self):
        """
        Returnerer den aktuelle ODBC-forbindelse.

        Returnerer:
        -----------
        pyodbc.Connection
            En aktiv ODBC-forbindelse til SQL Server-databasen.
        """
        return self.__cnxn
    
    def statistik(self, gruppenavn, navn, id, status, interval, runtime, featuresRead={}, featuresWritten={}):
        """
        Logger statistik for en FME-jobkørsel i databasen.

        Parametre:
        ----------
        gruppenavn : str
            Navnet på gruppen, som FME-jobbet tilhører.
        navn : str
            Navnet på FME-jobbet.
        id : str
            ID'et på FME-jobbet.
        status : str
            Statussen for FME-jobkørslen.
        interval : str
            Det tidsinterval, som FME-jobkørslen dækker.
        runtime : float
            Kørselstiden for FME-jobbet i sekunder.
        featuresRead : dict, valgfri
            En ordbog med antal læste features, grupperet efter feature-type.
        featuresWritten : dict, valgfri
            En ordbog med antal skrevne features, grupperet efter feature-type.
        """
        self.gruppenavn = gruppenavn
        self.id = id
        self.navn = navn
        self.status = status
        self.interval = interval
        self.runtime = runtime
        self.totalFeaturesRead = sum(featuresRead.values())
        self.totalFeaturesWritten = sum(featuresWritten.values())
        self.featuresRead = json.dumps(featuresRead)
        self.featuresWritten = json.dumps(featuresWritten)

        sql = f"""INSERT INTO [Digitalisering].[FME_STATISTIK]
                    (OBJECTID
                    , gruppenavn
                    , dato
                    , id
                    , navn
                    , status
                    , runtime
                    , featuresWritten
                    , totalFeaturesWritten
                    , interval
                    , featuresRead
                    , totalFeaturesRead) 
                VALUES (
                    (SELECT MAX(OBJECTID) FROM [Digitalisering].[FME_STATISTIK])+1
                    , '{self.gruppenavn}'
                    , GETDATE()
                    , '{self.id}'
                    , '{self.navn}'
                    , '{self.status}'
                    , {self.runtime}
                    , '{self.featuresWritten}'
                    , {self.totalFeaturesWritten}
                    , '{self.interval}'
                    , '{self.featuresRead}'
                    , {self.totalFeaturesRead}
                    )"""
        
        connection = DBConnect(server=self.__args['geodata_server'] , database=self.__args['geodata_database'])
        cursor = connection.cursor()
        cursor.execute(sql)
        cursor.commit()



