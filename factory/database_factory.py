from database import PostgresqlDBConnector
from enum import Enum


class DatabaseType(Enum):
    """Enumeration of supported database types."""

    POSTGRESQL = "postgresql"


class DatabaseFactory:
    """
    Factory class to create database connector instances based on database type.
    """

    @staticmethod
    def get_database_connector(
        db_type: DatabaseType,
        db_name,
        db_user,
        db_password,
        db_host="localhost",
        db_port=5432,
    ):
        """
        Create a database connector instance based on the specified database type.
        :param db_type: Type of database (e.g., "postgresql").
        :param db_name: Name of the database.
        :param db_user: Username for the database.
        :param db_password: Password for the database.
        :param db_host: Host address of the database (default is "localhost").
        :param db_port: Port number of the database (default is 5432).
        :return: An instance of a database connector.
        """

        if db_type == DatabaseType.POSTGRESQL:
            return PostgresqlDBConnector(
                db_name, db_user, db_password, db_host, db_port
            )
        else:
            raise ValueError(
                f"Unsupported database type: {db_type}, only 'postgresql' is supported."
            )
