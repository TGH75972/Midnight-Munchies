import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)
def init_db():
    with sqlite3.connect('/tmp/favorites.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS places (id INTEGER PRIMARY KEY, name TEXT, address TEXT)')
init_db() 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    location_name = request.form.get('location', '').strip()
    api_key = "67991bff3860450e88b140e28f0c7cb3"
    
    if not location_name:
        return redirect(url_for('index'))

    geo_url = f"https://api.geoapify.com/v1/geocode/search?text={location_name}&apiKey={api_key}"
    geo_data = requests.get(geo_url).json()
    
    if not geo_data.get('features'):
        return render_template('results.html', results=[], location=location_name)
    
    lon = geo_data['features'][0]['geometry']['coordinates'][0]
    lat = geo_data['features'][0]['geometry']['coordinates'][1]

    places_url = f"https://api.geoapify.com/v2/places?categories=catering&filter=circle:{lon},{lat},10000&bias=proximity:{lon},{lat}&limit=20&apiKey={api_key}"
    places_response = requests.get(places_url)
    places_response.raise_for_status()
    places_data = places_response.json()
    
    results = []
    for feature in places_data.get('features', []):
        props = feature.get('properties', {})
        results.append({
            "name": props.get('name', 'Unnamed Spot'),
            "formatted_address": props.get('address_line2', 'Address Unknown')
        })
    
    return render_template('results.html', results=results, location=location_name)

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    name = request.form.get('name')
    address = request.form.get('address')
    with sqlite3.connect('/tmp/favorites.db') as conn:
        conn.execute('INSERT INTO places (name, address) VALUES (?, ?)', (name, address))
    return redirect(url_for('view_favorites'))

@app.route('/favorites')
def view_favorites():
    with sqlite3.connect('/tmp/favorites.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM places')
        favs = cursor.fetchall()
    return render_template('favorites.html', favs=favs)
@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_favorite(item_id):
    with sqlite3.connect('/tmp/favorites.db') as conn:
        conn.execute('DELETE FROM places WHERE id=?', (item_id,))
    return redirect(url_for('view_favorites'))
if __name__ == '__main__':
    app.run(debug=True)
