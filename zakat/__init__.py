"""
 _____     _         _     _     _ _                          
|__  /__ _| | ____ _| |_  | |   (_) |__  _ __ __ _ _ __ _   _ 
  / // _` | |/ / _` | __| | |   | | '_ \| '__/ _` | '__| | | |
 / /| (_| |   < (_| | |_  | |___| | |_) | | | (_| | |  | |_| |
/____\__,_|_|\_\__,_|\__| |_____|_|_.__/|_|  \__,_|_|   \__, |
                                                        |___/ 

"رَبَّنَا افْتَحْ بَيْنَنَا وَبَيْنَ قَوْمِنَا بِالْحَقِّ وَأَنتَ خَيْرُ الْفَاتِحِينَ (89)" -- سورة الأعراف
... Never Trust, Always Verify ...

This file provides the ZakatLibrary classes, functions for tracking and calculating Zakat.
"""
# Importing necessary classes and functions from the main module
from zakat.zakat_tracker import (
    Helper,
    Model,
    DictModel,
    SQLModel,
    ZakatTracker,
    test,
    JSONEncoder,
    WeekDay,
)

from zakat.file_server import (
    start_file_server,
    find_available_port,
    FileType,
)

# Version information for the module
__version__ = Model.Version()
__all__ = [
    "Helper",
    "Model",
    "DictModel",
    "SQLModel",
    "ZakatTracker",
    "test",
    "JSONEncoder",
    "WeekDay",
    "start_file_server",
    "find_available_port",
    "FileType",
]
