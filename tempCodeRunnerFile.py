from flask import Flask, render_template,request,redirect,url_for,session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
from flask_session import Session
from flask_socketio import SocketIO, join_room, leave_room,emit
import json

local_server=True
with open('config.json','r') as c:
 params=json.load(c) ['params']    
app=Flask(__name__)
app.debug= True
app.config['SECRET_TYPE']='MRAAKASH'
app.config['SESSION_TYPE']= 'filesystem'
Session(app)
socketio=SocketIO(app, manage_session=True)

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail=Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI']=params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI']= params['prod_uri']    
db=SQLAlchemy(app)

class Contacts(db.Model):
    Sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg= db.Column(db.String(120), nullable=False)
    email= db.Column(db.String(20), nullable=False)
    date= db.Column(db.String(12),nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),nullable=False)
    slug= db.Column(db.String(21), nullable=False)
    content= db.Column(db.String(120), nullable=False)
    date= db.Column(db.String(12), nullable=True)
    img_file= db.Column(db.String(12), nullable=True)

        
    
@app.route("/")
@app.route("/index.html")
def home():
    return render_template('index.html',params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post= Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params, post=post)


@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''ADD Entry to the database'''
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        entry=Contacts(name=name, phone_num=phone, msg=message, email=email, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message From Blog'+name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + "\n"+ phone)
    return render_template('contact.html',params=params)

@app.route("/post")
def post():
    return render_template('post.html',params=params)

@app.route("/news.html")
def news():
    return render_template('news.html',params=params)


@app.route("/connect, /index.html", methods=['GET','POST'])
def index():
    return render_template('index1.html')

@app.route("/chat", methods=['GET','POST'])
def chat():
    if(request.method=='POST'):
        username=request.form['username']
        room=request.form['room']
        #Store the data
        session['username']=username
        session['room']= room
        return render_template('chat.html',session= session)
    else:
        if(session.get('username') is not None):
            return render_template('chat.html',session= session)
        else:
            return redirect(url_for('index1'))

@socketio.on('join', namespace='/chat')
def join(message):
    room =session.get('room')
    join_room(room)
    emit('status', {'msg': session.get('username')+ 'has entered the room.'}, room= room) 
           
           
@socketio.on('text' , namespace='/chat')
def text(message):
    room= session.get('room')
    emit('message',{'msg': session.get('username')+':'+ message['msg']}, room=room )               

@socketio.on('left', namespace='/chat')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)



if __name__ == '__main__':
    socketio.run(app,debug=True)
