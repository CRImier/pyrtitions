# -*- coding: utf-8 -*-

import pyrtitions

assert(pyrtitions.label_filter("привет") == "privet")
assert(pyrtitions.label_filter("#####") == None)
