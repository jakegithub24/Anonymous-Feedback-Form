import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv
import json

# optional dependencies that enable sharing via ngrok and QR codes
try:
    from pyngrok import ngrok
except ImportError:
    ngrok = None

import io
import base64
import qrcode

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# will be populated by ngrok->public url if available
app.config['NGROK_URL'] = None

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

import re
import yaml

# Database setup
def init_db():
    """Initialize the database with required tables.  The feedback table stores
    all responses as JSON in the `data` column; legacy columns are left in place
    for compatibility but are no longer populated by new submissions.
    """
    conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'feedback.db'))
    cursor = conn.cursor()

    # create or update feedback table (id + data are mandatory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # inspect existing columns and add any that are missing
    cursor.execute("PRAGMA table_info(feedback)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    if 'data' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE feedback ADD COLUMN data TEXT")
        except sqlite3.OperationalError:
            pass

    # also keep legacy columns if needed
    for col_def in [
        ('content_quality','INTEGER'),
        ('clarity','INTEGER'),
        ('engagement','INTEGER'),
        ('satisfaction','INTEGER'),
        ('apply_likelihood','INTEGER'),
        ('most_valuable','TEXT'),
        ('improvements','TEXT'),
        ('recommend','TEXT')
    ]:
        name, _type = col_def
        if name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE feedback ADD COLUMN {name} {_type}")
            except sqlite3.OperationalError:
                pass

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()


