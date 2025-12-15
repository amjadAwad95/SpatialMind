import os
import sys

# Add plugin directory to Python path
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)


def classFactory(iface):
    """Load SQLQueryPlugin class from file sql_query_plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .sql_query_plugin import SQLQueryPlugin

    return SQLQueryPlugin(iface)
