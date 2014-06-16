# -*- coding: utf-8 -*- from __future__ import unicode_literals
import Maker
import os

maker = Maker.Maker()

"""
при раскомментированной следующей строке выполняется
 обработка всех епабов в директории
"""
maker.editEpub()

"""
при раскомментированных следующих строках происходит работа
 с одним вабранным файлом указынными ниже методами
"""
# filename = os.path.join(maker.location, "bano_9781601636850_oeb_fm2_r1.html")
# maker.replace_svg_tags(filename)
# maker.replace_markers(filename)
# maker.replace_headers(filename)
