# WhatsApp Chat Analyzer - Flask Web Application

This is a Flask web application that converts your Streamlit WhatsApp Chat Analyzer into a full web application with a beautiful UI.

## Features

- Upload WhatsApp chat export files (.txt)
- Analyze chat statistics and visualize data
- View activity heatmaps, timelines, and word clouds
- Filter analysis by user
- Beautiful dark sidebar with green accents
- Responsive design

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the `stop_hinglish.txt` file in the project directory (for stopword filtering)

## Running the Application

1. Start the Flask server:
```bash
python flask_app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Upload your WhatsApp chat export file and start analyzing!

## Project Structure

```
.
├── flask_app.py          # Main Flask application
├── backhand.py           # Analysis functions (from Streamlit app)
├── preprocessor.py       # Data preprocessing
├── stop_hinglish.txt     # Stopwords file
├── requirements.txt      # Python dependencies
├── templates/
│   ├── index.html       # Upload page
│   └── results.html     # Results page
└── static/
    ├── css/
    │   └── style.css    # Stylesheet
    └── images/          # Generated visualization images
```

## Notes

- The application uses `kaleido` for generating plotly chart images. If you encounter issues with image generation, make sure kaleido is installed: `pip install kaleido`
- Chat files are processed in-memory and stored in the session
- Generated visualization images are stored in `static/images/`
- The app runs in debug mode by default (change for production)

## Features from Streamlit App

All features from your original Streamlit app are included:
- Top Statistics (Messages, Words, Media, Links)
- Most Busy Person (for Overall view)
- Monthly Timeline
- Daily Timeline
- Activity Map (Busy Day & Month)
- Active Hours Chart
- Chat Streak Analysis
- Wordcloud
- Most Common Words
- Emoji Analysis
- User Statistics

Enjoy analyzing your WhatsApp chats! 📊

