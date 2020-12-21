#!/usr/bin/env python3

import argparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from lxml import html, etree
from ebooklib import epub

DEFAULT_TIMEOUT = 5 # seconds

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)

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

def download(url):
    # url = "https://opennota2.duckdns.org/book/80558"
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

            http = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
            http.mount("https://", TimeoutHTTPAdapter(max_retries=retries))

            # https://opennota2.duckdns.org/book/72467/397201/download?format=h&enc=UTF-8
            chapter_url = "{}/{}/download?format=h&enc=UTF-8".format(url, chapter["id"])
            chapter_req = http.get(chapter_url)
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
    parser = argparse.ArgumentParser(description='Process some things.')
    parser.add_argument('--url', dest="url", type=str,
                        help='opennota or notabenoid url')

    args = parser.parse_args()
    download(args.url)