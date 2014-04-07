# -*- coding: utf-8 -*- from __future__ import unicode_literals
import Maker
import os

maker = Maker.Maker()
#uncomment following line to use in directory
# maker.editEpub()

filename = os.path.join(maker.location, "file.html")
maker.replace_markers(filename)