# Training Feedback Collection System

A modern, responsive Flask web application for collecting and analyzing training feedback with beautiful UI/UX and smooth animations.

## Features

- **Multi-step Form**: Intuitive 3-step feedback collection process
- **Real-time Validation**: Client-side validation with visual feedback
- **Responsive Design**: Mobile-first design with Bootstrap 5
- **Rating System**: Interactive star rating system
- **Email Notifications**: Automatic email alerts on new submissions
- **Analytics Dashboard**: Real-time statistics and charts
- **Database Storage**: SQLite3 database with proper schema
- **Smooth Animations**: CSS transitions and animations throughout
- **Accessibility**: WCAG compliant with keyboard navigation support

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Bootstrap 5, Custom CSS, Google Fonts (Poppins)
- **Icons**: FontAwesome 6
- **Database**: SQLite3
- **Email**: Flask-Mail
- **Charts**: Chart.js (for analytics)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/jakegithub24/Anonymous-Feedback-Form.git
cd Anonymous-Feedback-Form
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip3 install -r requirements.txt # On Windows: pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and update with your configuration:
```bash
cp .env.example .env
```

Edit `.env` file:
```env
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True
DATABASE_PATH=feedback.db

# Email configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### 5. Initialize the database
The database will be automatically initialized when you first run the application.

## Usage

### Running the Application
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

### Application Structure
```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── static/
│   ├── css/
│   │   └── style.css    # Custom styles
│   └── js/
│       └── script.js    # Client-side JavaScript
└── templates/
    ├── base.html        # Base template
    ├── index.html       # Main feedback form
    ├── success.html     # Success page
    └── admin.html       # Analytics dashboard
```

## Testing in 5 Steps

### Step 1: Database Initialization Test
1. Run the application
2. Check that `feedback.db` is created in the project root
3. Verify tables are created correctly:
   ```sql
   .tables
   .schema feedback
   ```

### Step 2: Form Validation Test
1. Navigate to the home page
2. Try submitting without filling any fields
3. Verify validation errors appear
4. Test character limits on text areas
5. Verify star ratings work correctly

### Step 3: Form Submission Test
1. Fill all required fields
2. Submit the form
3. Verify success message appears
4. Check database for the new entry:
   ```sql
   SELECT * FROM feedback ORDER BY id DESC LIMIT 1;
   ```

### Step 4: Email Notification Test
1. Configure email in `.env`
2. Submit a feedback form
3. Check your email for the notification
4. Verify email content is correct

### Step 5: Analytics Dashboard Test
1. Submit multiple feedback forms with different ratings
2. Navigate to `/admin`
3. Verify statistics update correctly
4. Test chart rendering
5. Check responsive design on different screen sizes

## API Endpoints

- `GET /` - Main feedback form
- `POST /submit-feedback` - Submit feedback
- `GET /success` - Success page
- `GET /admin` - Analytics dashboard
- `GET /api/feedback/stats` - JSON statistics

## Form Fields

1. **Quality of the content** - Rating (1-5)
2. **Clarity of explanations** - Rating (1-5)
3. **Engagement level of visuals** - Rating (1-5)
4. **Overall satisfaction** - Rating (1-5)
5. **What did you find most valuable?** - Text (max 250 words)
6. **What improvements would you suggest?** - Text (max 250 words)
7. **Would you recommend this training to others?** - Yes/No
8. **How likely are you to apply what you learned?** - Rating (1-5)

## Security Features

- CSRF protection (via Flask-WTF if extended)
- Input validation and sanitization
- SQL injection prevention
- Rate limiting (can be added)
- Environment-based configuration

## Performance Optimizations

- Database connection pooling
- Static file caching
- Minified assets (production)
- Lazy loading for images
- Debounced resize events

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+
- Mobile browsers (iOS/Android)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests if applicable
5. Submit a pull request

## License

AGPL v3.0 - See [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the GitHub Issues page.

## Testing Instructions

Follow these 5 steps to test the application:

### Step 1: Initial Setup Test
1. Install requirements: `pip3 install -r requirements.txt`
2. Run the app: `python3 app.py`
3. Verify the database is created: `ls -la feedback.db`
4. Check the application loads at `http://localhost:5000`

### Step 2: Form Functionality Test
1. Test star rating interactions
2. Verify character counters work
3. Test form validation (try submitting empty form)
4. Test section navigation (Next/Previous buttons)

### Step 3: Database Test
1. Submit a complete feedback form
2. Check database: `sqlite3 feedback.db "SELECT * FROM feedback;"`
3. Verify all fields are saved correctly
4. Check the submissions_log table for entries

### Step 4: Email Test (Optional)
1. Configure email in `.env` file
2. Submit a feedback form
3. Check your email inbox for notification
4. Verify email content matches submitted data

### Step 5: Analytics Test
1. Submit multiple feedback forms with different ratings
2. Visit `/admin` to view analytics
3. Verify charts render correctly
4. Test responsive design on different screen sizes
5. Check that statistics update in real-time

## Additional Features Implemented:

1. **Multi-step Form**: Better UX with progress indication
2. **Real-time Validation**: Immediate feedback for users
3. **Character Counters**: For text areas with limits
4. **Success Animations**: Visual confirmation of submission
5. **Analytics Dashboard**: With Chart.js visualizations
6. **Email Notifications**: Optional admin notifications
7. **Responsive Design**: Works on all device sizes
8. **Accessibility**: Keyboard navigation, ARIA labels
9. **Error Handling**: Graceful error recovery
10. **Loading States**: Visual feedback during submission
11. **Print Styles**: Form can be printed
12. **Dark Mode Support**: Respects system preferences
