import dataclasses
from datetime import date
from pathlib import Path
from typing import Generator

from bs4 import BeautifulSoup, Tag

import requests
import csv

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclasses.dataclass
class Author:
    name: str | None
    born_date: str | None
    born_location: str | None
    description: str | None


@dataclasses.dataclass
class Quote:
    text: str
    author: str
    tags: list[str]
    born_date: date | None = None
    born_location: str | None = None
    description: str | None = None


authors_cache = {}


def parse_author(author_page_soup: Tag) -> Author:
    author_name = author_page_soup.select_one(".author-title").text
    author_born_date = author_page_soup.select_one(".author-born-date").text
    author_born_location = author_page_soup.select_one(
        ".author-born-location"
    ).text.replace("in", "", 1)
    author_description = author_page_soup.select_one(
        ".author-description"
    ).text.lstrip()[:30]

    return Author(
        name=author_name,
        born_date=author_born_date,
        born_location=author_born_location,
        description=author_description,
    )


def parse_single_quote(quote: Tag) -> Quote:
    quote_text = quote.select_one(".text").text
    quote_author = quote.select_one(".author").text
    quote_tags = [tag.text for tag in quote.select(".tags a")]

    author_info = authors_cache.get(quote_author)
    if author_info:
        return Quote(
            text=quote_text,
            author=quote_author,
            tags=quote_tags,
            born_date=author_info.born_date,
            born_location=author_info.born_location,
            description=author_info.description,
        )
    author_info = Author(
        name=None, born_date=None, born_location=None, description=None
    )
    author_url = quote.select_one('a[href*="/author/"]')
    if author_url:
        author_url = f"https://quotes.toscrape.com{author_url['href']}" # noqa
        response = requests.get(author_url)
        if response.status_code == 200:
            author_soup = BeautifulSoup(response.content, "html.parser")
            author_info = parse_author(author_page_soup=author_soup)
    authors_cache[quote_author] = author_info
    return Quote(
        text=quote_text,
        author=quote_author,
        tags=quote_tags,
        born_date=author_info.born_date,
        born_location=author_info.born_location,
        description=author_info.description,
    )


def get_page_quotes(page_soup: Tag) -> list[Quote]:
    quotes = page_soup.select(".quote")
    return [parse_single_quote(quote) for quote in quotes]


def page_generator() -> Generator[BeautifulSoup, None, None]:
    next_page = 1
    with requests.Session() as session:
        while True:
            request_url = f"https://quotes.toscrape.com/page/{next_page}/" # noqa
            response = session.get(url=request_url)
            soup = BeautifulSoup(response.content, "html.parser")
            if not soup.select(".quote"):
                return
            yield soup
            next_page += 1


def get_quotes() -> list[Quote]:
    quotes = list()
    for page_soup in page_generator():
        quotes.extend(get_page_quotes(page_soup))
    return quotes


def write_quotes_to_file(output_csv_path: str, quotes: list[Quote]) -> None:
    with open(output_csv_path, "w") as file_out:
        writer = csv.writer(file_out)
        writer.writerow([field.name for field in dataclasses.fields(Quote)])
        writer.writerows([dataclasses.astuple(quote) for quote in quotes])


def main(output_csv_path: str) -> None:
    quotes = get_quotes()
    write_quotes_to_file(output_csv_path, quotes)


if __name__ == "__main__":
    main(BASE_DIR / "result.csv")