def load_form_definition():
    """Read `form.md` in the project root and return a parsed question list.
    The file should contain a YAML code block describing an array of
    question objects. Each object must have a `type` (rating, textarea, radio),
    `name` and `label`. Additional keys like `maxlength`, `options`,
    `placeholder`, etc. are supported.
    """
    path = os.path.join(os.path.dirname(__file__), 'form.md')
    if not os.path.exists(path):
        return {'rating': [], 'text': [], 'choice': []}

    text = open(path, 'r', encoding='utf-8').read()
    # extract first yaml fenced block
    m = re.search(r"```yaml(.*?)```", text, re.DOTALL)
    if not m:
        return {'rating': [], 'text': [], 'choice': []}
    try:
        questions = yaml.safe_load(m.group(1)) or []
    except Exception as e:
        app.logger.error('Failed to parse form.md: %s', e)
        questions = []

    result = {'rating': [], 'text': [], 'choice': []}
    for q in questions:
        t = q.get('type')
        if t == 'rating':
            result['rating'].append(q)
        elif t in ('text', 'textarea'):
            result['text'].append(q)
        elif t == 'radio':
            result['choice'].append(q)
    return result

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'feedback.db'))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Render the main feedback form, generating fields from `form.md`."""
    form_def = load_form_definition()
    return render_template('index.html', form=form_def)

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Handle form submission with validation and error handling"""
    try:
        # load form structure to know which fields we expect
        form_def = load_form_definition()
        all_questions = form_def['rating'] + form_def['text'] + form_def['choice']
        required_fields = [q['name'] for q in all_questions]

        for field in required_fields:
            if field not in request.form or not request.form[field].strip():
                return jsonify({
                    'success': False,
                    'message': f'Missing or empty field: {field}'
                }), 400

        # validate rating values
        for q in form_def['rating']:
            try:
                value = int(request.form[q['name']])
            except ValueError:
                return jsonify({'success': False, 'message': f"{q['name']} must be an integer"}), 400
            if value < 1 or value > 5:
                return jsonify({'success': False, 'message': f"{q['name']} must be between 1 and 5"}), 400

        # validate text lengths if maxlength provided
        for q in form_def['text']:
            val = request.form[q['name']].strip()
            maxlen = q.get('maxlength')
            if maxlen and len(val) > maxlen:
                return jsonify({'success': False,
                                'message': f"{q['name']} exceeds maximum length"}), 400

        # Step 4: Prepare data for insertion (keep original types where appropriate)
        feedback_data = {}
        for q in all_questions:
            name = q['name']
            if q['type'] == 'rating':
                feedback_data[name] = int(request.form[name])
            else:
                feedback_data[name] = request.form[name].strip()
        
        # Step 5: Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # supply legacy columns (marked NOT NULL) with defaults to avoid constraint
            legacy_fields = [
                'content_quality','clarity','engagement',
                'satisfaction','apply_likelihood',
                'most_valuable','improvements','recommend'
            ]
            legacy_values = []
            for lf in legacy_fields:
                if lf in feedback_data:
                    legacy_values.append(feedback_data[lf])
                else:
                    # numeric fields get 0, text fields empty
                    if lf in ['content_quality','clarity','engagement','satisfaction','apply_likelihood']:
                        legacy_values.append(0)
                    else:
                        legacy_values.append('')

            cursor.execute('''
                INSERT INTO feedback (data, content_quality, clarity, engagement, satisfaction, apply_likelihood,
                                       most_valuable, improvements, recommend)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (json.dumps(feedback_data),) + tuple(legacy_values))
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

def generate_qr_code(url: str) -> str:
    """Return a base64-encoded PNG of a QR code for the given url.
    If something goes wrong (missing PIL, etc.) an empty string is returned and
    the error is logged so the rest of the application can continue.
    """
    try:
        qr = qrcode.make(url)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception as err:  # pylint: disable=broad-except
        app.logger.error("QR code generation failed: %s", err)
        # return empty string so templates can fallback to plain link
        return ""


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


@app.route('/share')
def share():
    """Page showing the public link/QR code so people can scan and fill the form.
    If the QR image could not be generated it will still render the link only.
    """
    # prefer the ngrok URL, fall back to local address
    url = app.config.get('NGROK_URL') or request.url_root
    qr = generate_qr_code(url)
    return render_template('share.html', url=url, qr_code=qr)


@app.before_request
def ensure_ngrok():
    """Start ngrok tunnel the first time the application handles a request."""
    # run only once and only if ngrok is available and not disabled via env var
    if (app.config.get('NGROK_URL') or ngrok is None or
            app.config.get('NGROK_ATTEMPTED') or
            os.getenv('USE_NGROK', 'True').lower() not in ('1', 'true', 'yes')):
        return
    app.config['NGROK_ATTEMPTED'] = True
    try:
        port = int(os.getenv('PORT', 5000))
        public_url = ngrok.connect(port).public_url
        app.config['NGROK_URL'] = public_url
        print(f"* ngrok tunnel opened at {public_url}")
    except Exception as e:
        # record an error once, but don't spam every request
        print(f"ngrok could not start: {e}")

@app.route('/admin')
def admin():
    """Admin view to see all feedback (optional password protection)"""
    conn = get_db_connection()
    feedback = conn.execute('SELECT * FROM feedback ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('admin.html', feedback=feedback)


@app.route('/api/feedback/<int:fid>')
def feedback_detail(fid):
    """Return the responses for a single submission as JSON."""
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM feedback WHERE id = ?', (fid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'not found'}), 404
    data = {}
    if row['data']:
        try:
            data = json.loads(row['data'])
        except Exception:
            data = {}
    else:
        # fall back to legacy columns
        for col in ['content_quality','clarity','engagement','satisfaction','apply_likelihood','most_valuable','improvements','recommend']:
            data[col] = row[col]
    return jsonify(data)

@app.route('/api/feedback/stats')
def feedback_stats():
    """API endpoint to get feedback statistics based on JSON responses."""
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
    rows = conn.execute('SELECT data FROM feedback').fetchall()
    conn.close()

    rating_sums = {}
    rating_counts = {}
    categorical = {}
    for r in rows:
        try:
            d = json.loads(r['data'])
        except Exception:
            continue
        for k, v in d.items():
            if isinstance(v, int) or (isinstance(v, str) and v.isdigit()):
                iv = int(v)
                rating_sums[k] = rating_sums.get(k, 0) + iv
                rating_counts[k] = rating_counts.get(k, 0) + 1
            else:
                categorical.setdefault(k, {})
                categorical[k][v] = categorical[k].get(v, 0) + 1

    avg_ratings = {k: round(rating_sums[k] / rating_counts[k], 2)
                   for k in rating_sums}

    # compatibility: recommendations key if field named "recommend" exists
    recommend_stats = categorical.get('recommend', {})

    stats = {
        'total_submissions': total,
        'average_ratings': avg_ratings,
        'categorical': categorical,
        'recommendations': recommend_stats
    }
    return jsonify(stats)

if __name__ == '__main__':
    # when running locally, try to start ngrok tunnel so external users can access
    if ngrok is not None:
        try:
            port = int(os.getenv('PORT', 5000))
            public_url = ngrok.connect(port).public_url
            app.config['NGROK_URL'] = public_url
            print(f"* ngrok tunnel opened at {public_url}")
        except Exception as e:
            print(f"ngrok could not start: {e}")

    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
