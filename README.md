# drive_to_mongo
Here is an app that fetches your files from your google drive and puts it in your mongo database.

Here are the packages you should install:

google-api-python-client
google-api-python-client-py3
google-api-python-client-uritemplate
parsedatetime
pymongo
oauth2client
Flask

You should also install mongodb.


You can synchronize it with this google account: raphael.montaud.api@gmail.com
(for the password you should ask me)
The file client_secrets in the main directory is the credentials to access this account.



You can synchronize it with your google drive by doing as follows:

    1)Use this wizard to create or select a project in the Google Developers Console and automatically turn on the API. Click Continue, then Go to credentials.
    2)On the Add credentials to your project page, click the Cancel button.
    3)At the top of the page, select the OAuth consent screen tab. Select an Email address, enter a Product name if not already set, and click the Save button.
    4)Select the Credentials tab, click the Create credentials button and select OAuth client ID.
    5)Select the application type Other, enter the name "Drive API Quickstart", and click the Create button.
    6)Click OK to dismiss the resulting dialog.
    7)Click the file_download (Download JSON) button to the right of the client ID.
    8)Move this file to your working directory and rename it client_secret.json.



