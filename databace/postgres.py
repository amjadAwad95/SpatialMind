import psycopg2
from databace.base_databace import BaseDBConnector

class PostgresqlDBConnector(BaseDBConnector):
    """
    Singleton-style PostgreSQL database connector.

    This class manages connections to a PostgreSQL database using psycopg2.
    It ensures that only one instance per unique configuration (database name, user, host, etc.) exists.
    """

    _instance = {}

    def __new__(cls, db_name, db_user, db_password, db_host="localhost", db_port=5432):
        """
        Create or return an existing instance of the database connector.

        :param db_name: Name of the PostgreSQL database.
        :param db_user: Username for authenticating with the database.
        :param db_password: Password for authenticating with the database.
        :param db_host: Database host address (default is "localhost").
        :param db_port: Database port number (default is 5432).
        :return: A singleton instance of PostgresqlDBConnector for the given configuration.
        """
        config_key = (db_name, db_user, db_password, db_host, db_port)

        if config_key not in cls._instance:
            instances = super(PostgresqlDBConnector, cls).__new__(cls)

            cls._instance[config_key] = instances
            instances.__init__(db_name, db_user, db_password, db_host, db_port)

        return cls._instance[config_key]

    def __init__(
        self, db_name, db_user, db_password, db_host="localhost", db_port=5432
    ):
        """
        Initialize the database connection parameters.

        :param db_name: Name of the PostgreSQL database.
        :param db_user: Username for the database.
        :param db_password: Password for the database.
        :param db_host: Database host address (default is "localhost").
        :param db_port: Database port number (default is 5432).
        """
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

        self.connection = None
        self.cursor = None

    def connect(self):
        """
        Establish a connection to the PostgreSQL database.

        :return: The active psycopg2 connection object if successful, otherwise None.
        """
        if self.connection:
            print("Already connected to the database.")
            return self.connection

        try:
            self.connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
            )
            self.cursor = self.connection.cursor()
            print("Connection to the database established successfully.")
            return self.connection
        except:
            print("Failed to connect to the database.")
            return None

    def execute_query(self, query, params=None):
        """
        Execute an SQL query and return the fetched results.

        :param query: SQL query to execute.
        :param params: Optional parameters for parameterized queries.
        :return: List of query results.
        """
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.fetchall()

    def get_schema(self):
        """
        Retrieve and format the database schema for all public tables and views.

        This includes table names, column details (name, data type, nullability, default value),
        and one sample row from each table.

        :return: Formatted string representation of the database schema, or None if no tables/views are found.
        """
        schema = ""

        table_names = self.execute_query(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type IN ('BASE TABLE', 'VIEW')
            ORDER BY table_name;
        """
        )

        if table_names:
            for (table_name,) in table_names:
                schema += f"\n--- Table/View: {table_name} --- \n"

                column_details = self.execute_query(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                """,
                    (table_name,),
                )

                one_row = self.execute_query(
                    f"""
                    SELECT *
                    FROM {table_name}
                    LIMIT 1;
                """
                )

                schema += f"Sample:{one_row}\n"

                for col in column_details:
                    col_name, data_type, is_nullable, col_default = col

                    default_info = f" DEFAULT {col_default}" if col_default else ""
                    nullable_info = "NOT NULL" if is_nullable == "NO" else "NULL"

                    schema += f"  - {col_name:<20} {data_type:<15} {nullable_info}{default_info} \n"

            return schema
        else:
            print("No tables or views found in the 'public' schema.")
            return None

    def close(self):
        """
        Close the database connection and cursor if they are active.

        :return: True if the connection was successfully closed, False otherwise.
        """
        if self.connection:
            self.cursor.close()
            self.connection.close()
            self.connection = None
            self.cursor = None
            print("Database connection closed.")
            return True
        else:
            print("No active database connection to close.")
            return False
