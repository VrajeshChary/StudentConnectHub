from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, UTC
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connectnet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.context_processor
def inject_now():
    return {'current_year': datetime.now(UTC).year}

db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class Connection(db.Model):
    __tablename__ = 'connections'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    connected_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # e.g. pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)
    # (Optional: add a unique constraint if desired, e.g. db.UniqueConstraint('user_id', 'connected_user_id', name='uix_connection'))
    # (Optional: add a relationship to the "connected" user, e.g. connected_user = db.relationship("User", foreign_keys=[connected_user_id], backref=db.backref("incoming_connections", lazy="dynamic")))

    def __init__(self, user_id, connected_user_id, status='pending'):
         self.user_id = user_id
         self.connected_user_id = connected_user_id
         self.status = status

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    university = db.Column(db.String(100))
    major = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    profile_picture = db.Column(db.String(200))
    bio = db.Column(db.Text)
    
    # Relationships (using Connection.user_id as foreign key)
    connections = db.relationship("Connection", foreign_keys=[Connection.user_id], backref=db.backref("user", lazy="joined"), lazy="dynamic")
    connected_to = db.relationship('Connection', foreign_keys='Connection.connected_user_id', backref='connected_user', lazy='dynamic')
    events = db.relationship('Event', backref='organizer', lazy='dynamic')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    notifications = db.relationship("Notification", backref=db.backref("user", lazy="joined"), lazy="dynamic")

    def __init__(self, username, email, password_hash, first_name=None, last_name=None, university=None, major=None, bio=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.university = university
        self.major = major
        self.bio = bio

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # (Optional: add a "room" column if you still need it, e.g. room = db.Column(db.String(100), nullable=False))

    def __init__(self, content, sender_id, recipient_id, room=None):
         self.content = content
         self.sender_id = sender_id
         self.recipient_id = recipient_id
         # (Optional: assign self.room if you added a "room" column)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    location = db.Column(db.String(200))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendees = db.relationship('User', secondary='event_attendees',
                              backref=db.backref('attending_events', lazy='dynamic'))

# Association table for event attendees
event_attendees = db.Table('event_attendees',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class BlogPost(db.Model):
    __tablename__ = 'blog_post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # (Optional: add other fields, e.g. slug, published, etc.)

    # (Update the "author" relationship (backref) so that the backref is named "blog_author" (instead of "author").)
    author = db.relationship('User', backref=db.backref('blog_posts', lazy='dynamic'), lazy='joined')

    def __init__(self, title, content, author_id, created_at=None, updated_at=None):
         self.title = title
         self.content = content
         self.author_id = author_id
         if created_at is not None:
             self.created_at = created_at
         if updated_at is not None:
             self.updated_at = updated_at

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    university = StringField('University', validators=[DataRequired()])
    major = StringField('Major', validators=[DataRequired()])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            university=form.university.data,
            major=form.major.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Create a list of temporary demo students with Indian names and details
    demo_users = [
        {
            'id': 101, # Temporary ID
            'username': 'RahulSharma',
            'major': 'Computer Science',
            'year': 'Senior',
            'bio': 'Interested in AI and machine learning.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Rahul+Sharma&background=random',
            'interests': ['Programming', 'Research'],
        },
        {
            'id': 102,
            'username': 'PriyaSingh',
            'major': 'Electrical Engineering',
            'year': 'Junior',
            'bio': 'Passionate about renewable energy and sustainable design.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Priya+Singh&background=random',
            'interests': ['Research', 'Design'],
        },
        {
            'id': 103,
            'username': 'AmitPatel',
            'major': 'Business Administration',
            'year': 'Sophomore',
            'bio': 'Aspiring entrepreneur with a focus on tech startups.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Amit+Patel&background=random',
            'interests': ['Entrepreneurship'],
        },
        {
            'id': 104,
            'username': 'AnjaliDesai',
            'major': 'Fine Arts',
            'year': 'Freshman',
            'bio': 'Exploring digital art and animation.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Anjali+Desai&background=random',
            'interests': ['Design'],
        },
        {
            'id': 105,
            'username': 'VikramYadav',
            'major': 'Mechanical Engineering',
            'year': 'Senior',
            'bio': 'Interested in robotics and automation.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Vikram+Yadav&background=random',
            'interests': ['Programming', 'Research'],
        },
        {
            'id': 106,
            'username': 'SnehaReddy',
            'major': 'Computer Science',
            'year': 'Junior',
            'bio': 'Frontend development enthusiast.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Sneha+Reddy&background=random',
            'interests': ['Programming', 'Design'],
        },
         {
            'id': 107,
            'username': 'ArjunNair',
            'major': 'Physics',
            'year': 'Graduate',
            'bio': 'Researcher in theoretical physics.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Arjun+Nair&background=random',
            'interests': ['Research'],
        },
        {
            'id': 108,
            'username': 'NehaGupta',
            'major': 'Economics',
            'year': 'Senior',
            'bio': 'Interested in financial markets and analytics.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Neha+Gupta&background=random',
            'interests': ['Research', 'Entrepreneurship'],
        },
        {
            'id': 109,
            'username': 'RohitVerma',
            'major': 'Chemical Engineering',
            'year': 'Junior',
            'bio': 'Focus on sustainable chemical processes.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Rohit+Verma&background=random',
            'interests': ['Research'],
        },
        {
            'id': 110,
            'username': 'DeepikaSharma',
            'major': 'Architecture',
            'year': 'Sophomore',
            'bio': 'Exploring modern architectural design.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Deepika+Sharma&background=random',
            'interests': ['Design'],
        },
    ]

    filtered_users = demo_users # Start with all demo users

    if request.method == 'POST':
        selected_major = request.form.get('major')
        selected_year = request.form.get('year')
        selected_interests = request.form.getlist('interests')

        # Apply filters
        if selected_major and selected_major != 'all':
            filtered_users = [user for user in filtered_users if user.get('major') == selected_major]

        if selected_year and selected_year != 'all':
             filtered_users = [user for user in filtered_users if user.get('year') == selected_year]

        if selected_interests:
             # Filter users who have at least one of the selected interests
             filtered_users = [user for user in filtered_users if any(interest in user.get('interests', []) for interest in selected_interests)]


    return render_template('dashboard.html', users=filtered_users)

@app.route('/network')
@login_required
def network():
    # Get all users except current user
    users = User.query.filter(User.id != current_user.id).all()
    # Get users with similar majors
    similar_major_users = User.query.filter(
        User.major == current_user.major,
        User.id != current_user.id
    ).all() if current_user.major else []
    
    return render_template('network.html', 
                         users=users,
                         similar_major_users=similar_major_users)

@app.route('/chat/<username>')
@login_required
def chat(username):
    # Temporary logic for demo user RahulSharma
    if username == 'RahulSharma':
        # Create a temporary user object for RahulSharma
        user = type('User', (object,), {
            'id': 101,
            'username': 'RahulSharma',
            'major': 'Computer Science',
            'bio': 'Interested in AI and machine learning.',
            'profile_picture': 'https://ui-avatars.com/api/?name=Rahul+Sharma&background=random',
            'interests': ['Programming', 'Research'],
            '__tablename__': 'user' # Needed for url_for if linking back to profile
        })()
        # Create temporary messages between current_user and RahulSharma
        messages = [
            type('Message', (object,), {'content': 'Hi Rahul!', 'sender': type('Sender', (object,), {'username': current_user.username})(), 'timestamp': datetime.utcnow() - timedelta(minutes=5)})(),
            type('Message', (object,), {'content': 'Hey {{ current_user.username }}! How are you doing?', 'sender': user, 'timestamp': datetime.utcnow() - timedelta(minutes=4)})(),
            type('Message', (object,), {'content': 'I am doing great, thanks! Just checking out the new dashboard.', 'sender': type('Sender', (object,), {'username': current_user.username})(), 'timestamp': datetime.utcnow() - timedelta(minutes=3)})(),
            type('Message', (object,), {'content': 'Awesome! Let me know if you find anyone interesting.', 'sender': user, 'timestamp': datetime.utcnow() - timedelta(minutes=2)})(),
        ]
        # Sort messages by timestamp (temporary objects, so manually sort)
        messages.sort(key=lambda msg: msg.timestamp)

    else:
        # Original logic to fetch user and messages from the database
        user = User.query.filter_by(username=username).first_or_404()
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == user.id)) |
            ((Message.sender_id == user.id) & (Message.recipient_id == current_user.id))
        ).order_by(Message.timestamp).all()

    return render_template('chat.html', user=user, messages=messages)

