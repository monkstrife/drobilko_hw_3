import json
import sys
from pathlib import Path

import pytest


project_dir = str(Path(__file__).resolve().parent.parent)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Путь добавляется до импорта модуля из соседней папки.
from scraper import CATALOGUE_URL, get_book_data, scrape_books  # noqa: E402


@pytest.fixture(scope='module')
def first_book():
    """Возвращает данные первой книги каталога."""
    url = CATALOGUE_URL + 'a-light-in-the-attic_1000/index.html'
    return get_book_data(url)


def test_book_fields(first_book):
    """Проверяет состав словаря и полей из таблицы."""
    assert isinstance(first_book, dict)
    assert set(first_book) == {
        'title', 'price', 'rating', 'stock', 'description', 'product_info'
    }
    assert set(first_book['product_info']) == {
        'UPC', 'Product Type', 'Price (excl. tax)', 'Price (incl. tax)',
        'Tax', 'Availability', 'Number of reviews'
    }


def test_first_book_values(first_book):
    """Сверяет значения полей с карточкой A Light in the Attic."""
    assert first_book['title'] == 'A Light in the Attic'
    assert first_book['price'] == 51.77
    assert first_book['rating'] == 3
    assert first_book['stock'] == 22
    assert first_book['description']
    assert first_book['product_info']['UPC'] == 'a897fe39b1053632'


def test_scrape_books(tmp_path):
    """Проверяет полноту выгрузки и содержимое сохранённого файла."""
    books = scrape_books(is_save=True, output_dir=tmp_path)
    assert len(books) == 1000
    assert len({book['product_info']['UPC'] for book in books}) == 1000

    file_path = tmp_path / 'books_data.txt'
    with open(file_path, encoding='utf-8') as file:
        assert json.load(file) == books
