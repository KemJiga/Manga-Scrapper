import shutil
from bs4 import BeautifulSoup
import requests
import json
import os
import re

def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        time_taken = end - start
        print(f'Time taken: {time_taken:.1f} seconds')
        return result
    return wrapper

def clean_manga_name(folder_name):
    pattern = r'[<>:"/\\|?*\x00-\x1F]'
    return re.sub(pattern, '', folder_name)

@timer
def scrap(website):
    response = requests.get(website)
    content = response.text
    soup = BeautifulSoup(content, 'lxml')

    manga_name = soup.find('div', class_='story-info-right').h1.text
    manga_name = clean_manga_name(manga_name)

    chapter_list = soup.find('ul', class_='row-content-chapter')
    chapter_list = chapter_list.find_all('li')

    chapters = {}
    print(f'Scraping {manga_name}...')
    for chapter in chapter_list:
        chapter_name = chapter.a['title']
        chapter_link = chapter.a['href']

        # result = requests.get(chapter_link)
        # chapter_content = result.text

        # chapter_soup = BeautifulSoup(chapter_content, 'lxml')
        
        # img_container = chapter_soup.find('div', class_='container-chapter-reader')
        # img_list = img_container.find_all('img')


        # img_srcs = list(map(lambda img: img['src'], img_list))

        chapters[chapter_name] = chapter_link
    
    export_chapters(manga_name, chapters)
    return chapters

def export_chapters(manga_name, chapters):
    parent_directory = 'Downloads'
    output_folder = os.path.join(parent_directory, manga_name)
    
    # Create the directory
    os.makedirs(output_folder, exist_ok=True)

    chapter_img_list = os.path.join(output_folder, f'{manga_name}.json')
    with open(chapter_img_list, 'w') as file:
        json.dump(chapters, file, indent=4)

@timer
def download_chapter(chapter_link:str, chapter_name:int, output_folder:str):
    chapter_folder = os.path.join(output_folder, chapter_name)
    os.makedirs(chapter_folder, exist_ok=True)

    headers = {
            'referer': 'Referer: https://chapmanganato.to/'
            }
        
    print(f'Downloading {chapter_name}...')

    load_chapter = requests.get(chapter_link)
    chapter_content = load_chapter.text
    soup = BeautifulSoup(chapter_content, 'lxml')

    img_list = soup.find('div', class_='container-chapter-reader').find_all('img')
    img_srcs = list(map(lambda img: img['src'], img_list))

    for i, img_src in enumerate(img_srcs):
        img_response = requests.get(img_src, headers=headers)
        img_content = img_response.content

        img_name = f'{i+1}.jpg'
        img_path = os.path.join(chapter_folder, img_name)

        with open(img_path, 'wb') as file:
            file.write(img_content)

def search_yellow_pages(manga_name:str):
    manga_directory = os.path.join('Downloads', 'manga_yellow_pages.json')

    if os.path.exists(manga_directory):
        with open(manga_directory, 'r+') as file:
            try:
                mangas = json.load(file)
            except json.JSONDecodeError:
                mangas = {}
            if manga_name in mangas:
                print('Manga found in yellow pages')
                return True
            return False
    else:
        with open(manga_directory, 'w') as file:
            json.dump({}, file, indent=4)
        search_yellow_pages(manga_name)
    return False

def from_yellow_pages(manga_name:str):
    manga_directory = os.path.join('Downloads', 'manga_yellow_pages.json')

    if os.path.exists(manga_directory):
        with open(manga_directory, 'r') as file:
            mangas = json.load(file)
            if manga_name in mangas:
                print(f'returning {mangas[manga_name]} from yellow pages')
                return mangas[manga_name]
            return {'code': 404, 'message': 'Manga not found'}
    return {'code': 404, 'message': 'Manga not found'}

def add_yellow_pages(manga_name:str, manga_info:dict):
    manga_directory = os.path.join('Downloads', 'manga_yellow_pages.json')

    if os.path.exists(manga_directory):
        with open(manga_directory, 'r') as file:
            mangas = json.load(file)
            mangas[manga_name] = manga_info
        with open(manga_directory, 'w') as file:
            json.dump(mangas, file, indent=4)

@timer
def search_by_name(manga_name:str):
    if search_yellow_pages(manga_name):
        return from_yellow_pages(manga_name)

    clean_name = manga_name.replace(' ', '_')
    website = f'https://manganato.com/search/story/{clean_name}'

    response = requests.get(website)
    content = response.text
    soup = BeautifulSoup(content, 'lxml')

    results = soup.find('div', class_='panel-search-story')

    if not results:
        print('nothing found...')
        return {'code': 404, 'message': 'Manga not found'}
    print('something found...')

    manga_list = results.find_all('div', class_='search-story-item', limit=3)

    mangas = {}
    
    for manga in manga_list:
        left = manga.find('a', class_='item-img bookmark_check')
        src = left['href']
        title = left['title']
        img = left.img['src']
        m = {
            'src': src,
            'img': img
        }
        mangas[title] = m
    
    add_yellow_pages(manga_name, mangas)
    return {'code': 200, 'mangas': mangas}

def main():
    # result = search_by_name('kijima-san to yamada-san')
    # mangas = result['mangas']

    # manga_titles = list(mangas.keys())
    # first_manga_title = manga_titles[0]
    # first_manga_src = mangas[first_manga_title]['src']

    # scrap(first_manga_src)
    output_folder = os.path.join('Downloads', 'Kijima-San To Yamada-San')
    download_chapter("https://chapmanganato.to/manga-ix985680/chapter-1", 'Chapter 1', output_folder)

if __name__ == '__main__':
    main()