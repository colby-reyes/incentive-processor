# utils.py

from dataclasses import dataclass


@dataclass
class VersionInfo:
    version = "2.0.0"
    description = """Incentive Processor version 2.0.0 (full version as described in `README.MD` file)"""  # noqa: E501
    author = "Colby Reyes"
    contact = "colbyr@hs.uci.edu"

    ### copy from v1 utils.py and add in new functions as needed for v2
