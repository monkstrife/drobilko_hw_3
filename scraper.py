import json
import re
import time
from pathlib import Path

import requests
import schedule
from bs4 import BeautifulSoup


CATALOGUE_URL = 'https://books.toscrape.com/catalogue/'
RATINGS = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}


def get_book_data(book_url: str, session=None) -> dict:
    """Собирает информацию со страницы книги.
    
    Сигнатура: get_book_data(book_url: str, session=None) -> dict,
    где аргументы: book_url - url страницы книги,
    session - сессия;
    а возвращаемое значение - словарь dict: название, цена в фунтах, рейтинг от 1 до 5, остаток,
    описание и все поля таблицы Product Information
            
    """
    client = requests if session is None else session
    response = client.get(book_url, timeout=15)
    response.raise_for_status()
    page = BeautifulSoup(response.content, 'html.parser')

    title = page.find('h1').get_text(strip=True)
    price_text = page.find('p', class_='price_color').get_text(strip=True)
    rating_tag = page.find('p', class_='star-rating')
    stock_text = page.find('p', class_='availability').get_text(strip=True)
    stock_match = re.search(r'(\d+) available', stock_text)
    description_tags = page.select('#product_description + p')
    description = ''
    if description_tags:
        description = description_tags[0].get_text(strip=True)

    product_info = {}
    for row in page.select('table.table-striped tr'):
        key = row.find('th').get_text(strip=True)
        product_info[key] = row.find('td').get_text(strip=True)

    return {
        'title': title,
        'price': float(price_text.replace('£', '')),
        'rating': RATINGS[rating_tag['class'][1]],
        'stock': int(stock_match.group(1)) if stock_match else 0,
        'description': description,
        'product_info': product_info,
    }


def scrape_books(is_save: bool = False, output_dir='.') -> list:
    """Собирает информацию обо всех книгах со всех страниц каталога.
        
    Сигнатура: scrape_books(is_save: bool = False, output_dir='.') -> list,
    где is_save - флаг сохранения результата в файл books_data.txt,
    output_dir - папка для сохранения файла (по умолчанию текущая папка).
    Возвращаемое значение - список словарей с данными о книгах
    в порядке их появления в каталоге.
    
    """
    books = []
    page_url = CATALOGUE_URL + 'page-1.html'

    with requests.Session() as session:
        while True:
            response = session.get(page_url, timeout=15)
            response.raise_for_status()
            page = BeautifulSoup(response.content, 'html.parser')

            for link in page.select('article.product_pod h3 a'):
                book_url = CATALOGUE_URL + link['href']
                books.append(get_book_data(book_url, session))

            next_links = page.select('li.next a')
            if not next_links:
                break
            page_url = CATALOGUE_URL + next_links[0]['href']

    if is_save:
        file_path = Path(output_dir) / 'books_data.txt'
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(books, file, ensure_ascii=False, indent=2)

    return books


def run_scheduler(output_dir, run_at: str = '19:00') -> None:
    """Запустить ежедневную выгрузку до прерывания.
    
    сигнатура: run_scheduler(output_dir, run_at: str = '19:00') -> None
    output_dir (str или Path) — папка для файла books_data.txt.
    run_at (str) — местное время запуска в формате ЧЧ:ММ.
    
    """
    scheduler = schedule.Scheduler()
    scheduler.every().day.at(run_at).do(
        scrape_books, is_save=True, output_dir=output_dir
    )
    print(f'Ежедневная выгрузка в {run_at} по местному времени.')

    try:
        while True:
            scheduler.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print('Планировщик остановлен.')


if __name__ == '__main__':
    artifacts_dir = Path(__file__).resolve().parent / 'artifacts'
    run_scheduler(artifacts_dir)
