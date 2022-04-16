from flask import Flask, jsonify, redirect, render_template, request, session, url_for, render_template_string
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3 as sql
import requests
import time
import json

con = sql.connect('test_database.db')
con.execute('CREATE TABLE IF NOT EXISTS tbl (ID INTEGER PRIMARY KEY AUTOINCREMENT, songtitle TEXT, songartist TEXT, thumbnail TEXT, songlink TEXT, songduration INTEGER)')
con.close
sched = BackgroundScheduler(daemon=True)
sched.start()
app = Flask(__name__)

# once the song is finished playing this function should run #
# remove the song from the database and update admin page to play the new one #
def song_over():
    print('song is over... removing...')
    # remove the top song if a song actualy played :(#
    con = sql.connect('test_database.db')
    con.execute('DELETE FROM tbl WHERE ID=(SELECT Min(ID) FROM tbl)')
    con.commit()
    con.close()
    sched.remove_job('SONGOVERJOB')
    # see if theres another song in queue and make a new job for it #
    con = sql.connect('test_database.db')
    csr = con.execute('SELECT songtitle, songartist, thumbnail, songlink, songduration FROM tbl WHERE ID=(SELECT Min(ID) FROM tbl)')
    songtitle = '' 
    songartist = '' 
    songthumbnail = ''
    songlink = ''
    songdur = 0
    for row in csr:
        songtitle = row[0] 
        songartist = row[1] 
        songthumbnail = row[2]
        songlink = row[3]
        songdur = row[4]
    con.close()
    try:
        el = f'https://www.youtube.com/embed/{songlink.split("=")[1]}?autoplay=1' 
    except:
        el = ''
    if songdur != 0:
        sched.add_job(song_over, 'interval', seconds=songdur, id='SONGOVERJOB')
        print('_+=+==+==++++++====== added new new job')


# get num seconds from the cryptic shit yt gave me #
def fuckyouyoutube(s):
    total = 0
    try:
        total += int(s.split('M')[0]) * 60
    except:
        pass
    try:
        total += int(s.split('S')[0][-2:])
    except:
        pass
    return total

# used to scrape. idk what to call it now so it sticks #
def scrape_for_songs(content, ytapikey):
    jsondata = json.loads(content)
    songs = []
    for i in range(5):
        info = {}
        info['Title'] = jsondata['items'][i]['snippet']['title']
        videoid = jsondata['items'][i]['id']['videoId']
        info['Link'] = f'https://youtube.com/watch?v={videoid}'
        # literal cancer #
        try:
            dururl = f'https://www.googleapis.com/youtube/v3/videos?id={videoid}&part=contentDetails&key={ytapikey}' 
            request = requests.get(dururl)
            jsondur = json.loads(request.text)
            crypticdur = jsondur['items'][0]['contentDetails']['duration'].split('T')[1] 
            total = fuckyouyoutube(crypticdur)
            info['Duration'] = total 
        except:
            print('Error with duration request')
            info['Duration'] = 0
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
    requesturl = f'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=5&q={searchterm}&type=video&key={ytapikey}'
    try:
        request = requests.get(requesturl)
    except:
        print('Error with request')
        return None
    if int(request.status_code / 100) != 2:
        print(f'Request returned with status code {request.status_code}!')
        return None
    return scrape_for_songs(request.text, ytapikey) 

@app.route('/searchresults/<term>', methods=['POST', 'GET'])
def results(term):
    searchresults = search_songs(term)
    if searchresults == None:
        return render_template('error.html') 
    if request.method == 'POST':
        bidamount = int(request.form['bidamt']) 
        print(f'Bidded: ${bidamount}')
        # shut up it works #
        k = -1 
        print(len(searchresults))
        for i in range(len(searchresults)):
            try:
               test = request.form[f'adsn{i}']
               k = i
            except:
                pass
        newsongtitle = searchresults[k]['Title'] 
        newsongartist = searchresults[k]['Artist'] 
        newthumbnail = searchresults[k]['Thumbnail']
        newlink = searchresults[k]['Link']
        newsongdur = searchresults[k]['Duration']
        con = sql.connect('test_database.db')
        con.execute('INSERT INTO tbl (songtitle, songartist, thumbnail, songlink, songduration) VALUES (?,?,?,?,?)', (newsongtitle, newsongartist, newthumbnail, newlink, newsongdur)) 
        con.commit()
        con.close()
        return redirect(url_for('home'))
    return render_template('searchresults.html', results=searchresults, numresults=len(searchresults))

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
            return redirect(url_for('results', term=request.form['srch']))
    return render_template('home.html')

@app.route('/add/', methods=['POST', 'GET'])
def add():
    if request.method == 'POST':
        random1 = request.form['sng']
        random2 = request.form['art']
        con = sql.connect('test_database.db')
        con.execute('INSERT INTO tbl (songtitle, songartist, thumbnail) VALUES (?,?,?)', (random1, random2, 'https://i.imgur.com/hUopSs6.jpg'))
        con.commit()
        con.close()
    return render_template_string('''<h1>add songs here (for testing/no wifi)</h1> 
           <form autocomplete="off" method="POST">
                <input type="text" name="sng" placeholder="songhere"></input>
                <input type="text" name="art" placeholder="artisthere"></input>
                <input type="submit" name="srsb" value="Submit"></input>
           </form>
            ''')

@app.route('/clear/')
def clear():
    con = sql.connect('test_database.db')
    con.execute('DELETE FROM tbl')
    con.commit()
    con.close()
    return 'cleared'

# bad but works for now #
@app.route('/stream/')
def stream():
    def generate():
        while True:
            con = sql.connect('test_database.db')
            songqueue = con.execute(f'SELECT songtitle, songartist, thumbnail, songlink FROM tbl')
            queuedata = {}
            i = 0
            for i, song in enumerate(songqueue):
                queuedata[i] = {}
                queuedata[i]['title'] = song[0] 
                queuedata[i]['artist'] = song[1] 
                queuedata[i]['img'] = song[2] 
                queuedata[i]['link'] = f'https://www.youtube.com/embed/{song[3].split("=")[1]}?autoplay=1' 
            queuedatastr = json.dumps(queuedata)
            con.close()
            yield str(i) + queuedatastr + '\n' 
            time.sleep(5)
    return app.response_class(generate(), mimetype='application/json')

@app.route('/admin/')
def admin():
    con = sql.connect('test_database.db')
    csr = con.execute('SELECT songtitle, songartist, thumbnail, songlink, songduration FROM tbl WHERE ID=(SELECT Min(ID) FROM tbl)')
    songtitle = '' 
    songartist = '' 
    songthumbnail = ''
    songlink = ''
    songdur = 0
    for row in csr:
        songtitle = row[0] 
        songartist = row[1] 
        songthumbnail = row[2]
        songlink = row[3]
        songdur = row[4]
    con.close()
    try:
        el = f'https://www.youtube.com/embed/{songlink.split("=")[1]}?autoplay=1' 
    except:
        el = ''
    try:
        sched.remove_job('SONGOVERJOB')
    except:
        pass
    if songdur != 0:
        sched.add_job(song_over, 'interval', seconds=songdur, id='SONGOVERJOB')
        print('_+=+==+==++++++====== added new job')
    return render_template('admin.html') 


if __name__ == '__main__':
	app.run(debug=True)

