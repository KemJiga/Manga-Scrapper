from flask import Flask, jsonify, request
from Scrapper import search_manga, download_range
import asyncio

app = Flask(__name__)

"""
Endpoints
1. buscar manga
entrada: link de manganato
salida: lista de capitulos

2. descargar un capitulo
entrada: numero del capitulo
salida: lista de imagenes

3. descargar rango de capitulos
entrada: numero de inicio y fin
salida: lista de imagenes

4. descargar todos los capitulos
salida: lista de imagenes
"""

@app.route('/search/<string:manga_id>', methods=['GET'])
async def get_manga(manga_id, update=True):
    website = f'https://manganato.com/manga-{manga_id}'
    try:
        chapters = await search_manga(website, update)
        return jsonify(chapters), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/download/<string:manga_id>/<string:chapters>', methods=['GET'])
async def download_chapter(manga_id, chapters):
    website = f'https://manganato.com/manga-{manga_id}'
    try:
        start = int(chapters.split('-')[0])
        end = int(chapters.split('-')[1])
        await download_range(website, start, end)
        return jsonify({'message': 'Chapter downloaded'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/download/<string:manga_id>/all', methods=['GET'])
async def download_all_chapters(manga_id):
    website = f'https://manganato.com/manga-{manga_id}'
    try:
        await download_range(website, download_all=True)
        return jsonify({'message': 'Chapter downloaded'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
