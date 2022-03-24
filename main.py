from flask import Flask, redirect, render_template, request, session, flash, url_for
from datetime import timedelta
import sqlite3 as sql
import requests

con = sql.connect('test_database.db')
con.execute('CREATE TABLE IF NOT EXISTS tbl (ID INTEGER PRIMARY KEY AUTOINCREMENT, songtitle TEXT, songartist TEXT)')
con.close
app = Flask(__name__)

# return a list containing dicts of info about the song #
def scrape_for_songs(content):
    # in reference from "pure-u-md-1-4" appearing...
    # song link is 2 down  
    # song thumbnail is 4 down
    # song duration is 5 down
    # song title is 7 down
    # song artist is 11 down
    return None

def search_songs(t):
    searchterm = t.replace(' ', '+')
    requesturl = f'https://invidious.kavin.rocks/search?q={searchterm}+content_type%3Avideo'
    request = requests.get(requesturl)
    return scrape_for_songs(request.text) 

@app.route('/searchresults/<term>', methods=['POST', 'GET'])
def results(term):
    searchresults = search_songs(term)
    return render_template('searchresults.html', results=searchresults)

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        try:
            newsongtitle = request.form['stit']
        except:
            return redirect(url_for('results', term=request.form['srch']))
        con = sql.connect('test_database.db')
        newsongartist = request.form['sart']
        con.execute('INSERT INTO tbl (songtitle, songartist) VALUES (?,?)', (newsongtitle, newsongartist)) 
        con.commit()
        con.close()
    con = sql.connect('test_database.db')
    csr = con.execute('SELECT songtitle, songartist FROM tbl WHERE ID=(SELECT Min(ID) FROM tbl)')
    songtitle = '' 
    songartist = '' 
    for row in csr:
        songtitle = row[0] 
        songartist = row[1] 
    songqueue = con.execute(f'SELECT songtitle, songartist FROM tbl WHERE songtitle<>"{songtitle}"')
    testing = []
    for i in songqueue:
        testing.append(i)
    con.close()
    #https://i.imgur.com/hUopSs6.jpg
    return render_template('home.html', songtitle=songtitle, artist=songartist, imgurl='', queue=testing)

@app.route('/clear')
def clear():
    con = sql.connect('test_database.db')
    con.execute('DELETE FROM tbl')
    con.commit()
    con.close()
    return 'cleared'

if __name__ == '__main__':
	app.run(debug=True)

