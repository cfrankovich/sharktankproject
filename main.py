from flask import Flask, redirect, render_template, request, session, flash, url_for
from datetime import timedelta
import sqlite3 as sql
import requests
from bs4 import BeautifulSoup as bs
import json

con = sql.connect('test_database.db')
con.execute('CREATE TABLE IF NOT EXISTS tbl (ID INTEGER PRIMARY KEY AUTOINCREMENT, songtitle TEXT, songartist TEXT, thumbnail TEXT)')
con.close
app = Flask(__name__)

def scrape_for_songs(content):
    jsondata = json.loads(content)
    songs = []
    for i in range(10):
        info = {}
        info['Title'] = jsondata['items'][i]['snippet']['title']
        videoid = jsondata['items'][i]['id']['videoId']
        info['Link'] = f'https://youtube.com/watch?v={videoid}'
        info['Duration'] = '0:00' # https://www.googleapis.com/youtube/v3/videos?id={VIDEO_ID}&part=contentDetails&key={YOUR_API_KEY} #
        info['Thumbnail'] = jsondata['items'][i]['snippet']['thumbnails']['high']['url'] 
        info['Artist'] = jsondata['items'][i]['snippet']['channelTitle'] 
        songs.append(info)
    return songs 

def search_songs(t):
    searchterm = t.replace(' ', '+')
    ytapikey = ''
    try:
        with open('YTAPIKEY.txt') as keyfile:
            ytapikey = keyfile.read()[:-1]
    except IOError:
        print('Youtube API Key was not able to be read from the file "YTAPIKEY.txt"')
        return None
    requesturl = f'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=20&q={searchterm}&type=video&key={ytapikey}'
    request = requests.get(requesturl)
    if int(request.status_code / 100) != 2:
        print(f'Request returned with status code {request.status_code}!')
        return None
    return scrape_for_songs(request.text) 

@app.route('/searchresults/<term>', methods=['POST', 'GET'])
def results(term):
    searchresults = search_songs(term)
    if searchresults == None:
        return render_template('error.html', requested=f'https://invidious.kavin.rocks/search?q={term}+content_type%3Avideo')
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

@app.route('/clear/')
def clear():
    con = sql.connect('test_database.db')
    con.execute('DELETE FROM tbl')
    con.commit()
    con.close()
    return 'cleared'

if __name__ == '__main__':
	app.run(debug=True)

