# coding=utf-8
import os
import flask
import httplib2
from apiclient import discovery
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from pymongo import MongoClient
import gridfs
import last_update
import io
import datetime
import sys
from flask import Flask, flash, redirect, render_template, request, url_for
import time
import read_sets

app = Flask(__name__)
app.secret_key = 'random string'
mongoclient = MongoClient('localhost',27017)
db = mongoclient.drive_backup
coll = db.dataset
fs=gridfs.GridFS(db)


@app.route('/')
def init():
    credentials = get_credentials()
    if credentials == False:
        return flask.redirect(flask.url_for('oauth2callback'))
    elif credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        flash('authorization successfull')
        return flask.redirect(flask.url_for('working'))
    return render_template('init.html')

@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets('client_secret.json',
                                          scope='https://www.googleapis.com/auth/drive',
                                          redirect_uri=flask.url_for('oauth2callback',
                                                                     _external=True))  # access drive api using developer credentials
    flow.params['include_granted_scopes'] = 'true'
    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        open('credentials.json', 'w').write(credentials.to_json())  # write access token to credentials.json locally
        return flask.redirect(flask.url_for('idle'))

def get_credentials():
    credential_path = 'credentials.json'

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        print("Credentials not found.")
        return False
    else:
        print("Credentials fetched successfully.")
        return credentials


@app.route('/idle')
def idle():
    return render_template('idle.html')

@app.route('/settings', methods=['GET','POST'])
def settings():
    error = None

    if request.method == 'POST':
        entry=request.form['max_size']
        try:
            int(entry)
            fichier = open("size_setting.txt", "w")
            fichier.write(entry)
            fichier.close()
            return redirect(url_for('idle'))
        except:
            error = 'Invalid entry, you must provide a number'

    return render_template('settings.html', error=error)

@app.route('/working', methods=['GET', 'POST'])
def working():

    max_size = read_sets.get()

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)

    results = drive_service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        flash('No files found.')
    else:
        flash('Here are the files found in your google drive:')
        for item in items:
            flash('{0}'.format(item['name']))
    page_token=None

    while True:

        response = drive_service.files().list(q="mimeType contains 'pdf' or mimeType contains 'mp3' or mimeType co"
                                                "ntains 'docx' or mimeType contains 'docx' or mimeType contains "
                                                "'jpg' or mimeType contains 'ppt' or mimeType contains 'jpeg' "
                                                "or mimeType contains 'pptx' or mimeType contains 'png'",
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name, modifiedTime)',
                                              pageToken=page_token).execute()

        flash("********************************************************")
        flash("downloading new files")
        flash("********************************************************")
        files = response.get('files', [])
        if not files:
            flash('No files')
        else:
            for file in files:
                drive_id = file.get('id')
                file_name = file.get('name')
                flash("")
                flash("working on "+file_name)
                if fs.exists(metadata=drive_id):
                    flash('this file is already in your database')
                    fp = fs.get_last_version(metadata=drive_id)
                    if last_update.to_date(file.get('modifiedTime')) > fp.uploadDate:
                        flash ('but is not up to date')
                        request = drive_service.files().get_media(fileId=drive_id)
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        flash('downloading')
                        j=1
                        oversize = False
                        while done is False:
                            print(j)
                            j=j+1 #un mega octet = 1,91 chunks
                            status, done = downloader.next_chunk()
                            if j>max_size:
                                oversize=True
                                break;
                        if oversize:
                            flash("the file is too heavy, it will not be uploaded")
                            fs.delete(fp._id)
                        else:
                            fs.delete(fp._id)
                            fs.put(fh.getvalue(), filename=file_name,metadata=drive_id)

                    else:
                        flash("and is up tu date")
                else:
                    flash('file doesnt exist')
                    request = drive_service.files().get_media(fileId=drive_id)
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    flash('downloading')
                    j=1
                    oversize=False
                    while done is False:
                        j=j+1
                        print(j)
                        status, done = downloader.next_chunk()
                        if j>max_size:
                            oversize = True
                            break;
                    if oversize:
                        print("the file is too heavy, it will not be uploaded")
                    else:
                        fs.put(fh.getvalue(), filename=file_name, metadata=drive_id)

        if page_token is None:
            break;

    if True:
        return redirect(url_for('deleting_choice'))
    return render_template('working.html')


@app.route('/deleting_choice',methods=['GET']) #this part is not satisfying
def deleting_choice():
    return render_template('deleting_choice.html')

@app.route('/deleting',methods=['GET', 'POST']) #this part is not satisfying
def deleting():

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)

    flash("********************************************************")
    flash("deleting the files that are no longer on the drive")
    flash("********************************************************")

    for file in fs.find({}, no_cursor_timeout=True):
        results = drive_service.files().list(q="name = '"+str(file.name)+"'",pageSize=10, fields="nextPageToken, files(id, name)").execute()
        #str(file.name)
        files = results.get('files', [])

        if not files:
            flash("deleting "+file.name)
            #ici il y a un problème avec la fonction de recherche de drive
            #il parvient toujours à "trouver" les documents, même une fois supprimés, il doit garder en mémoire le nom
            #parce que le code python est bon (exemple si on remplace str(file.name) par "blabla"
            # alors toute la base de donnée est supprimée)
            fs.delete(file._id)

    if True:
        return redirect(url_for('idle'))

    return render_template('deleting.html')



if __name__ == "__main__":
    if os.path.exists('client_secret.json') == False:
        print('Client secrets file (client_id.json) not found in the app path.')
        exit()
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.run(debug=False)