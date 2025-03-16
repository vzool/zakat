"""
"رَبَّنَا افْتَحْ بَيْنَنَا وَبَيْنَ قَوْمِنَا بِالْحَقِّ وَأَنتَ خَيْرُ الْفَاتِحِينَ (89)" -- سورة الأعراف

```
 _____     _         _     _     _ _                          
|__  /__ _| | ____ _| |_  | |   (_) |__  _ __ __ _ _ __ _   _ 
  / // _` | |/ / _` | __| | |   | | '_ \| '__/ _` | '__| | | |
 / /| (_| |   < (_| | |_  | |___| | |_) | | | (_| | |  | |_| |
/____\__,_|_|\_\__,_|\__| |_____|_|_.__/|_|  \__,_|_|   \__, |
... Never Trust, Always Verify ...                       |___/ 
```

This file provides the ZakatLibrary classes, functions for tracking and calculating Zakat.
"""
# Importing necessary classes and functions from the main module
from zakat.zakat_tracker import (
    ZakatTracker,
    test,
    Action,
    JSONEncoder,
    JSONDecoder,
    MathOperation,
    WeekDay,
)

from zakat.file_server import (
    start_file_server,
    find_available_port,
    FileType,
)

# Version information for the module
__version__ = ZakatTracker.Version()
__all__ = [
    "ZakatTracker",
    "test",
    "Action",
    "JSONEncoder",
    "JSONDecoder",
    "MathOperation",
    "WeekDay",
    "start_file_server",
    "find_available_port",
    "FileType",
]
