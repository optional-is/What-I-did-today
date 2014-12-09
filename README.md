# What I did today

This is a very simple service that emails you a reminder asking what you did during the day. You simply reply to the email and it logs the response.

Ideally, for a distributed team, each can answer with what they have been working on and it will collate all the responses for everyone to easily see. All this is handled via email.

The service uses Mandrill, you will need to setup several things outside of this code. Updating your MX record to let Mandrill receive your emails and adding webhooks into Mandrill so that it calls back to this app with the data.

This is also using a postgres database to store your team members and their email responses. To setup the databases, you will need to get to a python command prompt and type:

from app import db

db.create_all()

These two commands will build the database for you.

You can automatically deploy this code to Heroku by clicking the button
[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

After which you will still need to update Mandrill & create the database tables.

## Todo
* Improve the raw_email parsing to remove block quotes, signatures, etc.
* Add natural language parsing
* Add database migration support
