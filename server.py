from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from more import getresponse, createlog
from waitress import serve
from datetime import datetime
import os
import threading
import time
import logging
from openai import OpenAI
from pathlib import Path
from werkzeug.utils import secure_filename


# Import our authentication modules
from config import Config
from models import db, User, Chat
from auth import auth

UPLOAD_FOLDER = './uploads/'

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f'Request: {request.method} {request.url} - IP: {request.remote_addr} - User-Agent: {request.headers.get("User-Agent", "Unknown")}')

@app.after_request
def log_response_info(response):
    logger.info(f'Response: {response.status_code} for {request.method} {request.url}')
    return response

# Initialize database
db.init_app(app)

# Create database tables if they don't exist
def init_database_on_startup():
    """Initialize database tables on startup if they don't exist"""
    with app.app_context():
        try:
            # First, check if database file exists (for SQLite)
            from pathlib import Path
            db_path = Path("moreai.db")
            
            if db_path.exists():
                print("📁 Database file found, checking tables...")
                try:
                    # Try to query the database to see if tables exist
                    User.query.first()
                    print("✅ Database tables already exist and are working")
                    
                    # Check if admin user exists
                    admin_user = User.query.filter_by(username='admin').first()
                    if admin_user:
                        print("✅ Admin user exists")
                    else:
                        print("👤 Creating admin user...")
                        admin = User(
                            username='admin',
                            is_admin=True,
                            is_active=True
                        )
                        admin.set_password('Admin123!')
                        db.session.add(admin)
                        db.session.commit()
                        print("✅ Admin user created (username: admin, password: Admin123!)")
                    
                except Exception as e:
                    print(f"⚠️  Database exists but tables may be corrupted: {e}")
                    print("🔄 Recreating database tables...")
                    db.drop_all()
                    db.create_all()
                    create_admin_user()
                    
            else:
                print("🔄 Database file not found, creating new database...")
                db.create_all()
                create_admin_user()
                
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            print("🔄 Attempting to recreate database...")
            try:
                db.drop_all()
                db.create_all()
                create_admin_user()
                print("✅ Database recreated successfully")
            except Exception as e2:
                print(f"❌ Failed to recreate database: {e2}")
                raise e2

def create_admin_user():
    """Create admin user if it doesn't exist"""
    try:
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("👤 Creating admin user...")
            admin = User(
                username='admin',
                is_admin=True,
                is_active=True
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created (username: admin, password: Admin123!)")
        else:
            print("✅ Admin user already exists")
    except Exception as e:
        print(f"⚠️  Could not create admin user: {e}")

# Initialize database on startup
try:
    init_database_on_startup()
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    print("⚠️  The application will start but authentication may not work properly")
    print("💡 Try running 'python init_db.py' manually to troubleshoot")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        print(f"👤 User loader: Loaded user {user.username} (ID: {user.id})")
    else:
        print(f"❌ User loader: No user found for ID {user_id}")
    return user

# Register authentication blueprint
app.register_blueprint(auth, url_prefix='/auth')

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
speech_folder = Path(__file__).parent / "static" / "speech"
speech_folder.mkdir(parents=True, exist_ok=True)
uploads_folder = Path(__file__).parent / "uploads"
uploads_folder.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def midnight_checker():
    """Create daily logs for all users at midnight"""
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            try:
                # Get all users and create logs for their conversations
                users = User.query.all()
                for user in users:
                    # Get user's conversations from today
                    today_start = datetime(now.year, now.month, now.day)
                    user_chats = Chat.query.filter(
                        Chat.user_id == user.id,
                        Chat.timestamp >= today_start,
                        Chat.message_type.in_(['user', 'assistant'])
                    ).order_by(Chat.timestamp).all()
                    
                    if user_chats:
                        # Convert to conversation history format
                        conversation_history = []
                        for chat in user_chats:
                            conversation_history.append({
                                'message': chat.message,
                                'type': chat.message_type
                            })
                        
                        # Create log entry
                        createlog(user_id=user.id, conversation_history=conversation_history)
                
                print("✅ Daily logs created for all users")
            except Exception as e:
                print(f"❌ Error creating daily logs: {e}")
        
        time.sleep(60)

midnight_thread = threading.Thread(target=midnight_checker, daemon=True)
midnight_thread.start()


@app.route('/')
@app.route('/index')
def index():
    logger.info(f"Root route accessed - User authenticated: {current_user.is_authenticated}")
    # If user is logged in, redirect to chat to show their history
    if current_user.is_authenticated:
        logger.info(f"Redirecting authenticated user {current_user.username} to chat")
        return redirect(url_for('getresp'))
    
    logger.info("Serving index.html to unauthenticated user")
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/health')
def health_check():
    """Health check endpoint to verify database connectivity"""
    try:
        # Test database connection
        user_count = User.query.count()
        chat_count = Chat.query.count()
        session_count = UserSession.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'user_count': user_count,
            'chat_count': chat_count,
            'session_count': session_count,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/chat')
@login_required
def getresp():
    usertext = request.args.get('usertext')
    
    if usertext:
        # Check if this exact message was just sent (prevent duplicates)
        recent_message = Chat.query.filter_by(
            user_id=current_user.id,
            message=usertext,
            message_type='user'
        ).order_by(Chat.timestamp.desc()).first()
        
        # If the same message was sent within the last 30 seconds, don't process it
        if recent_message and (datetime.utcnow() - recent_message.timestamp).seconds < 30:
            print(f"Duplicate message detected, skipping: {usertext}")
        else:
            # Get user's previous conversation history (excluding the current message)
            previous_chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.timestamp).all()
            conversation_history = []
            for chat in previous_chats:
                conversation_history.append({
                    'message': chat.message,
                    'type': chat.message_type
                })
            
            # Store user message
            print(f"💾 Storing user message for: {current_user.username} (ID: {current_user.id})")
            user_chat = Chat(
                user_id=current_user.id,
                message=usertext,
                message_type='user'
            )
            db.session.add(user_chat)
            db.session.flush()  # Get the ID without committing
            
            # Get AI response with conversation history (excluding the current message)
            ai_response = getresponse(usertext, user_id=current_user.id, conversation_history=conversation_history, db_session=db.session)
            if ai_response:
                print(f"🤖 Storing AI response for: {current_user.username} (ID: {current_user.id})")
                ai_chat = Chat(
                    user_id=current_user.id,
                    message=ai_response,
                    message_type='assistant'
                )
                db.session.add(ai_chat)
            
            db.session.commit()
            print(f"✅ Messages committed to database for user: {current_user.username}")
        
        # Redirect to clear URL parameters and prevent resubmission on refresh
        from flask import redirect, url_for
        return redirect(url_for('getresp'))

    # Get user's chat history from database
    print(f"🔍 Loading chat history for user: {current_user.username} (ID: {current_user.id})")
    user_chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.timestamp).all()
    print(f"📊 Found {len(user_chats)} chat messages for user {current_user.username}")
    
    # Format chat history for display
    history = []
    for chat in user_chats:
        history.append({
            'message': chat.message,
            'type': chat.message_type,
            'timestamp': chat.timestamp.isoformat()
        })

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(history=history)

    return render_template("chat.html", history=history)


