#!/usr/bin/python
# Von https://pythonhosted.org/NagAconda/plugin.html
from NagAconda import Plugin
import os
import subprocess
from pyparsing import *

btrfs_check = Plugin("Plugin to show disk usage of btrfs.", "0.1")
btrfs_check.add_option('m', 'mountpoint', 'mountpoint for btrfs',
    required=True)

btrfs_check.enable_status('warning')
btrfs_check.enable_status('critical')
btrfs_check.start()

btrfs_output = subprocess.check_output(["btrfs", "fi", "df", btrfs_check.options.mountpoint])

# DEBUG:
# print btrfs_output

# PyParsing definitions
#
# Output is something like:
# Data, RAID1: total=222.72GB, used=197.44GB
# System, RAID1: total=64.00MB, used=40.00KB
# System: total=4.00MB, used=0.00
# Metadata, RAID1: total=10.00GB, used=5.40GB

# Parse Byte values with units
byteDefs=["B", "KB", "MB", "GB", "TB", "PB", "EB"]
byteDef = oneOf(byteDefs)
fnumber = Word(nums+'.').setParseAction(lambda t: float(t[0]))
bnumber = Group(fnumber('num') + Optional(byteDef('unit'), default="B"))

# Definitions for each row
row_data = "Data, " + "RAID1: " + "total=" + bnumber('bytesize_total') + "," + "used=" + bnumber('bytesize_used')
row_system1 = "System, " + "RAID1: " + "total=" + bnumber('bytesize_total') + "," + "used=" + bnumber('bytesize_used')
row_system2 = "System: " + "total=" + bnumber('bytesize_total') + "," + "used=" + bnumber('bytesize_used')
row_metadata = "Metadata, " + "RAID1: " + "total=" + bnumber('bytesize_total') + "," + "used=" + bnumber('bytesize_used')

# The whole parsing term
btrfs_output_parser = row_data('data') + row_system1('system1') + row_system2('system2') + row_metadata('metadata')

# Parse btrfs output
btrfs_output_parsed = btrfs_output_parser.parseString(btrfs_output)

# calculate values
byteUnits=[("B", 1), ("KB", 1000), ("MB", 1000000), ("GB", 1000000000), ("TB", 1000000000000), ("PB", 1000000000000000), ("EB", 1000000000000000000)]
def calc_bnumber(bnum):
	"""Get float number of bytes for something like 2GB"""
	for byteSize in byteUnits:
		if byteSize[0] == bnum.unit:
			return byteSize[1] * bnum.num
	return None

data_bytes_used_float = calc_bnumber(btrfs_output_parsed.data.bytesize_used)
data_bytes_size_float = calc_bnumber(btrfs_output_parsed.data.bytesize_total)
data_usage_percentage_float = data_bytes_used_float / data_bytes_size_float * 100.0

system1_bytes_used_float = calc_bnumber(btrfs_output_parsed.system1.bytesize_used)
system1_bytes_size_float = calc_bnumber(btrfs_output_parsed.system1.bytesize_total)

system2_bytes_used_float = calc_bnumber(btrfs_output_parsed.system2.bytesize_used)
system2_bytes_size_float = calc_bnumber(btrfs_output_parsed.system2.bytesize_total)

metadata_bytes_used_float = calc_bnumber(btrfs_output_parsed.metadata.bytesize_used)
metadata_bytes_size_float = calc_bnumber(btrfs_output_parsed.metadata.bytesize_total)

# DEBUG:
# print btrfs_output_parsed.dump()

# set nagios output
btrfs_check.set_range('warning', 100000000000000000000000, range_num=2)
btrfs_check.set_range('critical', 200000000000000000000000, range_num=2)


btrfs_check.set_value("data_used", btrfs_output_parsed.data.bytesize_used.num, scale=btrfs_output_parsed.data.bytesize_used.unit, threshold=2)
btrfs_check.set_value("data_total", btrfs_output_parsed.data.bytesize_total.num, scale=btrfs_output_parsed.data.bytesize_total.unit, threshold=2)
btrfs_check.set_value("data_ratio", data_usage_percentage_float, scale="%", threshold=1)

btrfs_check.set_value("system1_used", btrfs_output_parsed.system1.bytesize_used.num, scale=btrfs_output_parsed.system1.bytesize_used.unit, threshold=2)
btrfs_check.set_value("system1_total", btrfs_output_parsed.system1.bytesize_total.num, scale=btrfs_output_parsed.system1.bytesize_total.unit, threshold=2)

btrfs_check.set_value("system2_used", btrfs_output_parsed.system2.bytesize_used.num, scale=btrfs_output_parsed.system2.bytesize_used.unit, threshold=2)
btrfs_check.set_value("system2_total", btrfs_output_parsed.system2.bytesize_total.num, scale=btrfs_output_parsed.system2.bytesize_total.unit, threshold=2)

btrfs_check.set_value("metadata_used", btrfs_output_parsed.metadata.bytesize_used.num, scale=btrfs_output_parsed.metadata.bytesize_used.unit, threshold=2)
btrfs_check.set_value("metadata_total", btrfs_output_parsed.metadata.bytesize_total.num, scale=btrfs_output_parsed.metadata.bytesize_total.unit, threshold=2)

btrfs_check.set_status_message("{0}{1} of {2}{3} used ({4}%)".format(btrfs_output_parsed.data.bytesize_used.num, btrfs_output_parsed.data.bytesize_used.unit, btrfs_output_parsed.data.bytesize_total.num, btrfs_output_parsed.data.bytesize_total.unit, data_usage_percentage_float ))

btrfs_check.finish()

