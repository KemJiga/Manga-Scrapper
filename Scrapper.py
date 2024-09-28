import shutil
import time
from bs4 import BeautifulSoup
import requests
import json
import os
import re
from utils import reverse_order_dict

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

def clean_manga_name(folder_name:str):
    pattern = r'[<>:"/\\|?*\x00-\x1F]'
    return re.sub(pattern, '', folder_name)

@timer
async def scrape(website:str):
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
        chapters[chapter_name] = chapter_link

    reverse_chapters = reverse_order_dict(chapters)

    description = soup.find('div', class_='panel-story-info-description').text.split('Description :')[1].strip()
    img = soup.find('img', attrs={'class': 'img-loading', 'alt': manga_name})['src']
    genres = list(map(lambda genre: genre.text, soup.find('table', class_='variations-tableInfo').find_all('a')))
    author = genres.pop(0)

    manga_info = {
        'author': author,
        'name': manga_name,
        'genres': genres,
        'description': description,
        'src': website,
        'img': img,
        'chapters': reverse_chapters
    }
    
    update_visited_manga(manga_name, manga_info)
    export_chapters(manga_name, reverse_chapters)
    return reverse_chapters

def export_chapters(manga_name:str, chapters):
    parent_directory = 'Downloads'
    output_folder = os.path.join(parent_directory, manga_name)
    
    # Create the directory
    os.makedirs(output_folder, exist_ok=True)

    chapter_img_list = os.path.join(output_folder, f'{manga_name}.json')
    with open(chapter_img_list, 'w') as file:
        json.dump(chapters, file, indent=4)

@timer
async def download_chapter(chapter_link:str, chapter_name:int, output_folder:str):
    chapter_folder = os.path.join(output_folder, chapter_name)
    os.makedirs(chapter_folder, exist_ok=True)

    headers = {
            'referer': 'Referer: https://chapmanganato.to/'
            }
        
    print(f'Downloading {chapter_name}...')

    try:
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
        return {'code': 200, 'message': 'Chapter downloaded successfully', 'folder': chapter_folder}
    except Exception as e:
        print(f'Error: {e}')
        shutil.rmtree(chapter_folder)
        return {'code': 500, 'message': str(e)}

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
        os.makedirs('Downloads', exist_ok=True)
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
                return {'code': 200, 'mangas': mangas[manga_name]}
            return {'code': 404, 'message': 'Manga not in yellow pages'}
    return {'code': 404, 'message': 'Manga not in yellow pages'}

def add_yellow_pages(manga_name:str, manga_info:dict):
    manga_directory = os.path.join('Downloads', 'manga_yellow_pages.json')

    if os.path.exists(manga_directory):
        with open(manga_directory, 'r') as file:
            mangas = json.load(file)
            mangas[manga_name] = manga_info
        with open(manga_directory, 'w') as file:
            json.dump(mangas, file, indent=4)

@timer
async def search_by_name(manga_name:str):
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

    mangas = []
    
    for manga in manga_list:
        try:
            left = manga.find('a', class_='item-img bookmark_check')
            src = left['href']
            title = left['title']
            img = left.img['src']
            authors = manga.find('span', class_='text-nowrap item-author').text.split(',')
            updatedAt = manga.find('span', class_='text-nowrap item-time').text

            response = requests.get(src)
            content = response.text
            soup = BeautifulSoup(content, 'lxml')

            description = soup.find('div', class_='panel-story-info-description').text.split('Description :')[1].strip()
            chapter_list = soup.find('ul', class_='row-content-chapter')
            chapter_list = chapter_list.find_all('li')

            chapters = {}
            print(f'Scraping {manga_name}...')
            for chapter in chapter_list:
                chapter_name = chapter.a['title']
                chapter_link = chapter.a['href']
                chapters[chapter_name] = chapter_link

            reverse_chapters = reverse_order_dict(chapters)
            genres = list(map(lambda genre: genre.text, soup.find('table', class_='variations-tableInfo').find_all('a')))
            for i in range(len(authors)):
                genres.pop(0)
            

            m = {
                'title': title,
                'author': authors,
                'genres': genres,
                'description': description,
                'src': src,
                'img': img,
                'chapters': reverse_chapters,
                'updatedAt': updatedAt,
            }
            #print(m)
            mangas.append(m)
        except Exception as e:
            print(f'Error: {e}')
            continue
    
    add_yellow_pages(manga_name, mangas)
    return {'code': 200, 'mangas': mangas}

@timer
def update_visited_manga(manga_name:str, manga_info:dict):
    visited_directory = os.path.join('Downloads', 'visited_manga.json')

    if os.path.exists(visited_directory):
        with open(visited_directory, 'r') as file:
            visited_manga = json.load(file)
            visited_manga[manga_name] = manga_info
        with open(visited_directory, 'w') as file:
            json.dump(visited_manga, file, indent=4)
    else:
        os.makedirs('Downloads', exist_ok=True)
        with open(visited_directory, 'w') as file:
            json.dump({manga_name: manga_info}, file, indent=4)

async def main():
    # result = await search_by_name('one piece')
    # mangas = result['mangas']

    # manga_titles = list(mangas.keys())
    # first_manga_title = manga_titles[0]
    # first_manga_src = mangas[first_manga_title]['src']

    await scrape('https://manganato.com/manga-tn996848')

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())