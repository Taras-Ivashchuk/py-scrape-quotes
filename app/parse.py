import dataclasses
from pathlib import Path
from typing import Generator

from bs4 import BeautifulSoup, Tag

import requests
import csv

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclasses.dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


def parse_single_quote(quote: Tag) -> Quote:
    return Quote(
        text=quote.select_one(".text").text,
        author=quote.select_one(".author").text,
        tags=[tag.text for tag in quote.select(".tags a")]
    )


def get_page_quotes(page_soup: Tag) -> list[Quote]:
    quotes = page_soup.select(".quote")
    return [
        parse_single_quote(quote)
        for quote in quotes
    ]


def page_generator() -> Generator[BeautifulSoup, None, None]:
    next_page = 1
    with requests.Session() as session:
        while True:
            request_url = f"https: //quotes.toscrape.com/page/{next_page}/"
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
