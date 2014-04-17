# -*- coding: utf-8 -*- from __future__ import unicode_literals
import Maker
import os

maker = Maker.Maker()

#uncomment following line to use in directory
maker.editEpub()

#uncomment following lines to use for only file
# filename = os.path.join(maker.location, "bano_9781601636850_oeb_fm2_r1.html")
# maker.replace_svg_tags(filename)
# maker.replace_markers(filename)
# maker.replace_headers(filename)
