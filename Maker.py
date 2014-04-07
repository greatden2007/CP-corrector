__author__ = 'kudinovdenis'
import os
import re
import zipfile
from os import listdir
from os.path import isfile, join
import shutil
from shutil import make_archive
import zlib

class Maker(object):
    def __init__(self):
        self.location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self.onlyfiles = [f for f in listdir(self.location) if isfile(join(self.location, f))]
        print("\t--- Found {} epubs:".format(len(self.onlyfiles) - 1))

    def editEpub(self):
        i = 0
        for epubnameWithFormat in self.onlyfiles:
            try:
                splitter = "."
                epubNameWithoutFormat = epubnameWithFormat.split(splitter)[0]
                htmlFolder = os.path.join(self.location, epubNameWithoutFormat + "/ops/xhtml/")
                inZipPath = os.path.join(self.location, epubNameWithoutFormat)
                outZipPath = os.path.join(self.location, epubnameWithFormat)

                self.unarchiveEpub(epubnameWithFormat, epubNameWithoutFormat)
                self.correctAllHtml(htmlFolder)
                os.remove(outZipPath)
                self.zip(inZipPath, outZipPath)
                shutil.rmtree(inZipPath)
                i += 1
            except:
                print("skip  " + epubnameWithFormat)
        print("\t--- Done {} epubs".format(i))


    def unarchiveEpub(self, archiveName, destinationFolderName):
        inputPath = os.path.join(self.location, archiveName)
        outputPath = os.path.join(self.location, destinationFolderName)
        with zipfile.ZipFile(inputPath, "r") as z:
            z.extractall(outputPath)

    def correctAllHtml(self, htmlFolder):
        allHtmls = [f for f in listdir(htmlFolder) if isfile(join(htmlFolder, f))]
        for htmlName in allHtmls:
            html = os.path.join(htmlFolder, htmlName)
            self.replace_svg_tags(html)
            self.replace_markers(html)


    def replace_svg_tags(self, filename):
        print('\t--- Replasing SVG Tags...')
        f = open(os.path.join(self.location, filename), 'r')
        pattern = r'<svg:.+?href="(.+?)".+?svg>'
        INPUT = f.read()
        strings = re.findall(pattern, INPUT, flags=re.S)
        i = 0
        correctStrings = []
        for imageName in strings:
            #print(imageName)
            correctStrings.append(
                '<div class="cover"><img alt="cover" height="95%" src="{!s}"/></div>'.format(imageName))

            originalString = INPUT
            pattern = '(<svg.+?href=".+?\..+?".+?width.+?svg>)'
            pattern_obj = re.compile(pattern, re.S)
            replacement_string = correctStrings[i]
            INPUT = pattern_obj.sub(replacement_string, originalString, count=1)

            i += 1
        #print(INPUT)
        f.close()
        f = open(os.path.join(self.location, filename), 'w')
        f.write(INPUT)

    def replace_markers(self, filename):
        print('\t--- Replasing Markers...')
        f = open(os.path.join(self.location, filename), 'r')
        pattern = r'<p class=".+?><img.+?"\/>(.+?)<\/p>'
        INPUT = f.read()
        strings = re.findall(pattern, INPUT, flags=re.S)
        i = 0
        correctStrings = []
        for text in strings:
            #print(text)
            correctStrings.append('<ul><li>{!s}</li></ul>'.format(text))

            originalString = INPUT
            pattern = '(<p class=".+?><img.+?"\/>.+?<\/p>)'
            pattern_obj = re.compile(pattern, re.S)
            replacement_string = correctStrings[i]
            INPUT = pattern_obj.sub(replacement_string, originalString, count=1)

            i += 1
        #print(INPUT)
        f.close()
        f = open(os.path.join(self.location, filename), 'w')
        f.write(INPUT)

    def zip(self, res, dst):
        zf = zipfile.ZipFile("%s" % (dst), "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(res)
        for dirname, subdirs, files in os.walk(res):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                #print('zipping %s as %s' % (os.path.join(dirname, filename), arcname))
                zf.write(absname, arcname)
        zf.close()
