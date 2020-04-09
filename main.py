import argparse
from concurrent.futures import ThreadPoolExecutor
import os
import requests
import pathlib
import time
import urllib

import pandas as pd
#from tqdm import tqdm


def parse_book_url(url, title, author, format_="pdf"):
    """
    Given the original book URL, get the download URL and human-friendly
    local filename for the given format ('pdf' or 'epub').

    This function produces a URL but does not check that it is valid.
    """

    format_ = format_.lower()

    # Replace percent-encoding with UTF-8 characters, replace "/book/..." URL
    # path prefix with "/content/pdf/..." (or "/content/epub/...", etc. based
    # on `format_`), and add format extension.
    download_url = urllib.parse.unquote(url)
    if format_ == "pdf":
        download_url = download_url.replace("book", "content/" + format_)
    elif format_ == "epub":
        download_url = download_url.replace("book", "download/" + format_)
    else:
        raise ValueError("Unsupported format: {}".format(format_))
    download_url += "." + format_

    original_fname = os.path.split(download_url)[1]

    # Replace desired characters for human-friendly local filename.
    char_replacements = {
        "/": "_",
    }

    new_fname = [
        title.translate(str.maketrans(char_replacements)),
        author.translate(str.maketrans(char_replacements)),
        original_fname
    ]
    new_fname = " - ".join(new_fname)

    return download_url, new_fname


def book_info_from_table(book_table):
    """
    Yield relevant book info for each book in the table.
    """

    # Package name is essentially category/discipline.
    columns = [
        "Book Title", "Author", "English Package Name", "OpenURL"
    ]

    for title, author, pkg, url in book_table[columns].values:
        yield {
            "title": title,
            "author": author,
            "pkg": pkg.replace(" ", "_").replace(",", ""),
            "url": url
        }


def download_book(book, dst_dir=".", get_epub=False):
    book_dir = dst_dir / book["pkg"]
    book_dir.mkdir(exist_ok=True)

    success = {
        "pdf": None,
        "epub": None
    }

    request = requests.get(book["url"])

    pdf_download_url, pdf_fname = parse_book_url(
        request.url, book["title"], book["author"], "pdf"
    )
    pdf_fpath = book_dir / pdf_fname

    if pdf_fpath.exists():
        success["pdf"] = "exists"
    else:
        success["pdf"] = False
        pdf_request = requests.get(pdf_download_url, allow_redirects=True)
        if pdf_request.status_code == 200:
            with open(str(pdf_fpath), "wb") as f:
                ret = f.write(pdf_request.content)
                success["pdf"] = ret > 0

    if get_epub:
        epub_download_url, epub_fname = parse_book_url(
            request.url, book["title"], book["author"], "epub"
        )
        epub_fpath = book_dir / epub_fname

        if epub_fpath.exists():
            success["epub"] = "exists"
        else:
            success["epub"] = False
            epub_request = requests.get(epub_download_url, allow_redirects=True)
            if epub_request.status_code == 200:
                with open(str(epub_fpath), "wb") as f:
                    ret = f.write(epub_request.content)
                    success["epub"] = ret > 0
    book["success"] = success
    return True


def download_books(dst_dir, book_table, get_epub=False, max_workers=8):
    books = list(book_info_from_table(book_table))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(download_book, book, dst_dir=dst_dir, get_epub=get_epub)
            for book in books
        ]
    return books


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dst_dir", type=pathlib.Path, default="download",
        help="Destination directory"
    )
    parser.add_argument("--epub", action="store_true", help="Grab epubs")
    parser.add_argument("-w", "--max-workers", type=int, default=8)
    args = vars(parser.parse_args())

    book_table_url = "".join(
        [
            "https://resource-cms.springernature.com/",
            "springer-cms/rest/v1/content/17858272/data/v4"
        ]
    )

    dst_dir = args["dst_dir"].expanduser().absolute()
    dst_dir.mkdir(exist_ok=True)

    table_path = dst_dir / "table.xlsx"

    if not table_path.exists():
        book_table = pd.read_excel(book_table_url)
        book_table.to_excel(str(table_path))
    else:
        book_table = pd.read_excel(str(table_path))

    start_time = time.time()
    res = download_books(
        dst_dir, book_table, get_epub=args["epub"],
        max_workers=args["max_workers"]
    )
    elapsed = time.time() - start_time
    print(elapsed)
