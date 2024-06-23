"""
 _____     _         _     _____               _             
|__  /__ _| | ____ _| |_  |_   _| __ __ _  ___| | _____ _ __ 
  / // _` | |/ / _` | __|   | || '__/ _` |/ __| |/ / _ \ '__|
 / /| (_| |   < (_| | |_    | || | | (_| | (__|   <  __/ |   
/____\__,_|_|\_\__,_|\__|   |_||_|  \__,_|\___|_|\_\___|_|   

"رَبَّنَا افْتَحْ بَيْنَنَا وَبَيْنَ قَوْمِنَا بِالْحَقِّ وَأَنتَ خَيْرُ الْفَاتِحِينَ (89)" -- سورة الأعراف
... Never Trust, Always Verify ...

This module provides the ZakatTracker class for tracking and calculating Zakat.
"""
# Importing necessary classes and functions from the main module
from .zakat_tracker import (
    ZakatTracker,
    Action,
    JSONEncoder,
    MathOperation,
)

# Version information for the module
__version__ = ZakatTracker.Version()
__all__ = [
    "ZakatTracker",
    "Action",
    "JSONEncoder",
    "MathOperation",
]