@app.route('/events')
@login_required
def events():
    # Get upcoming events
    upcoming_events = Event.query.filter(
        Event.start_time > datetime.utcnow()
    ).order_by(Event.start_time).all()
    
    # Get events created by the current user
    my_events = Event.query.filter_by(created_by=current_user.id).all()
    
    # Get events the user is attending
    attending_events = current_user.attending_events.all()
    
    return render_template('events.html',
                         upcoming_events=upcoming_events,
                         my_events=my_events,
                         attending_events=attending_events)

@app.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        
        event = Event(
            title=title,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            created_by=current_user.id
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!')
        return redirect(url_for('events'))
    
    return render_template('create_event.html')

@app.route('/events/<int:event_id>/attend', methods=['POST'])
@login_required
def attend_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event not in current_user.attending_events:
        current_user.attending_events.append(event)
        db.session.commit()
        flash('You are now attending this event!')
    return redirect(url_for('events'))

@app.route('/events/<int:event_id>/unattend', methods=['POST'])
@login_required
def unattend_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event in current_user.attending_events:
        current_user.attending_events.remove(event)
        db.session.commit()
        flash('You are no longer attending this event.')
    return redirect(url_for('events'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/blog')
def blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog.html', posts=posts)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog_post.html', post=post)

@app.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_blog_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        post = BlogPost(
            title=title,
            content=content,
            author_id=current_user.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Blog post created successfully!')
        return redirect(url_for('blog_post', post_id=post.id))
    
    return render_template('create_blog_post.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically send an email or store the message
        # For now, we'll just flash a success message
        flash('Thank you for your message! We will get back to you soon.')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', current_date=datetime.utcnow())

@app.route('/terms')
def terms():
    return render_template('terms.html', current_date=datetime.now(UTC))

@app.route('/cookies')
def cookies():
    return render_template('cookies.html', current_date=datetime.now(UTC))

# WebSocket events
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f"{current_user.username} has joined the room."}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f"{current_user.username} has left the room."}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = Message(
        content=data['message'],
        sender_id=current_user.id,
        recipient_id=data['recipient_id'],
        room=room
    )
    db.session.add(message)
    db.session.commit()
    
    emit('message', {
        'user': current_user.username,
        'message': data['message'],
        'timestamp': message.timestamp.strftime('%H:%M')
    }, room=room)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)  # (or "content" if you prefer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __init__(self, user_id, message, is_read=False):
         self.user_id = user_id
         self.message = message
         self.is_read = is_read

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True) 