@app.route('/journal')
@login_required
def journal():
    # Get user's log entries from database
    user_logs = Chat.query.filter_by(
        user_id=current_user.id,
        message_type='log'
    ).order_by(Chat.timestamp.desc()).all()
    
    # Format logs for display
    journal_entries = []
    for log in user_logs:
        journal_entries.append({
            'content': log.message,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return render_template('journal.html', journal_entries=journal_entries)


@app.route('/morevoice')
@login_required
def morevoice():
    return render_template('morevoice.html')


@app.route('/tts')
@login_required
def tts():
    text = request.args.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    speech_file_path = speech_folder / "speech.mp3"
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        instructions="""Voice Affect:
Calm, composed, and deeply empathetic. A steady, reassuring presence that conveys safety and understanding. The voice should exude competence and emotional attunement, fostering trust and openness.
Tone:
Warm, nonjudgmental, and reflective. Sincere with gentle curiosity—never rushed or authoritative. A balance of professionalism and human connection, validating emotions while guiding insight.
Pacing:
Slow to moderate, allowing space for processing emotions and thoughts. Deliberate pauses after important reflections or questions to let words resonate. Slightly quicker when summarizing or transitioning to action steps, signaling structure and forward movement.
Emotions:
Empathic attunement (reflecting care and deep listening), gentle encouragement (supporting growth without pressure), and grounded stability (a steady anchor in distress).
Pronunciation:
Clear and measured, with careful articulation to ensure key therapeutic phrases land effectively (e.g., "How does that feel for you?" or "Let’s explore that together."). Softened inflection when addressing sensitive topics.
Pauses:
Before reflective statements to invite contemplation.
After emotionally charged disclosures to honor the weight of the moment.
Between questions to avoid overwhelming the client.
"""
    ) as response:
        response.stream_to_file(speech_file_path)

    return send_file(speech_file_path, mimetype="audio/mpeg")


@app.route('/stt', methods=['POST'])
@login_required
def stt():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    audio_file = request.files['audio']
    audio_path=os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(audio_file.filename))
    audio_file.save(audio_path)
    with open(audio_path, "rb") as af:
        transcription = client.audio.transcriptions.create(
            file=af,
            model="whisper-1"
        )
    text = transcription.text
    return jsonify({"text": text})


if __name__ == "__main__":
    print("🚀 Starting MoreAI server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🔍 Health check: http://localhost:8000/health")
    print("🔐 Admin login: admin / Admin123!")
    print("=" * 50)
    serve(app, host="0.0.0.0", port=8000)