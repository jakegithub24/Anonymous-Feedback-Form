import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Database setup
def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'feedback.db'))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_quality INTEGER NOT NULL,
            clarity INTEGER NOT NULL,
            engagement INTEGER NOT NULL,
            satisfaction INTEGER NOT NULL,
            apply_likelihood INTEGER NOT NULL,
            most_valuable TEXT NOT NULL,
            improvements TEXT NOT NULL,
            recommend TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_id INTEGER,
            status TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feedback_id) REFERENCES feedback (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'feedback.db'))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Render the main feedback form"""
    return render_template('index.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Handle form submission with validation and error handling"""
    try:
        # Step 1: Validate all required fields are present
        required_fields = [
            'content_quality', 'clarity', 'engagement',
            'satisfaction', 'apply_likelihood',
            'most_valuable', 'improvements', 'recommend'
        ]
        
        for field in required_fields:
            if field not in request.form or not request.form[field].strip():
                return jsonify({
                    'success': False,
                    'message': f'Missing or empty field: {field}'
                }), 400
        
        # Step 2: Validate rating values (1-5)
        rating_fields = ['content_quality', 'clarity', 'engagement', 'satisfaction', 'apply_likelihood']
        for field in rating_fields:
            value = int(request.form[field])
            if value < 1 or value > 5:
                return jsonify({
                    'success': False,
                    'message': f'{field} must be between 1 and 5'
                }), 400
        
        # Step 3: Validate text lengths
        most_valuable = request.form['most_valuable'].strip()
        improvements = request.form['improvements'].strip()
        
        if len(most_valuable) > 2000:  # ~250 words * 8 chars/word
            return jsonify({
                'success': False,
                'message': 'Most valuable section exceeds maximum length'
            }), 400
        
        if len(improvements) > 2000:
            return jsonify({
                'success': False,
                'message': 'Improvements section exceeds maximum length'
            }), 400
        
        # Step 4: Prepare data for insertion
        feedback_data = {
            'content_quality': int(request.form['content_quality']),
            'clarity': int(request.form['clarity']),
            'engagement': int(request.form['engagement']),
            'satisfaction': int(request.form['satisfaction']),
            'apply_likelihood': int(request.form['apply_likelihood']),
            'most_valuable': most_valuable,
            'improvements': improvements,
            'recommend': request.form['recommend'],
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        # Step 5: Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO feedback 
                (content_quality, clarity, engagement, satisfaction, apply_likelihood,
                 most_valuable, improvements, recommend, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feedback_data['content_quality'],
                feedback_data['clarity'],
                feedback_data['engagement'],
                feedback_data['satisfaction'],
                feedback_data['apply_likelihood'],
                feedback_data['most_valuable'],
                feedback_data['improvements'],
                feedback_data['recommend'],
                feedback_data['ip_address'],
                feedback_data['user_agent']
            ))
            
            feedback_id = cursor.lastrowid
            
            # Log successful submission
            cursor.execute('''
                INSERT INTO submissions_log (feedback_id, status)
                VALUES (?, ?)
            ''', (feedback_id, 'success'))
            
            conn.commit()
            
            # Step 6: Send email notification (optional)
            try:
                if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
                    send_notification_email(feedback_data, feedback_id)
            except Exception as email_error:
                # Log email error but don't fail the submission
                cursor.execute('''
                    INSERT INTO submissions_log (feedback_id, status, error_message)
                    VALUES (?, ?, ?)
                ''', (feedback_id, 'email_failed', str(email_error)))
                conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully!',
                'redirect': url_for('success')
            })
            
        except sqlite3.Error as e:
            conn.rollback()
            cursor.execute('''
                INSERT INTO submissions_log (status, error_message)
                VALUES (?, ?)
            ''', ('database_error', str(e)))
            conn.commit()
            return jsonify({
                'success': False,
                'message': 'Database error occurred. Please try again.'
            }), 500
            
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500

def send_notification_email(feedback_data, feedback_id):
    """Send email notification about new feedback"""
    msg = Message(
        subject=f'New Feedback Received - ID: {feedback_id}',
        recipients=[app.config['MAIL_USERNAME']]  # Send to yourself
    )
    
    # Create email body
    body = f"""
    New feedback submission received:
    
    Submission ID: {feedback_id}
    Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Ratings:
    - Content Quality: {feedback_data['content_quality']}/5
    - Clarity: {feedback_data['clarity']}/5
    - Engagement: {feedback_data['engagement']}/5
    - Overall Satisfaction: {feedback_data['satisfaction']}/5
    - Likelihood to Apply: {feedback_data['apply_likelihood']}/5
    
    Most Valuable: {feedback_data['most_valuable'][:100]}...
    
    Improvements Suggested: {feedback_data['improvements'][:100]}...
    
    Would Recommend: {feedback_data['recommend']}
    """
    
    msg.body = body
    mail.send(msg)

@app.route('/success')
def success():
    """Show success page after submission"""
    return render_template('success.html')

@app.route('/admin')
def admin():
    """Admin view to see all feedback (optional password protection)"""
    conn = get_db_connection()
    feedback = conn.execute('SELECT * FROM feedback ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('admin.html', feedback=feedback)

@app.route('/api/feedback/stats')
def feedback_stats():
    """API endpoint to get feedback statistics"""
    conn = get_db_connection()
    
    # Get total submissions
    total = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
    
    # Get average ratings
    avg_ratings = conn.execute('''
        SELECT 
            AVG(content_quality) as avg_content,
            AVG(clarity) as avg_clarity,
            AVG(engagement) as avg_engagement,
            AVG(satisfaction) as avg_satisfaction,
            AVG(apply_likelihood) as avg_apply
        FROM feedback
    ''').fetchone()
    
    # Get recommendation stats
    recommend_stats = conn.execute('''
        SELECT recommend, COUNT(*) as count
        FROM feedback
        GROUP BY recommend
    ''').fetchall()
    
    conn.close()
    
    stats = {
        'total_submissions': total,
        'average_ratings': {
            'content_quality': round(avg_ratings['avg_content'], 2),
            'clarity': round(avg_ratings['avg_clarity'], 2),
            'engagement': round(avg_ratings['avg_engagement'], 2),
            'satisfaction': round(avg_ratings['avg_satisfaction'], 2),
            'apply_likelihood': round(avg_ratings['avg_apply'], 2)
        },
        'recommendations': {
            row['recommend']: row['count'] for row in recommend_stats
        }
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
