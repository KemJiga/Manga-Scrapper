import shutil
from bs4 import BeautifulSoup
import requests
import json
import os
import re
import argparse

def time_wrapper(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        time_taken = end - start
        print(f'Time taken: {time_taken:.1f} seconds')
        return result
    return wrapper

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def clean_manga_name(folder_name):
    pattern = r'[<>:"/\\|?*\x00-\x1F]'
    return re.sub(pattern, '', folder_name)

@time_wrapper
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
        chapter_link = chapter.a['href']
        chapter_name = chapter.a['title']

        result = requests.get(chapter_link)
        chapter_content = result.text

        chapter_soup = BeautifulSoup(chapter_content, 'lxml')
        
        img_container = chapter_soup.find('div', class_='container-chapter-reader')
        img_list = img_container.find_all('img')

        img_srcs = []
        for img in img_list:
            img_link = img['src']
            img_srcs.append(img_link)

        chapters[chapter_name] = img_srcs

    export_json(manga_name, chapters)
    return manga_name, chapters

def export_json(manga_name, chapters):
    parent_directory = 'Downloads'
    output_folder = os.path.join(parent_directory, manga_name)
    
    #TODO: Implement a better way to handle this
    # Remove the directory if it exists
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    
    # Create the directory
    os.makedirs(output_folder, exist_ok=True)

    chapter_img_list = os.path.join(output_folder, 'Chapters.json')
    with open(chapter_img_list, 'w') as file:
        json.dump(chapters, file, indent=4)

@time_wrapper
def download_all_chapters(manga_name, chapters):
    parent_directory = 'Downloads'
    output_folder = os.path.join(parent_directory, manga_name)
    chapter_len = len(chapters)
    downloading_chapter = 0

    print(f'\nDownloading all {chapter_len} chapters of {manga_name}...')
    printProgressBar(downloading_chapter, chapter_len, prefix = 'Progress:', suffix = 'Complete', length = 50)
    for _, img_srcs in chapters.items():
        chapter_name = f'Chapter {chapter_len - downloading_chapter}'
        downloading_chapter += 1
        chapter_folder = os.path.join(output_folder, chapter_name)
        os.makedirs(chapter_folder, exist_ok=True)

        headers = {
            'referer': 'Referer: https://chapmanganato.to/'
            }

        for i, img_src in enumerate(img_srcs):
            img_response = requests.get(img_src, headers=headers)
            img_content = img_response.content

            img_name = f'{i+1}.jpg'
            img_path = os.path.join(chapter_folder, img_name)

            with open(img_path, 'wb') as file:
                file.write(img_content)

        printProgressBar(downloading_chapter, chapter_len, prefix = 'Progress:', suffix = 'Complete', length = 50)

@time_wrapper
def download_range(website, start_chapter=None, end_chapter=None, download_all=False, show_chapter_names=False):
    manga_name, chapters = scrap(website)
    manga_len = len(chapters)
    
    parent_directory = 'Downloads'
    output_folder = os.path.join(parent_directory, manga_name)

    if show_chapter_names:
        print(manga_name + ' chapters:')
        chapter_names = list(chapters.keys())
        for i, chapter in enumerate(chapters):
            print(f'{manga_len-i}. {chapter}')

    if download_all:
        download_all_chapters(manga_name, chapters)
        return

    if start_chapter is None:
        start_chapter = int(input('Enter the start chapter number: '))
    if end_chapter is None:
        end_chapter = int(input('Enter the end chapter number: '))

    if start_chapter > end_chapter:
        start_chapter, end_chapter = end_chapter, start_chapter
    
    for chapter_number in range(start_chapter, end_chapter+1):
        chapter_name = f'Chapter {chapter_number}'
        chapter_number = manga_len - chapter_number

        chapter_folder = os.path.join(output_folder, chapter_name)
        os.makedirs(chapter_folder, exist_ok=True)

        headers = {
                'referer': 'Referer: https://chapmanganato.to/'
                }
        
        img_srcs = chapters[chapter_names[chapter_number]]
        
        print(f'Downloading {chapter_names[chapter_number]}...')
        printProgressBar(0, len(img_srcs), prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, img_src in enumerate(img_srcs):
            img_response = requests.get(img_src, headers=headers)
            img_content = img_response.content

            img_name = f'{i+1}.jpg'
            img_path = os.path.join(chapter_folder, img_name)

            with open(img_path, 'wb') as file:
                file.write(img_content)

            printProgressBar(i+1, len(img_srcs), prefix = 'Progress:', suffix = 'Complete', length = 50)

def search_manga(website):
    manga_name, chapters = scrap(website)
    manga_len = len(chapters)

    print('\n' + manga_name + ' chapters:')
    for i, chapter in enumerate(chapters):
        print(f'{manga_len-i}. {chapter}')
    print()

def main():
    parser = argparse.ArgumentParser(description='Download manga chapters.')
    parser.add_argument('url', type=str, help='The URL of the manga to download')
    parser.add_argument('--start', type=int, help='The starting chapter number')
    parser.add_argument('--end', type=int, help='The ending chapter number')
    parser.add_argument('--names', action='store_true', help='Show chapters names')
    parser.add_argument('--search', action='store_true', help='Search for all chapters of the manga')
    parser.add_argument('--all', action='store_true', help='Download all chapters')

    args = parser.parse_args()

    if 'manganato' not in args.url:
        print('Please provide a valid manganato URL')
        return
    if args.start and args.end and args.start > args.end:
        print('The start chapter number should be less than the end chapter number')
        return
    
    if args.search:
        search_manga(args.url)
        return
    if args.all:
        download_range(args.url, download_all=True)
        return
    else:
        download_range(args.url, start_chapter=args.start, end_chapter=args.end)
        return

if __name__ == '__main__':
    main()