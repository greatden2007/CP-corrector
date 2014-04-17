__author__ = 'kudinovdenis'
import os
import re
import zipfile
from os import listdir
from os.path import isfile, join
import shutil


class Maker(object):
    def __init__(self):
        self.toc_folder = ""
        self.location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self.onlyfiles = [f for f in listdir(self.location) if isfile(join(self.location, f))]
        print("\t--- Found {} files:".format(len(self.onlyfiles) - 1))

    def editEpub(self):
        i = 0
        for epubnameWithFormat in self.onlyfiles:
            try:
                splitter = "."
                epubNameWithoutFormat = epubnameWithFormat.split(splitter)[0]
                htmlFolder = os.path.join(self.location, epubNameWithoutFormat + "/ops/xhtml/")
                self.toc_folder = os.path.join(self.location, epubNameWithoutFormat + "/ops/")
                inZipPath = os.path.join(self.location, epubNameWithoutFormat)
                outZipPath = os.path.join(self.location, epubnameWithFormat)

                print('\t--- Current epub: {}'.format(epubnameWithFormat))
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
        self.repair_toc_ncx()
        try:
            allHtmls = [f for f in listdir(htmlFolder) if isfile(join(htmlFolder, f))]
        except:
            print("First try finding HTML directory failed. Second try...")
            htmlFolder = os.path.join(htmlFolder[:-10], "OEBPS")
            allHtmls = [f for f in listdir(htmlFolder) if isfile(join(htmlFolder, f))]
        for htmlName in allHtmls:
            print('\t--- Current file: {}'.format(htmlName))
            try:
                html = os.path.join(htmlFolder, htmlName)
                self.replace_svg_tags(html)
                self.replace_markers(html)
                self.replace_headers(html)
            except:
                print("\t--- Skip file: {}".format(htmlName))

    def repair_toc_ncx(self):
        print('\t\t--- Repairing toc.ncx file...')
        self.toc_folder = os.path.join(self.toc_folder, "toc.ncx")
        try:
            f = open(self.toc_folder, 'r', encoding='utf-8')
        except:
            print("\t\t--- ! toc.ncx not in ops directory")
            self.toc_folder = os.path.join(self.toc_folder[:-11], "OEBPS/toc.ncx")
            f = open(self.toc_folder, 'r', encoding='utf-8')
        pattern = r'html(#.+?)"'
        INPUT = f.read()
        strings = re.findall(pattern, INPUT, flags=re.S)
        for string in strings:
            INPUT = INPUT.replace(string, "")
        f.close()
        f = open(self.toc_folder, 'w', encoding='utf-8')
        f.write(INPUT)
        f.close()

    def replace_svg_tags(self, filename):
        print('\t\t--- Replasing SVG Tags...')
        f = open(os.path.join(self.location, filename), 'r', encoding='utf-8')
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
        f = open(os.path.join(self.location, filename), 'w', encoding='utf-8')
        f.write(INPUT)
        f.close()

    def replace_markers(self, filename):
        print('\t\t--- Replasing Markers...')
        f = open(os.path.join(self.location, filename), mode='r', encoding='utf-8')
        pattern = r'<p class=".+?><img.+?"\/>(.+?)<\/p>'
        pattern_full_message = r'(<p class=".+?><img.+?"\/>.+?<\/p>)'
        INPUT = f.read()
        # print(INPUT)
        full_messages = re.findall(pattern_full_message, INPUT)  # строки целиком вместе с тегами
        strings = re.findall(pattern, INPUT)  # только текст
        i = 0
        correctStrings = []  # исправленные строки с тегами
        for text in strings:
            correctStrings.append('<ul><li>{!s}</li></ul>'.format(text))
            INPUT = INPUT.replace(full_messages[i], correctStrings[i])
            i += 1
            # print(INPUT)
        print('\t\t--- Editing <ul> and <li> tags...')
        INPUT = INPUT.replace("</ul>\n<ul>", "\n")
        f.close()
        f = open(os.path.join(self.location, filename), 'w', encoding='utf-8')
        f.write(INPUT)
        f.close()

    def replace_headers(self, filename):
        print('\t\t--- Replasing headers...')
        f = open(os.path.join(self.location, filename), 'r', encoding='utf-8')
        pattern = r'<h. class="h(.)".+?\/h.>'
        pattern_full_message = r'(<h. class="h.".+?\/h.>)'
        INPUT = f.read()
        strings = re.findall(pattern, INPUT)  # только текст
        full_message = re.findall(pattern_full_message, INPUT)
        i = 0
        INPUT = INPUT.replace("h4", "h3")
        for text in full_message:
            if int(strings[i]) == 2:
                new_message = '<div class="chapter_header">{!s}</div>'.format(text)
                INPUT = INPUT.replace(text, new_message)
            # if int(strings[i]) == 3:
            #     temp_string = strings[i].capitalize()
            #     new_message = text.replace(strings[i], temp_string)
            #     INPUT = INPUT.replace(text, new_message)

            i += 1
        print('\t\t--- Correcting quotes...')
        INPUT = INPUT.replace("chap-bq", "right")
        INPUT = INPUT.replace("&#8212;", " &#8212 ")
        f.close()
        f = open(os.path.join(self.location, filename), 'w', encoding='utf-8')
        f.write(INPUT)
        f.close()


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
