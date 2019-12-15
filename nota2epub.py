#!/usr/bin/env python3

import requests
from lxml import html, etree
from ebooklib import epub

def create_ebook(chapters, author = "Author Authorowski", book_id = "unknown_id", title = "Title unknown"):
    book = epub.EpubBook()
    book.set_identifier(book_id)
    book.set_title(title)
    book.set_language("ru")
    book.add_author(author)

    spine = []
    for chapter in chapters:
        file_name = "chapter_{}.xhtml".format(chapter["id"])
        c = epub.EpubHtml(title=chapter["title"], file_name=file_name, lang="ru")
        c.content = chapter["content"]
        book.add_item(c)
        spine.append(c)
        # toc.append(c)

    book.toc = (epub.Link('intro.xhtml', 'Introduction', 'intro'),
                    (
                        epub.Section('Chapters'),
                        spine,
                    )
                )
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub('test.epub', book, {})

    return

def abc():
    url = "https://opennota2.duckdns.org/book/72467"
    request = requests.get(url)

    if request.status_code == 200:
        # print(request.text)
        data = html.fromstring(request.text)
        title = data.xpath('/html/head/title')[0].text_content()
        print(title)
        # info = data.xpath('//*[@id="Info"]')[0]
        chapters = []
        # print(dir(chapters[0]))
        for tr in data.xpath('//table[@id="Chapters"]/tbody/tr'):
            chapter = dict()
            chapter["id"] = tr.attrib["data-id"]
            chapter["title"] = tr[0].text_content()
            print(chapter["id"], chapter["title"])

            # https://opennota2.duckdns.org/book/72467/397201/download?format=h&enc=UTF-8
            chapter_url = "{}/{}/download?format=h&enc=UTF-8".format(url, chapter["id"])
            chapter_req = requests.get(chapter_url)
            if chapter_req.status_code == 200:
                print('OK', chapter_url)
                chapter["content"] = chapter_req.text
                chapters.append(chapter)
            else:
                print('Bad', chapter_req.status_code, chapter_url)

        author = title.split('-')[0]
        book_id = url.split('/')[-1]
        # print(chapters, author, book_id, title)
        create_ebook(chapters, author, book_id, title)

if __name__ == "__main__":
    abc()
