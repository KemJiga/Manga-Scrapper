import json, os
from werkzeug.wsgi import FileWrapper
from flask import Flask, jsonify, request, send_file, Response
from Scrapper import search_by_name, download_chapter, scrape
from utils import search_by_accuracy, zip_specific_folder

app = Flask(__name__)

@app.route('/search/', methods=['GET'])
async def search_manga():
    manga_name = request.args.get('manga_name')
    search = await search_by_name(manga_name)
    code = search['code']
    print(search)
    if code == 404:
        return jsonify(search['message']), 404
    try:
        return jsonify(search['mangas']), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/search_chapters/', methods=['GET'])
async def search_chapters():
    manga_name = request.args.get('manga_name')
    chapter = int(request.args.get('chapter'))
    offset = request.args.get('offset', 0)

    with open('Downloads/manga_yellow_pages.json', 'r') as file:
        mangas = json.load(file)
        confirm_name = search_by_accuracy(manga_name, mangas)
    
    if not confirm_name:
        return jsonify({'message': 'Manga not found in yellow pages'}), 404
    
    input_title = mangas[manga_name]
    manga_titles = list(input_title.keys())
    first_manga_title = manga_titles[offset]
    first_manga_src = input_title[first_manga_title]['src']

    chapters = await scrape(first_manga_src)
    chapters_name = list(chapters.keys())

    try:
        return jsonify({'chapter':chapters[chapters_name[chapter]]}), 200
    except Exception as e:
        return jsonify({'error message': str(e)}), 500
    
@app.route('/download_chapter/', methods=['GET'])
async def download():
    data = request.get_json()
    manga_link = data.get('manga_link')
    manga_name = request.args.get('manga_name')
    chapter = int(request.args.get('chapter'))

    output_folder = os.path.join('Downloads', manga_name)

    try:
        result = await download_chapter(manga_link, f'Chapter {chapter}', output_folder)
        if result['code'] == 200:
            return jsonify(result), 200
        return jsonify(result), 500
    except Exception as e:
        return jsonify({'error message': str(e)}), 500

@app.route('/get_imgs/', methods=['GET'])
def get_img():
    manga_name = request.args.get('manga_name')
    chapter = request.args.get('chapter')
    
    image_paths = []
    parent_folder = os.path.join('Downloads', manga_name, f'Chapter {chapter}')
    for img in os.listdir(parent_folder):
        img = os.path.join(parent_folder, img)
        image_paths.append(img)

    zip_file = zip_specific_folder(parent_folder)
    if not zip_file:
        return Response(response="Invalid zip file", status="400")

    file_wrapper = FileWrapper(zip_file)
    headers = {
        'Content-Disposition': 'attachment; filename="{}"'.format('file.zip')
    }
    
    return Response(file_wrapper, mimetype='application/zip', direct_passthrough=True, headers=headers)

if __name__ == '__main__':
    app.run(debug=True)
