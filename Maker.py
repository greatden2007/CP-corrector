__author__ = 'kudinovdenis'
import os
import re
import zipfile
from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup
import shutil


class Maker(object):
    def __init__(self):
        # non-safe defenition ( = "" ). Sets inside correctAllHtml()
        self.toc_folder = ""
        self.html_folder = ""
        self.epub_number = ""
        # self.ok = True
        self.toc_ids = []
        self.opf_ids_part1 = []
        self.opf_ids_part2 = []
        self.big_strings = []
        self.small_strings = []
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
                self.epub_number = epubNameWithoutFormat

                print('\t--- Current epub: {}'.format(epubnameWithFormat))
                self.unarchiveEpub(epubnameWithFormat, epubNameWithoutFormat)
                self.correctAllHtml(htmlFolder)
                os.remove(outZipPath)
                # if self.ok:
                #     outZipPath = inZipPath + "_ok.epub"
                # else:
                #     outZipPath = inZipPath + "_not_ok.epub"
                #     self.ok = True
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
        try:
            allHtmls = [f for f in listdir(htmlFolder) if isfile(join(htmlFolder, f))]
            self.html_folder = htmlFolder
        except:
            print("First try finding HTML directory failed. Second try...")
            htmlFolder = os.path.join(htmlFolder[:-10], "OEBPS")
            self.html_folder = htmlFolder
            allHtmls = [f for f in listdir(htmlFolder) if isfile(join(htmlFolder, f))]
        self.repair_toc_ncx()

        try:
            allHtmls = [f for f in listdir(htmlFolder) if isfile(join(htmlFolder, f))]
            self.html_folder = htmlFolder
        except:
            print("First try finding HTML directory failed. Second try...")
            htmlFolder = os.path.join(htmlFolder[:-10], "OEBPS")
            self.html_folder = htmlFolder
            allHtmls = [f for f in listdir(htmlFolder) if isfile(join(htmlFolder, f))]
        # self.repair_toc_ncx_NOT_USED()
        for htmlName in allHtmls:
            print('\t--- Current file: {}'.format(htmlName))
            try:
                html = os.path.join(htmlFolder, htmlName)
                self.replace_svg_tags(html)
                self.replace_markers(html)
                self.replace_headers(html)
                if "css" in htmlName:
                    os.remove(html)
            except:
                print("\t--- Skip file: {}".format(htmlName))

    def repair_toc_ncx(self):
        print('\t\t--- Repairing toc.ncx file, .opf file...')
        self.toc_folder = os.path.join(self.toc_folder, "toc.ncx")
        try:
            f = open(self.toc_folder, 'r', encoding='utf-8')
        except:
            print("\t\t\t--- ! toc.ncx not in ops directory")
            self.toc_folder = os.path.join(self.toc_folder[:-11], "OEBPS/toc.ncx")
            f = open(self.toc_folder, 'r', encoding='utf-8')
        for file in os.listdir(self.toc_folder[:-7]):
            if file.endswith(".opf"):
                opf_file = os.path.join(self.toc_folder[:-7], file)

        pattern = r'src="(.*?\/)*(.+?\..*html)#(.+?)"'
        toc_id_pattern = r'id\s*=\s*"(.+?)"'
        INPUT = f.read()

        self.toc_ids = re.findall(toc_id_pattern, INPUT)
        opfFile = open(opf_file, 'r', encoding='utf-8')
        opfINPUT = opfFile.read()

        strings = re.findall(pattern, INPUT)
        i = 0
        toc_id_pattern = r'<navPoint id="(.+?)".+?<content src="(?:xhtml\/|)(.+?html)\#*(.*?)"'
        old_ids_refs_parts = re.findall(toc_id_pattern, INPUT, flags=re.S)

        for chapter in strings:
            # self.ok = False
            filename = chapter[1]
            part = chapter[2]
            self.splitHTML(filename, part)
            new_name = self.change_file_name(filename, part)
            old_str = filename + "#" + part
            INPUT = INPUT.replace(old_str, new_name, 1)
            # old_ids_refs_parts[self.toc_ids[i]] = filename
            # new_ids_refs_parts[self.toc_ids[i]] = new_name
            i += 1

        toc_id_pattern = r'<navPoint id="(.+?)".+?<content src="(xhtml\/|)(.+?html)"'
        new_ids_refs_parts = re.findall(toc_id_pattern, INPUT, flags=re.S)

        f.close()
        f = open(self.toc_folder, 'w', encoding='utf-8')
        f.write(INPUT)
        f.close()


        #работа с 1/2 блоками в .opf + удаление информации из toc.ncx и .opf
        ids = []
        new_lines = ""
        pattern = r'(<item id="(.+?)" href="(?:xhtml\/|)(.+?)" media-type=".+?"\s*\/>)'
        lines = []
        f = open(self.toc_folder, 'r', encoding='utf-8')
        INPUT = f.read()
        j = 0
        # part 1
        old_lines = re.findall(pattern, opfINPUT)
        for old_line in old_lines:
            for id_ref_part in old_ids_refs_parts:
                if id_ref_part[1] == old_line[2]:
                    for new_id_ref_part in new_ids_refs_parts:
                        if id_ref_part[0] == new_id_ref_part[0]:
                            #создаем новую строку и добавляем в массив новых строк
                            string = '<item id="{}" href="{}" media-type="application/xhtml+xml" />'.format(
                                id_ref_part[0], new_id_ref_part[2])
                            new_lines += string + "\n"
                            ids.append(new_id_ref_part[0])
                            lines.append(string)
                            main_id = old_line[1]
            if "" != new_lines:
                if len(lines) > 0:
                    lines = []
                    opfINPUT = opfINPUT.replace(old_line[0], new_lines)
                    opfINPUT = opfINPUT.replace(old_line[0], "")
                    new_lines = ""
                    ids_string = ""
                    # part 2
                    for part_id in ids:
                        ids_string += '<itemref idref="{}" />\n'.format(part_id)
                    opfINPUT = opfINPUT.replace('<itemref idref="{}" />'.format(main_id), ids_string)
                    opfINPUT = opfINPUT.replace('<itemref idref="{}" />'.format(main_id), "")
                    opfINPUT = opfINPUT.replace('<itemref idref="{}"/>'.format(main_id), ids_string)
                    opfINPUT = opfINPUT.replace('<itemref idref="{}"/>'.format(main_id), "")
                    #удаление из toc.ncx
                    toc_delete_pattern = '(<navPoint id="{}".+?<content src="(?:xhtml\/|).+?html"\s*\/>)'.format(ids[0])
                    ids = []
                    replacement = re.findall(toc_delete_pattern, INPUT, flags=re.S)
                    if len(lines) > 1:
                        INPUT = INPUT.replace(replacement[0],
                                              '<navPoint id="test{}" playOrder="1">\n<navLabel>\n<text>Praise</text>\n</navLabel>\n<content src="bano_9781601638687_oeb_fm1_r1.html"/>'.format(
                                                  j))
                        j += 1
                new_lines = ""
                lines = []
                ids = []
        try:
            #удаление оглавления из книг (toc)
            pattern = r'(<navPoint id="toc".+?<\/navPoint>)'
            toc = re.findall(pattern, INPUT, re.S)
            toc = toc[0]
            INPUT = INPUT.replace(toc, "")
        except:
            print("\t\t\t--- Error deleting toc from toc.ncx")
        try:
            #удаление оглавления из книг (spine)
            pattern = r'(<itemref idref="toc"\s*\/>)'
            toc = re.findall(pattern, opfINPUT, re.S)
            toc = toc[0]
            opfINPUT = opfINPUT.replace(toc, "")
        except:
            print("\t\t\t--- Error deleting toc from spine")

        f.close()
        f = open(self.toc_folder, 'w', encoding='utf-8')
        # soup = BeautifulSoup(INPUT)
        # INPUT = soup.prettify()
        f.write(INPUT)
        f.close()

        opfFile.close()
        opfFile = open(opf_file, 'w', encoding='utf-8')
        opfFile.write(opfINPUT)
        opfFile.close()


    def splitHTML(self, filename, splitter):
        f = open(os.path.join(self.html_folder, filename), 'r', encoding='utf-8')
        pattern = r'<\w+?><a id="(.+?)"\s*\/>\s*<\/\w+>(.+?)(?=<\w+?><a id=".+?"\s*\/>\s*<\/\w+>|<\/body>)'
        head_pattern = r'(.+?)<body>'
        content = ""
        INPUT = f.read()
        head = re.match(head_pattern, INPUT, flags=re.S)
        head = head.group(0)
        contents = re.findall(pattern, INPUT, flags=re.S)
        if len(contents) == 0:
            pattern = r'<a id="(.+?)".+?\/a>(.+?)(?=<a id=".+?".+?\/a>|<\/body>)'
            contents = re.findall(pattern, INPUT, flags=re.S)
        for content_group in contents:
            if splitter == content_group[0]:
                content = content_group[1]
        if len(content) < 2:
            return
        end = "</body>\n</html>"
        OUTPUT = head + content + end
        f.close()
        dot_splitter = "."
        file = filename.split(dot_splitter)
        new_file = file[0] + splitter + "." + file[1]
        f = open(os.path.join(self.html_folder, new_file), 'w', encoding='utf-8')
        f.write(OUTPUT)
        f.close()

    def change_file_name(self, old_name, chapter_name):
        dot_splitter = "."
        old_format = old_name.split(dot_splitter)[1]
        old_name = old_name.split(dot_splitter)[0]
        new_name = old_name + chapter_name + "." + old_format
        return new_name

    def repair_toc_ncx_NOT_USED(self):
        print('\t\t--- Repairing toc.ncx file...')
        self.toc_folder = os.path.join(self.toc_folder, "toc.ncx")
        # try:
        f = open(self.toc_folder, 'r', encoding='utf-8')
        # except:
        #     print("\t\t--- ! toc.ncx not in ops directory")
        #     self.toc_folder = os.path.join(self.toc_folder[:-11], "OEBPS/toc.ncx")
        #     f = open(self.toc_folder, 'r', encoding='utf-8')
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
        splitter = "."
        name = filename.split(splitter)[0]
        INPUT = f.read()
        if "cover" in filename:
            try:
                pattern = r'(<body.+?<\/p>)'
                image_pattern = r'<body.+?src="(.+?)".+?<\/p>'
                image = re.findall(image_pattern, INPUT, flags=re.S)
                image = image[0]
                new_string = '<body><div class="cover"><img alt="cover" height="95%" src="{}"/></div>'.format(image)
                image_block = re.findall(pattern, INPUT, flags=re.S)
                image_block = image_block[0]
                INPUT = INPUT.replace(image_block, new_string)
            except:
                print("\t\t\t---Ecxeption svg tags")
        pattern = r'<svg:.+?href="(.+?)".+?svg>'
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

        pattern = r'(<div class="list\w">(.+?<\/div>)<\/div>)'
        blocks = re.findall(pattern, INPUT, re.S)
        for block in blocks:
            old_block = block[0]
            new_block = "<ul>" + block[1] + "</ul>"
            pattern = r'(<div class="lsl\d"?>(.+?)<\/div>)'
            li_blocks = re.findall(pattern, old_block, re.S)
            for li_block in li_blocks:
                new_li_block = "<li>" + li_block[1] + "</li>"
                new_block = new_block.replace(li_block[0], new_li_block)
            INPUT = INPUT.replace(old_block, new_block)
        # и ещё они умудрились делать списки без обозначения того, что это списки
        pattern = r'(<div class="lsl\d"?>(.+?)<\/div>)'
        li_blocks = re.findall(pattern, INPUT, re.S)
        for li_block in li_blocks:
            new_li_block = "<ul><li>" + li_block[1] + "</li></ul>"
            INPUT = INPUT.replace(li_block[0], new_li_block)

        INPUT = INPUT.replace("&#x2022;", "")
        INPUT = INPUT.replace("</ul>\n<ul>", "\n")
        INPUT = INPUT.replace("</ul><ul>", "\n")
        pattern = r'<li>(<img src=.+?\/>)'
        images_in_li = re.findall(pattern, INPUT, re.S)
        for image_in_li in images_in_li:
            INPUT = INPUT.replace(image_in_li, "")
        # удаление от <div> до </div>
        pattern = r'(<div>(.+?)<\/div>)'
        divs = re.findall(pattern, INPUT, re.S)
        for div in divs:
            INPUT = INPUT.replace(div[0], div[1])
        f.close()
        f = open(os.path.join(self.location, filename), 'w', encoding='utf-8')
        f.write(INPUT)
        f.close()

    def replace_headers(self, filename):
        splitter = "."
        format = filename.split(splitter)
        format = format[1]
        print('\t\t--- Replasing headers...')
        if not "ncx" in filename and not "opf" in filename:
            f = open(os.path.join(self.location, filename), 'r', encoding='utf-8')
            pattern = r'<h. class="h(.)".+?\/h.>'
            pattern_full_message = r'(<h. class="h.".+?\/h.>)'
            INPUT = f.read()
            strings = re.findall(pattern, INPUT, re.S)  # только текст
            full_message = re.findall(pattern_full_message, INPUT, re.S)
            i = 0
            INPUT = INPUT.replace("h4", "h3")
            for text in full_message:
                if int(strings[i]) == 2 or int(strings[i]) == 1:
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

            pattern = r'(<div class="(?:tx|tx1|fmhT|fmtx|atx1|fmtx1|epiv|eps)">(<div class="(?:tx|tx1|fmhT|fmtx|atx1|fmtx1|epiv|eps)">)*(.+?)<\/div>.*?(<\/div>)*)'
            divs = re.findall(pattern, INPUT, re.S)
            for div in divs:
                new_line = "<p>" + div[2] + "</p>"
                INPUT = INPUT.replace(div[0], new_line)
            divs = re.findall(pattern, INPUT, re.S)
            for div in divs:
                new_line = "<p>" + div[2] + "</p>"
                INPUT = INPUT.replace(div[0], new_line)
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
