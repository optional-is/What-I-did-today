from flask import Flask
from flask import request
import os
import datetime
import json
import re
from smtplib import SMTP
from cStringIO import StringIO
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.header import Header
from email import Charset
from email.generator import Generator

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

class Member(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String())
    email = db.Column(db.String())

    def __init__(self, name, email):
        self.name  = name
        self.email = email

    def __repr__(self):
        return '<name {}>'.format(self.name)

tags = db.Table('tags',
    db.Column('tag_id',     db.Integer, db.ForeignKey('tag.id')),
    db.Column('message_id', db.Integer, db.ForeignKey('message.id'))
)
		
class Tag(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String())

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<name {}>'.format(self.name)
		
class Message(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String())
    message  = db.Column(db.String())
    date_did = db.Column(db.String())
    tags     = db.relationship('Tag', secondary=tags, backref=db.backref('messages', lazy='dynamic'))

    def __init__(self, email, message, date_did):
        self.message  = message
        self.email    = email
        self.date_did = date_did

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def tag(self,tag):
		# It should be a tag object, but if it isn't, we'll sort it out
		if type(tag) is unicode:
			tag = Tag(tag)
		self.tags.append(tag)
		return self

    def untag(self,tag):
		# It should be a tag object, but if it isn't, we'll sort it out
		if type(tag) is unicode:
			tag = db.session.query(Tag).filter_by(name=tag)	
		self.tags.remove(tag)
		return self



def send_email(to_email,subject,message):
    # send the message
    smtp = SMTP()
    smtp.connect('smtp.mandrillapp.com', 587)
    smtp.login(os.environ.get('MANDRILL_USERNAME'), os.environ.get('MANDRILL_APIKEY'))
    
    from_addr = "Tindfell <whatididtoday@tindfell.com>"
    to_addr = [to_email]
    
    date = datetime.datetime.now().strftime( "%d/%m/%Y %H:%M" )
    
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')
    msg = MIMEMultipart("alternative")
    
    msg['From'] = Header(from_addr.encode('utf-8'), 'UTF-8').encode()
    msg['To'] = Header(', '.join(to_addr).encode('utf-8'), 'UTF-8').encode()
    msg['Subject'] = Header(subject.encode('utf-8'), 'UTF-8').encode()
    
    msg.attach(MIMEText(message.encode('utf-8'),'plain','utf-8'))
    #msg.attach(MIMEText(message.encode('utf-8'),'html','utf-8'))
    
    io = StringIO()
    g = Generator(io, False) # second argument means "should I mangle From?"
    g.flatten(msg)
    
    # For Degubbing
    #print io.getvalue()
    
    # send the message!
    smtp.sendmail(from_addr, to_addr, io.getvalue())
    smtp.quit()
    return

@app.route("/webhook", methods=['GET','POST'])
def webhook():
	# Get the data from mandrill and save it into the database
		
	if 'mandrill_events' in request.form:
		mandrill_events = json.loads(request.form['mandrill_events'])
		for inbound in mandrill_events:
			if inbound['event'] == u"inbound":
				subject    = inbound['msg']['subject']
				from_email = inbound['msg']['from_email']
				message    = inbound['msg']['text']
				
				#remove any signatures from the email
				signature_pos = message.find('-- ')
				message = message[:signature_pos]
				
				# Try to parse this a bit better
				date_did = subject
				
				# Save the information
				mm = Message(from_email, message, date_did)
				# Save everything

				# @TODO: Parse the message for tags
				tags = re.findall(r'#\w+', message)
				for i in tags:
					mm.tag(i[1:])
				
				db.session.add(mm)
				db.session.commit()
				
		return "Success"
	
	return "Error"

@app.route("/messages", methods=['GET'])
def messages():
	# Here we look in the database, loop through messages and display them

	html = ''
	messages = db.session.query(Message).all()
	for i in messages:
		html += '<h2>%s</h2><p>%s</p>'%(i.email,i.message)
		if len(i.tags) > 0:
			html += '<ul>'
			for j in i.tags:
				html += '<li>%s</li>'%(j.name)
			html += '</ul>'
			
    
	return html
    
		
@app.route("/ask", methods=['GET'])
def ask():
	# Here we look in the database, loop through users and send them an email asking what they have done today	
	if 'api_key' in request.args:
		if request.args['api_key'] == os.environ.get('API_KEY'):
			# Now loop through the DB and send the standard email
			subject = "What did you do today %s"%(datetime.datetime.today().strftime("%Y-%m-%d"))
			members = db.session.query(Member).all()
			for i in members:
				# Send an email to each person, extra X-Headers if needed
				send_email("%s <%s>"%(i.name,i.email),subject,"")
			
			return "Success"
			
	# If you are getting here, something failed	
	return "Error"

@app.route("/")
def hello():
    return "Welcome to Flask!"

if __name__ == "__main__":
	# Set up logging to stdout, which ends up in Heroku logs
	#stream_handler = logging.StreamHandler()
	#stream_handler.setLevel(logging.WARNING)
	#app.logger.addHandler(stream_handler)
	#manager.run()

	app.debug = True
	app.run(host='0.0.0.0', port=flask_config.port)
	#app.run(host='0.0.0.0', port=5000)