from abc import ABC, abstractmethod


class BaseDBConnector(ABC):
    """Abstract base class for database connectors."""

    @abstractmethod
    def connect(self):
        """Establish a connection to the database."""
        pass

    @abstractmethod
    def close(self):
        """Close the connection to the database."""
        pass

    @abstractmethod
    def execute_query(self, query):
        """
        Execute a SQL query and return the results.
        :param query: SQL query string to be executed.
        :return: Query results.
        """
        pass

    @abstractmethod
    def get_schema(self):
        """
        Retrieve the database schema.
        :return: Database schema information.
        """
        pass
