import argparse
import os
import requests
import pandas as pd
import pathlib
import pdb
from tqdm import tqdm
import urllib


def parse_book_url(url, title, author, format_='pdf'):
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
        download_url = download_url.replace('book', 'content/' + format_)
    elif format_ == "epub":
        download_url = download_url.replace('book', 'download/' + format_)
    else:
        raise ValueError("Unsupported format: {}".format(format_))
    download_url += '.' + format_

    original_fname = os.path.split(download_url)[1]

    # Replace desired characters for human-friendly local filename.
    char_replacements = {
        ',': '-',
        '.': '',
        '/': ' ',
    }

    new_fname = [
        title.translate(str.maketrans(char_replacements)),
        author.translate(str.maketrans(char_replacements)),
        original_fname
    ]
    new_fname = ' - '.join(new_fname)

    return download_url, new_fname


def get_books(book_table):
    """
    Yield relevant book info for each book in the table.
    """

    # Package name is essentially category/discipline.
    columns = [
        "Book Title", "Author", "English Package Name", "OpenURL"
    ]

    for title, author, pkg, url in book_table[columns].values():
        yield {
            "title": title,
            "author": author,
            "pkg": pkg,
            "url": url
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dst_dir", type=pathlib.Path, default="download",
        help="Destination directory"
    )
    parser.add_argument("--epub", action="store_true", help="Grab epubs")
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
    book_table = pd.read_excel(book_table_url)

    # Save table.
    book_table.to_excel(str(table_path))


if __name__ == "false":
        new_folder = os.path.join(folder, pk_name)

        if not os.path.exists(new_folder):
            os.mkdir(new_folder)

        r = requests.get(url)

        # Download pdf version.
        pdf_download_url, pdf_fname = parse_book_url(r.url, title, author, 'pdf')
        pdf_fpath = os.path.join(new_folder, pdf_fname)

        pdf_request = requests.get(pdf_download_url, allow_redirects=True)
        with open(pdf_fpath, 'wb') as f:
            f.write(pdf_request.content)

        #download epub version too if exists
        epub_download_url, epub_fname = parse_book_url(r.url, title, author, 'epub')
        epub_fpath = os.path.join(new_folder, epub_fname)

        epub_request = requests.get(epub_download_url, allow_redirects=True)
        if epub_request.status_code == 200:
            with open(epub_fpath, 'wb') as f:
                f.write(epub_request.content)
