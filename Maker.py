__author__ = 'kudinovdenis'
import os
import re
import zipfile
from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup
import time
import shutil


class Maker(object):
    """
    класс обрабатывает входящие епабы
    """

    def __init__(self):
        """
        метод устанавливает начальные значения переменным
        и определяет место запуска и пути к файлам, лежащим в данной папке
        """
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
        """
        метод устанавливает пути к файлам toc и к папке с html-страницами,
        разархивирует епаб в папку, запускает обработку и архивирует обратно
        """
        i = 0  # счётчик епабов в папке
        start_time = int(round(time.time()))
        for epubnameWithFormat in self.onlyfiles:
            try:
                splitter = "."
                epubNameWithoutFormat = epubnameWithFormat.split(splitter)[0]   # имя епаба без формата
                htmlFolder = os.path.join(self.location, epubNameWithoutFormat + "/ops/xhtml/") # папка, содержащая html-страницы
                self.toc_folder = os.path.join(self.location, epubNameWithoutFormat + "/ops/")  # папка, содержащая файл toc.ncx
                inZipPath = os.path.join(self.location, epubNameWithoutFormat)  # имя входного архива
                outZipPath = os.path.join(self.location, epubnameWithFormat)    # имя выходного архива
                self.epub_number = epubNameWithoutFormat

                print('\t--- Current epub: {}'.format(epubnameWithFormat))
                self.unarchiveEpub(epubnameWithFormat, epubNameWithoutFormat)
                self.correctAllHtml(htmlFolder)
                os.remove(outZipPath)
                self.zip(inZipPath, outZipPath)
                shutil.rmtree(inZipPath)
                i += 1
            except:
                print("skip  " + epubnameWithFormat)
        stop_time = int(round(time.time()))
        delta = stop_time - start_time
        print("\t--- Done {} epubs".format(i))
        print("Time: {}seconds, avg.time: {} ".format(delta, delta / i))    #среднее время на книгу


    def unarchiveEpub(self, archiveName, destinationFolderName):
        """
        разархивация епаба из archiveName в папку destinationFolderName

        @type archiveName: string
        @type destinationFolderName: string
        """
        inputPath = os.path.join(self.location, archiveName)
        outputPath = os.path.join(self.location, destinationFolderName)
        with zipfile.ZipFile(inputPath, "r") as z:
            z.extractall(outputPath)

    def correctAllHtml(self, htmlFolder):
        """
        метод ищет папку htmlFolder и запускает редактирование файлов

        @param htmlFolder: имя папки, в которой содержатся html файлы
        @type htmlFolder: string
        """
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
        """
        метод редактирует файлы toc.ncx, content.opf и разделяет файлы html
        """
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
        toc_id_pattern = r'<navPoint id="(.+?)".+?<content src="((?:x?html\/)*.+?html)\#*(.*?)"'
        old_ids_refs_parts = re.findall(toc_id_pattern, INPUT, flags=re.S)
        for chapter in strings:
            # self.ok = False
            j = 0
            chapters_for_current_file = []
            filename = chapter[1]
            part = chapter[2]
            for chapter1 in strings:
                if chapter1[1] == filename:
                    j += 1
                    chapters_for_current_file.append(chapter1[2])

            self.splitHTML(filename, part, j, chapters_for_current_file)
            new_name = self.change_file_name(filename, part)
            old_str = filename + "#" + part
            INPUT = INPUT.replace(old_str, new_name, 1)
            # old_ids_refs_parts[self.toc_ids[i]] = filename
            # new_ids_refs_parts[self.toc_ids[i]] = new_name
            i += 1

        toc_id_pattern = r'<navPoint id="(.+?)".+?<content src="((?:x?html\/)*.+?html)\#*(.*?)"'
        new_ids_refs_parts = re.findall(toc_id_pattern, INPUT, flags=re.S)

        f.close()
        f = open(self.toc_folder, 'w', encoding='utf-8')
        f.write(INPUT)
        f.close()


        #работа с 1 и 2 блоками в .opf + удаление информации из toc.ncx и .opf
        ids = []
        new_lines = ""
        pattern = r'(<item id="(.+?)"\n*\s*? href="(.+?)"\n*\s*? media-type=".+?"\s*\/>)'
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
                                id_ref_part[0], new_id_ref_part[1])
                            new_lines += string + "\n"
                            ids.append(new_id_ref_part[0])
                            lines.append(string)
                            main_id = old_line[1]
            if "" != new_lines:
                if len(lines) > 0:
                    opfINPUT = opfINPUT.replace(old_line[0], new_lines)
                    if len(lines) > 1:
                        opfINPUT = opfINPUT.replace(old_line[0], "")
                        line_another_format = old_line[0]
                        line_another_format = line_another_format[:-2] + " />"
                        opfINPUT = opfINPUT.replace(line_another_format, "")
                    new_lines = ""
                    ids_string = ""
                    # part 2
                    for part_id in ids:
                        ids_string += '<itemref idref="{}" />\n'.format(part_id)
                    opfINPUT = opfINPUT.replace('<itemref idref="{}" />'.format(main_id), ids_string)
                    if len(lines) > 1:
                        opfINPUT = opfINPUT.replace('<itemref idref="{}" />'.format(main_id), "")
                    opfINPUT = opfINPUT.replace('<itemref idref="{}"/>'.format(main_id), ids_string)
                    if len(lines) > 1:
                        opfINPUT = opfINPUT.replace('<itemref idref="{}"/>'.format(main_id), "")
                        # чтоб наверняка удалить main id
                        opfINPUT = opfINPUT.replace('<itemref idref="{}" />'.format(main_id), "")
                    #удаление из toc.ncx
                    toc_delete_pattern = '(<navPoint id="{}".+?<content src="(?:xhtml\/|).+?html"\s*\/>)'.format(ids[0])
                    ids = []
                    replacement = re.findall(toc_delete_pattern, INPUT, flags=re.S)

                    # удаление основных разделов из toc.ncx (например, ch066 если присутствуют ch06ch06, ch06lev01...)
                    if len(lines) > 1:
                        # INPUT = INPUT.replace(replacement[0],
                        #                       '<navPoint id="test{}" playOrder="1">\n<navLabel>\n<text>Praise</text>\n</navLabel>\n<content src="bano_9781601638687_oeb_fm1_r1.html"/>'.format(
                        #                           j))
                        j += 1
                    lines = []
                new_lines = ""
                lines = []
                ids = []
        try:
            #удаление оглавления из книг (toc)
            pattern = r'(<navPoint id="toc".+?<\/navPoint>)'
            toc = re.findall(pattern, INPUT, re.S)
            if len(toc) > 0:
                toc = toc[0]
                INPUT = INPUT.replace(toc, "")

            # удаление файла, если он называется Contents
            pattern = r'(<navP.+?>\n<navL.+?>\n<text>Contents<\/text>\n<\/navLabel>\n<content src="(.+?)"\/>\n<\/navPoint>)'
            found = re.findall(pattern, INPUT)
            if len(found) > 0:
                found = found[0]
                toc = found[0]
                ref = found[1]
                INPUT = INPUT.replace(toc, "")

            # и если Table of Contents
            pattern = r'(<navP.+?>\n*?<navL.+?>\n*?<text>Table of Contents<\/text>\n*?<\/navLabel>\n*?<content src="(.+?)"\/>\n*?<\/navPoint>)'
            found = re.findall(pattern, INPUT)
            if len(found) > 0:
                found = found[0]
                toc = found[0]
                ref = found[1]
                INPUT = INPUT.replace(toc, "")

        except:
            print("\t\t\t--- Error deleting toc from toc.ncx")
        try:
            #удаление оглавления из книг (spine)
            pattern = r'(<itemref idref="toc"\s*\/>)'
            toc = re.findall(pattern, opfINPUT, re.S)
            if len(toc) > 0:
                toc = toc[0]
                opfINPUT = opfINPUT.replace(toc, "")

            pattern = r'(<item id="(.+?)" href="{}" media-type="application/xhtml\+xml"\s*/>)'.format(ref)
            found = re.findall(pattern, opfINPUT)
            if len(found) > 0:
                found = found[0]
                opf1 = found[0]
                id = found[1]
                opfINPUT = opfINPUT.replace(opf1, "")
                pattern = r'(<itemref idref="{}"\s*\/>)'.format(id)
                opf2 = re.findall(pattern, opfINPUT)
                if len(opf2) > 0:
                    opf2 = opf2[0]
                    opfINPUT = opfINPUT.replace(opf2, "")
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


    def splitHTML(self, filename, splitter, count, chapters_for_file):
        """
        метод, раздеяющий страницу html на подстраницы для разбиения на подглавы

        выбирается массив всех глав в файле и ищутся две главы с соседними именами
        или, если эта глава единственная/последняя, то берётся весь файл до тега </body>
        текущая глава -- splitter;
        следующая глава: chapters_for_file[chapters_for_file.index(splitter)+1]

        @param filename: имя входного html файла
        @type filename: string

        @param splitter: имя очередной главы
        @type splitter: string

        @param count: количество глав в файле
        @type count: int

        @param chapters_for_file: список всех глав в файле
        @type chapters_for_file: string[]

        """
        current_chapter = splitter
        for chapter in chapters_for_file:
            if splitter == chapter:

                # если глава первая,
                # то взять всё от начала документа (тега <body> до второй главы)
                if chapters_for_file.index(splitter) == 0 and len(chapters_for_file) > 0:
                    content = ""
                    # если состоит из одной главы
                    if len(chapters_for_file) == 1:
                        f = open(os.path.join(self.html_folder, filename), 'r', encoding='utf-8')
                        INPUT = f.read()

                        pattern = r'<body>(.+?)</body>'
                        content = re.findall(pattern, INPUT, re.S)
                        head_pattern = r'(.+?)<body>'
                        head = re.match(head_pattern, INPUT, flags=re.S)
                        head = head.group(0)
                        end = "</body>\n</html>"
                        if len(content[0]) > 0:
                            OUTPUT = head + content[0] + end
                            f.close()
                            dot_splitter = "."
                            file = filename.split(dot_splitter)
                            new_file = file[0] + splitter + "." + file[1]
                            f = open(os.path.join(self.html_folder, new_file), 'w', encoding='utf-8')
                            f.write(OUTPUT)
                            f.close()
                    else:
                        next_chapter = chapters_for_file[chapters_for_file.index(splitter) + 1]

                        f = open(os.path.join(self.html_folder, filename), 'r', encoding='utf-8')
                        pattern = r'<body>(.+?(?=<\w+?><a id="{}"\s*\/>\s*<\/\w+>))'.format(next_chapter)
                        head_pattern = r'(.+?)<body>'
                        INPUT = f.read()
                        head = re.match(head_pattern, INPUT, flags=re.S)
                        head = head.group(0)
                        contents = re.findall(pattern, INPUT, flags=re.S)

                        # до тега h#, чтобы он не обрезался
                        if len(contents) == 0:
                            additional_contents_pattern13 = r'<body>(.+?)(?:<h. class="h."><a id="{}".+?\/a>)'.format(next_chapter)
                            additional_contents13 = re.findall(additional_contents_pattern13, INPUT, re.S)
                            contents += additional_contents13

                        if len(contents) == 0:
                            #(?:<a id=".+?".+?\/a>)*<a id="(.+?)".+?\/a>(.+?)(?=<a id=".+?".+?\/a>|<\/body>)
                            additional_contents_pattern1 = r'<body>(.+?(?=<a id="{}".+?\/a>))'.format(next_chapter)
                            additional_contents1 = re.findall(additional_contents_pattern1, INPUT, flags=re.S)
                            contents += additional_contents1

                        if len(contents) == 0:
                            additional_contents_pattern9 = r'<body>(.+?(?=<h. class="h..*?".+?<a id="{}".+?\/a>))'.format(
                                next_chapter)
                            additional_contents9 = re.findall(additional_contents_pattern9, INPUT, re.S)
                            contents += additional_contents9

                        if len(contents) == 0:
                            additional_contents_pattern2 = r'<body>(.+?(?=<a id="{}".+?\/a>))'.format(next_chapter)
                            additional_contents2 = re.findall(additional_contents_pattern2, INPUT, re.S)
                            contents += additional_contents2

                        if len(contents) == 0:
                            additional_contents_pattern12 = r'<body>(.+?(?=<h\d class="h..?" id="{}"))'.format(next_chapter)
                            additional_contents12 = re.findall(additional_contents_pattern12, INPUT, re.S)
                            contents += additional_contents12

                        if len(contents) == 0:
                            # <h# class="h#" id="??"
                            additional_contents_pattern3 = r'<body>(.+?(?=<h\d class="h..*?" id="{}"))'.format(
                                next_chapter)
                            additional_contents3 = re.findall(additional_contents_pattern3, INPUT, re.S)
                            contents += additional_contents3

                        if len(contents) == 0:
                            # ch02a
                            additional_contents_pattern4 = r'<body>(.+?(?:<a id="{}".+?\/a>))'.format(next_chapter)
                            additional_contents4 = re.findall(additional_contents_pattern4, INPUT, re.S)
                            contents += additional_contents4

                        if len(contents) == 0:
                            additional_contents_pattern5 = r'<body>(.+?(?=<a id="{}".+?\/a>))'.format(next_chapter)
                            additional_contents5 = re.findall(additional_contents_pattern5, INPUT, re.S)
                            contents += additional_contents5

                        if len(contents) == 0:
                            additional_contents_pattern6 = r'<body>(.+?(?=<a id="{}".+?\/a>))'.format(next_chapter)
                            additional_contents6 = re.findall(additional_contents_pattern6, INPUT, re.S)
                            contents += additional_contents6

                        if len(contents) == 0:
                            additional_contents_pattern8 = r'<body>(.+?(?=<a id="{}".+?\/a>))'.format(next_chapter)
                            additional_contents8 = re.findall(additional_contents_pattern8, INPUT, re.S)
                            contents += additional_contents8

                        if len(contents) == 0:
                            additional_contents_pattern10 = r'<body>(.+?(?=<p id="{}" class=".+?">))'.format(
                                next_chapter)
                            additional_contents10 = re.findall(additional_contents_pattern10, INPUT, re.S)
                            contents += additional_contents10

                        if len(contents) == 0:
                            additional_contents_pattern11 = r'<body>(.+?(?=<p class=".+?" id="{}">))'.format(
                                next_chapter)
                            additional_contents11 = re.findall(additional_contents_pattern11, INPUT, re.S)
                            contents += additional_contents11

                        for content_group in contents:
                            if len(content_group) > 1:
                                content = content_group
                                break
                        if content == "":
                            additional_contents_pattern7 = r'<body>(.+?(?=<a id="{}".+?\/a>))'.format(next_chapter)
                            additional_contents7 = re.findall(additional_contents_pattern7, INPUT, re.S)
                            for content_group in additional_contents7:
                                if len(content_group) > 1:
                                    content = content_group
                                    break

                        end = "</body>\n</html>"
                        OUTPUT = head + content + end
                        f.close()
                        dot_splitter = "."
                        file = filename.split(dot_splitter)
                        new_file = file[0] + splitter + "." + file[1]
                        f = open(os.path.join(self.html_folder, new_file), 'w', encoding='utf-8')
                        f.write(OUTPUT)
                        f.close()

                # если глава не последняя, но и не первая
                # глава посреди текста
                elif chapters_for_file.index(splitter) != len(chapters_for_file) - 1:

                    next_chapter = chapters_for_file[chapters_for_file.index(splitter) + 1]

                    f = open(os.path.join(self.html_folder, filename), 'r', encoding='utf-8')
                    pattern = r'(<\w+?><a id="({})"\s*\/>\s*<\/\w+>.+?(?=<\w+?><a id="{}"\s*\/>\s*<\/\w+>))'.format(
                        current_chapter, next_chapter)
                    head_pattern = r'(.+?)<body>'
                    INPUT = f.read()
                    head = re.match(head_pattern, INPUT, flags=re.S)
                    head = head.group(0)
                    contents = re.findall(pattern, INPUT, flags=re.S)

                    content = ""

                    if len(contents) == 0:
                        additional_contents_pattern9 = r'(<h. class="h.".{{0,50}}<a id="({})".+?\/a>(.+?))(?:<h. class="h..{{0,1}}".{{0,50}}<a id="{}".+?\/a>)'.format(
                            current_chapter, next_chapter)
                        additional_contents9 = re.findall(additional_contents_pattern9, INPUT, re.S)
                        contents += additional_contents9

                    if len(contents) == 0:
                        #(?:<a id=".+?".+?\/a>)*<a id="(.+?)".+?\/a>(.+?)(?=<a id=".+?".+?\/a>|<\/body>)
                        additional_contents_pattern1 = r'(<a id="({})".+?\/a>(.+?)(?=<a id="{}".+?\/a>))'.format(
                            current_chapter, next_chapter)
                        additional_contents1 = re.findall(additional_contents_pattern1, INPUT, flags=re.S)
                        contents += additional_contents1

                    if len(contents) == 0:
                        # ch##lev#
                        additional_contents_pattern2 = r'(<a id="({})".+?\/a>(.+?)(?=<a id="{}".+?\/a>))'.format(
                            current_chapter, next_chapter)
                        additional_contents2 = re.findall(additional_contents_pattern2, INPUT, re.S)
                        contents += additional_contents2

                    if len(contents) == 0:
                        additional_contents_pattern12 = r'(<h\d class="h..?" id="({})">(.+?)(?=<h\d class="h..?" id="{}"))'.format(current_chapter, next_chapter)
                        additional_contents12 = re.findall(additional_contents_pattern12, INPUT, re.S)
                        contents += additional_contents12

                    if len(contents) == 0:
                        # <h# class="h#" id="??"
                        additional_contents_pattern3 = r'(<h\d class="h..*?" id="({})">(.+?)(?=<h\d class="h..*?" id="{}"))'.format(
                            current_chapter, next_chapter)
                        additional_contents3 = re.findall(additional_contents_pattern3, INPUT, re.S)
                        contents += additional_contents3


                    if len(contents) == 0:
                        # ch02a
                        additional_contents_pattern4 = r'(<a id="ch\w+?"><\/a><a id="({})"><\/a>(.+?)(?:<a id="{}".+?\/a>))'.format(
                            current_chapter, next_chapter)
                        additional_contents4 = re.findall(additional_contents_pattern4, INPUT, re.S)
                        contents += additional_contents4

                    if len(contents) == 0:
                        additional_contents_pattern5 = r'(<a id="page\w+?"><\/a><a id="({})"><\/a>(.+?)(?=<a id="{}".+?\/a>))'.format(
                            current_chapter, next_chapter)
                        additional_contents5 = re.findall(additional_contents_pattern5, INPUT, re.S)
                        contents += additional_contents5

                    if len(contents) == 0:
                        additional_contents_pattern6 = r'(<a id="ch.+?".+?\/a><a id="({})".+?<\/a>(.+?)(?=<a id="{}".+?\/a>))'.format(
                            current_chapter, next_chapter)
                        additional_contents6 = re.findall(additional_contents_pattern6, INPUT, re.S)
                        contents += additional_contents6

                    if len(contents) == 0:
                        additional_contents_pattern8 = r'(<h. class="h..*<a id="page\w+?"><\/a><a id="{}"><\/a>(.+?)(?=<a id="{}".+?\/a>))'.format(
                            current_chapter, next_chapter)
                        additional_contents8 = re.findall(additional_contents_pattern8, INPUT, re.S)
                        contents += additional_contents8

                    if len(contents) == 0:
                        additional_contents_pattern10 = r'(<p id="({})" class=".+?">(.+?)(?=<p id="{}" class=".+?">))'.format(
                            current_chapter, next_chapter)
                        additional_contents10 = re.findall(additional_contents_pattern10, INPUT, re.S)
                        contents += additional_contents10

                    if len(contents) == 0:
                        additional_contents_pattern11 = r'(<p class=".+?" id="({})">.+?(?=<p class=".+?" id="{}">))'.format(
                            current_chapter, next_chapter)
                        additional_contents11 = re.findall(additional_contents_pattern11, INPUT, re.S)
                        contents += additional_contents11

                    for content_group in contents:
                        if splitter == content_group[0]:
                            content = content_group[1]
                            break
                    if content == "":
                        for content_group in contents:
                            if splitter == content_group[1]:
                                content = content_group[0]
                                break
                    if content == "":
                        additional_contents_pattern7 = r'(<a id="lev.+?".+?<\/a><a id="({})".+?<\/a>(.+?)(?=<a id="{}".+?\/a>))'.format(
                            current_chapter, next_chapter)
                        additional_contents7 = re.findall(additional_contents_pattern7, INPUT, re.S)
                        for content_group in additional_contents7:
                            if splitter == content_group[0]:
                                content = content_group[1]
                                break

                    # пробегаемся по всем id и если такой в контенте нет, то добавляем контент по этой id
                    # for content_group in contents:
                    #     if not content_group[0] in content:
                    #         content += content_group[1]
                    if count == 1:
                        for content_group in contents:
                            if not content_group[1] in content:
                                content += content_group[0]

                    end = "</body>\n</html>"
                    OUTPUT = head + content + end
                    f.close()
                    dot_splitter = "."
                    file = filename.split(dot_splitter)
                    new_file = file[0] + splitter + "." + file[1]
                    f = open(os.path.join(self.html_folder, new_file), 'w', encoding='utf-8')
                    f.write(OUTPUT)
                    f.close()
                # если глава последняя
                # то берём всё от её начала до тега </body>
                else:
                    f = open(os.path.join(self.html_folder, filename), 'r', encoding='utf-8')
                    pattern = r'(<\w+?><a id="({})"\s*\/>\s*<\/\w+>.+?(?=<\/body>))'.format(current_chapter)
                    head_pattern = r'(.+?)<body>'
                    INPUT = f.read()
                    head = re.match(head_pattern, INPUT, flags=re.S)
                    head = head.group(0)
                    contents = re.findall(pattern, INPUT, flags=re.S)

                    content = ""

                    if len(contents) == 0:
                        additional_contents_pattern9 = r'(<h. class="h..{{0,1}}">.{{0,50}}<a id="({})".+?\/a>(.+?)(?=<\/body>))'.format(current_chapter)
                        additional_contents9 = re.findall(additional_contents_pattern9, INPUT, re.S)
                        contents += additional_contents9

                    if len(contents) == 0:
                        #(?:<a id=".+?".+?\/a>)*<a id="(.+?)".+?\/a>(.+?)(?=<a id=".+?".+?\/a>|<\/body>)
                        additional_contents_pattern1 = r'(<a id="({})".+?\/a>(.+?)(?=<\/body>))'.format(current_chapter)
                        additional_contents1 = re.findall(additional_contents_pattern1, INPUT, flags=re.S)
                        contents += additional_contents1

                    if len(contents) == 0:
                        # ch##lev#
                        additional_contents_pattern2 = r'(<a id="({})".+?\/a>(.+?)(?=<\/body>))'.format(current_chapter)
                        additional_contents2 = re.findall(additional_contents_pattern2, INPUT, re.S)
                        contents += additional_contents2

                    if len(contents) == 0:
                        additional_contents_pattern12 = r'(<h\d class="h..?" id="({})">(.+?)(?=<\/body>))'.format(current_chapter)
                        additional_contents12 = re.findall(additional_contents_pattern12, INPUT, re.S)
                        contents += additional_contents12

                    if len(contents) == 0:
                        # <h# class="h#" id="??"
                        additional_contents_pattern3 = r'(<h\d class="h..*?" id="({})">(.+?)(?=<\/body>))'.format(
                            current_chapter)
                        additional_contents3 = re.findall(additional_contents_pattern3, INPUT, re.S)
                        contents += additional_contents3

                    if len(contents) == 0:
                        # ch02a
                        additional_contents_pattern4 = r'(<a id="ch\w+?"><\/a><a id="({})"><\/a>(.+?)(?:<\/body>))'.format(
                            current_chapter)
                        additional_contents4 = re.findall(additional_contents_pattern4, INPUT, re.S)
                        contents += additional_contents4

                    if len(contents) == 0:
                        additional_contents_pattern5 = r'(<a id="page\w+?"><\/a><a id="({})"><\/a>(.+?)(?=<\/body>))'.format(
                            current_chapter)
                        additional_contents5 = re.findall(additional_contents_pattern5, INPUT, re.S)
                        contents += additional_contents5

                    if len(contents) == 0:
                        additional_contents_pattern6 = r'(<a id="ch.+?".+?\/a><a id="({})".+?<\/a>(.+?)(?=<\/body>))'.format(
                            current_chapter)
                        additional_contents6 = re.findall(additional_contents_pattern6, INPUT, re.S)
                        contents += additional_contents6

                    if len(contents) == 0:
                        additional_contents_pattern8 = r'(<h. class="h..*<a id="page\w+?"><\/a><a id="({})"><\/a>(.+?)(?=<\/body>))'.format(
                            current_chapter)
                        additional_contents8 = re.findall(additional_contents_pattern8, INPUT, re.S)
                        contents += additional_contents8

                    if len(contents) == 0:
                        additional_contents_pattern10 = r'(<p id="({})" class=".+?">.+?(?=<\/body>))'.format(
                            current_chapter)
                        additional_contents10 = re.findall(additional_contents_pattern10, INPUT, re.S)
                        contents += additional_contents10

                    if len(contents) == 0:
                        additional_contents_pattern11 = r'(<p class=".+?" id="({})">.+?(?=<\/body>))'.format(
                            current_chapter)
                        additional_contents11 = re.findall(additional_contents_pattern11, INPUT, re.S)
                        contents += additional_contents11

                    for content_group in contents:
                        if splitter == content_group[0]:
                            content = content_group[1]
                            break
                    if content == "":
                        for content_group in contents:
                            if splitter == content_group[1]:
                                content = content_group[0]
                                break
                    if content == "":
                        additional_contents_pattern7 = r'<a id="lev.+?".+?<\/a><a id="({})".+?<\/a>(.+?)(?=<\/body>)'.format(
                            current_chapter)
                        additional_contents7 = re.findall(additional_contents_pattern7, INPUT, re.S)
                        for content_group in additional_contents7:
                            if splitter == content_group[0]:
                                content = content_group[1]
                                break

                    # пробегаемся по всем id и если такой в контенте нет, то добавляем контент по этой id
                    # for content_group in contents:
                    #     if not content_group[0] in content:
                    #         content += content_group[1]
                    if count == 1:
                        for content_group in contents:
                            if not content_group[1] in content:
                                content += content_group[0]

                    end = "</body>\n</html>"
                    OUTPUT = head + content + end
                    f.close()
                    dot_splitter = "."
                    file = filename.split(dot_splitter)
                    new_file = file[0] + splitter + "." + file[1]
                    f = open(os.path.join(self.html_folder, new_file), 'w', encoding='utf-8')
                    f.write(OUTPUT)
                    f.close()
                if content == "":
                    print("Not enough data to split HTML. file: {} with chapter {}".format(filename, splitter))

    def change_file_name(self, old_name, chapter_name):
        """
        метод прибавляет к названию входного файла имя главы

        @param old_name: имя входного файла
        @type old_name: string

        @param chapter_name: имя главы
        @type chapter_name: string
        """
        dot_splitter = "."
        old_format = old_name.split(dot_splitter)[1]
        old_name = old_name.split(dot_splitter)[0]
        new_name = old_name + chapter_name + "." + old_format
        return new_name

    def repair_toc_ncx_NOT_USED(self):
        """
        метод убирает части, оставляя в оглавлении только главы

        !!! НЕ ИСПОЛЬЗУЕТСЯ !!!
        """
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
        """
        работа с картинками в cover в формате <svg:...svg>, переделывание их в
        <div class="cover"><img alt="cover" height="95%" src="<svg:...svg>"/></div>

        @param filename: имя входного файла html
        @type filename: string
        """
        print('\t\t--- Replasing SVG Tags...')
        f = open(os.path.join(self.location, filename), 'r', encoding='utf-8')
        splitter = "."
        name = filename.split(splitter)[0]
        INPUT = f.read()
        if "cover" in filename or "tp" in filename:
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
        """
        работа с маркированными списками
        1) убираются картинки в маркированных списках(для того, чтобы собственные маркеры
        не выравнивались по центру вместо левого края
        2)удаление парного открывающегося/закрывающегося тега <ul></ul> для корректности
        отображения списков

        @param filename: имя входного файла html
        @type filename: string
        """
        print('\t\t--- Replasing Markers...')
        f = open(os.path.join(self.location, filename), mode='r', encoding='utf-8')
        pattern = r'<p class="list\w+?">\n*\s*?<img.+?\/>(.+?)<\/p>'
        pattern_full_message = r'(<p class="list\w+?">\n*\s*?<img.+?\/>.+?<\/p>)'
        INPUT = f.read()
        # print(INPUT)
        full_messages = re.findall(pattern_full_message, INPUT, re.S)  # строки целиком вместе с тегами
        strings = re.findall(pattern, INPUT, re.S)  # только текст
        if len(full_messages) == 0 or len(strings) == 0:
            pattern = r'<p class="list\w*">\n*?\s*?<img.+?<\/img>(.+?)<\/p>'
            pattern_full_message = r'(<p class="list\w*">\n*?\s*?<img.+?<\/img>.+?<\/p>)'
            full_messages = re.findall(pattern_full_message, INPUT, re.S)  # строки целиком вместе с тегами
            strings = re.findall(pattern, INPUT, re.S)  # только текст
        i = 0
        correctStrings = []  # исправленные строки с тегами
        for text in strings:
            correctStrings.append('<ul><li>{!s}</li></ul>'.format(text))
            INPUT = INPUT.replace(full_messages[i], correctStrings[i])
            i += 1
            # print(INPUT)
        pattern = r'(<p class="number\w*?">\n*?\s*?<img .+?\/>\n*?(.+?)<\/p>)'
        markers = re.findall(pattern, INPUT, re.S)
        for marker in markers:
            INPUT = INPUT.replace(marker[0], "<ul><li>" + marker[1] + "</li></ul>")

        pattern = r'(<p class="list\w*?">\n*?\s*?<img .+?\/>\n*?(.+?)<\/p>)'
        markers = re.findall(pattern, INPUT, re.S)
        for marker in markers:
            INPUT = INPUT.replace(marker[0], "<ul><li>" + marker[1] + "</li></ul>")

        pattern = r'(<p class="indent\w*?">\n*?\s*?<img .+?\/>\n*?(.+?)<\/p>)'
        markers = re.findall(pattern, INPUT, re.S)
        for marker in markers:
            INPUT = INPUT.replace(marker[0], "<ul><li>" + marker[1] + "</li></ul>")

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

        pattern = r'<p class="bullet\w*".+?(<img.+?\/>).+?<\/p>'
        images = re.findall(pattern, INPUT, re.S)
        for image in images:
            INPUT = INPUT.replace(image, "")
        INPUT = INPUT.replace("○", "")
        f.close()
        f = open(os.path.join(self.location, filename), 'w', encoding='utf-8')
        f.write(INPUT)
        f.close()

    def replace_headers(self, filename):
        """
        1)метод заменяет заголовки h5, h4, h3 на h2 и при тегах h1, h2, h3 добавляет к ним
        <div class="chapter_header"> [текст] </div> для оформления в читалке
        2)заменяет тег цитат на right, убирает точки в маркированных списках
        3)ставит пробел до и после тире
        4)убирает теги, отсутствующие в нашей читалке(для увеличения размера текста)
        5)удаляет проблемы с названиями глав, когда первая буква написана большим шрифтом, чем остальные,
        и при этом после первой установлен пробел
        6)удаляет тег strong

        @param filename: имя входного файла html
        @type filename: string
        """
        splitter = "."
        format = filename.split(splitter)
        format = format[1]
        print('\t\t--- Replasing headers...')
        if not "ncx" in filename and not "opf" in filename:
            f = open(os.path.join(self.location, filename), 'r', encoding='utf-8')
            INPUT = f.read()
            soup = BeautifulSoup(INPUT)
            INPUT = soup.prettify()
            INPUT = INPUT.replace("h5", "h4")
            INPUT = INPUT.replace("h4", "h3")
            INPUT = INPUT.replace("h3", "h2")

            pattern = r'<h(.) class="h..*?".+?\/h.>'
            pattern_full_message = r'(<h. class="h..*?".+?\/h.>)'
            strings = re.findall(pattern, INPUT, re.S)  # только текст
            full_message = re.findall(pattern_full_message, INPUT, re.S)
            i = 0
            done_array = []
            for text in full_message:
                if not text in done_array:
                    done_array.append(text)
                    if int(strings[i]) == 2 or int(strings[i]) == 1 or int(strings[i]) == 3:
                        new_message = '<div class="chapter_header">{!s}</div>'.format(text)
                        INPUT = INPUT.replace(text, new_message)
                i += 1
            print('\t\t--- Correcting quotes...')
            INPUT = INPUT.replace("chap-bq", "right")
            INPUT = INPUT.replace("&#8212;", " &#8212 ")
            INPUT = INPUT.replace("•", "")
            INPUT = INPUT.replace("—", " — ")

            # иногда заворачивают текст в три тега:
            pattern = r'(<div class="(?:tx|tx1|fmhT|fmtx|atx1|aptx1|fmtx1|epiv|eps|ctag1|pepiv|peps|ct|cepiv|ceps|fmtx1d|bmtx|bmtx1|bmhT|ctl|apshT|aptx|aptx1|cst|ctBT-T|chaboxg|crt|fmshT)">(<div class="(?:tx|tx1|fmhT|fmtx|atx1|fmtx1|epiv|eps|ctag1|pepiv|peps|ct|cepiv|ceps|fmtx1d|bmtx|bmtx1|bmhT|ctl|apshT|aptx|cst|ctBT-T|chaboxg|crt|fmshT)">)*(.+?)<\/div>.*?(<\/div>)*)'
            divs = re.findall(pattern, INPUT, re.S)
            for div in divs:
                new_line = "<p>" + div[2] + "</p>"
                INPUT = INPUT.replace(div[0], new_line)
            divs = re.findall(pattern, INPUT, re.S)
            for div in divs:
                new_line = "<p>" + div[2] + "</p>"
                INPUT = INPUT.replace(div[0], new_line)
            divs = re.findall(pattern, INPUT, re.S)
            for div in divs:
                new_line = "<p>" + div[2] + "</p>"
                INPUT = INPUT.replace(div[0], new_line)

            pattern = r'(<p class="(?:tx|tx1|fmhT|fmtx|atx1|fmtx1|epiv|eps|ctag1|pepiv|peps|ct|cepiv|ceps|fmtx1d|bmtx|bmtx1|bmhT|ctl|apshT|aptx|aptx1|cst|ctBT-T|chaboxg|crt|fmshT)" .+?>(.+?)<\/p>)'
            lines = re.findall(pattern, INPUT, re.S)
            for line in lines:
                old = line[0]
                new = "<p>" + line[1] + "</p>"
                INPUT = INPUT.replace(old, new)

            # удаление "С качущих" букв в оглавлении
            pattern = r'(([a-zA-Z]).{1,6}<small>.{1,3}\s+(.+?)\n.+?<\/small>)'
            bad_paragrafs = re.findall(pattern, INPUT, re.S)
            for par in bad_paragrafs:
                INPUT = INPUT.replace(par[0], par[1] + par[2])

            # удаление тега strong
            pattern = r'(<strong>(.+?)<\/strong>)'
            strong_pars = re.findall(pattern, INPUT, re.S)
            for par in strong_pars:
                INPUT = INPUT.replace(par[0], par[1])

            f.close()
            f = open(os.path.join(self.location, filename), 'w', encoding='utf-8')
            f.write(INPUT)
            f.close()


    def zip(self, res, dst):
        """
        создаёт zip архив

        @param res: путь до архива (с расширением)
        @type res: string

        @param dst: выходной путь (папка)
        @type dst: string
        """
        zf = zipfile.ZipFile("%s" % (dst), "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(res)
        for dirname, subdirs, files in os.walk(res):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                #print('zipping %s as %s' % (os.path.join(dirname, filename), arcname))
                zf.write(absname, arcname)
        zf.close()
