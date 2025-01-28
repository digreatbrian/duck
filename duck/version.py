"""Version module for Duck"""
import sys

version_num = (1, 0, 1)
version = "%d.%d.%d" % version_num
version_name = "Duck"

pyversion = sys.version.split(" ")[0]
server_version = "{}/{} {}/{}".format(version_name, version, "Python",
                                      pyversion)

__version__ = version
