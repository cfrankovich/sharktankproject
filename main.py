from flask import Flask, redirect, render_template, request, session, flash, url_for
from datetime import timedelta
import sqlite3 as sql
import requests
from bs4 import BeautifulSoup as bs

con = sql.connect('test_database.db')
con.execute('CREATE TABLE IF NOT EXISTS tbl (ID INTEGER PRIMARY KEY AUTOINCREMENT, songtitle TEXT, songartist TEXT, thumbnail TEXT)')
con.close
app = Flask(__name__)

def scrape_for_songs(content):
    songs = []
    lines = content.splitlines()
    for i, line in enumerate(lines):
        info = {}
        if line.__contains__('pure-u-md-1-4'):
            # gross but works due to some results being weird (not having some atributsesseses)#
            try:
                soup = bs(lines[i+7], 'html.parser')
                info['Title'] = soup.p.string 
                soup = bs(lines[i+2], 'html.parser')
                xtra = soup.find(href=True) 
                info['Link'] = xtra['href']
                soup = bs(lines[i+5], 'html.parser')
                info['Duration'] = soup.p.string
                soup = bs(lines[i+4], 'html.parser')
                xtra = soup.find('img')
                info['Thumbnail'] = f"https://invidious.kavin.rocks{xtra['src']}"
                soup = bs(lines[i+11], 'html.parser')
                info['Artist'] = soup.p.string
                songs.append(info)
            except:
                pass
    return songs 

def search_songs(t):
    searchterm = t.replace(' ', '+')
    requesturl = f'https://invidious.kavin.rocks/search?q={searchterm}+content_type%3Avideo'
    request = requests.get(requesturl)
    return scrape_for_songs(request.text) 

@app.route('/searchresults/<term>', methods=['POST', 'GET'])
def results(term):
    searchresults = search_songs(term)
    if request.method == 'POST':
        # shut up it works #
        k = -1 
        for i in range(len(searchresults)):
            try:
               test = request.form[f'adsn{i}']
               k = i
            except:
                pass
        newsongtitle = searchresults[k]['Title'] 
        newsongartist = searchresults[k]['Artist'] 
        newthumbnail = searchresults[k]['Thumbnail']
        con = sql.connect('test_database.db')
        con.execute('INSERT INTO tbl (songtitle, songartist, thumbnail) VALUES (?,?,?)', (newsongtitle, newsongartist, newthumbnail)) 
        con.commit()
        con.close()
        return redirect(url_for('home'))
    return render_template('searchresults.html', results=searchresults, numresults=len(searchresults))

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
            return redirect(url_for('results', term=request.form['srch']))
    con = sql.connect('test_database.db')
    csr = con.execute('SELECT songtitle, songartist, thumbnail FROM tbl WHERE ID=(SELECT Min(ID) FROM tbl)')
    songtitle = '' 
    songartist = '' 
    songthumbnail = ''
    for row in csr:
        songtitle = row[0] 
        songartist = row[1] 
        songthumbnail = row[2]
    songqueue = con.execute(f'SELECT songtitle, songartist, thumbnail FROM tbl WHERE songtitle<>"{songtitle}"')
    testing = []
    for i in songqueue:
        testing.append(i)
    con.close()
    #https://i.imgur.com/hUopSs6.jpg
    return render_template('home.html', songtitle=songtitle, artist=songartist, imgurl=songthumbnail, queue=testing)

@app.route('/clear')
def clear():
    con = sql.connect('test_database.db')
    con.execute('DELETE FROM tbl')
    con.commit()
    con.close()
    return 'cleared'

if __name__ == '__main__':
	app.run(debug=True)

