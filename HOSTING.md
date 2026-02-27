# 🌐 Hosting Guide: RigMaster AI

This guide explains how to take your project from local development to a live hosted environment.

## 1. Prerequisites
- **Python Hosting**: Platforms like Render, Railway.app, Heroku, or a VPS (DigitalOcean/Linode).
- **Database**: A hosted MongoDB instance. We recommend **MongoDB Atlas** (Free Tier available).
- **Environment**: Access to set environment variables.

## 2. Environment Variables (.env)
Ensure your hosting provider has the following variables set:
| Variable | Description | Example |
| :--- | :--- | :--- |
| `MONGO_URI` | Your MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/...` |
| `SECRET_KEY` | A long random string for sessions | `super-secret-random-123` |
| `GEMINI_API_KEY` | Your Google AI SDK Key | `AIzaSy...` |
| `SMTP_SERVER` | (Optional) For email notifications | `smtp.gmail.com` |
| `SMTP_PORT` | (Optional) SMTP Port | `587` |

## 3. Database Initialization
Once you have your `MONGO_URI` set, run the following command **once** in the hosted terminal to set up indexes and migrate your data:

```bash
python setup_prod_db.py
```

## 4. Production Web Server
Locally, you use `app.run()`. In production, you should use a production-grade WSGI server like **Gunicorn**:

**Install Gunicorn:**
```bash
pip install gunicorn
```

**Start Command:**
```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

## 5. Deployment Steps (Railway/Render)
1.  Connect your GitHub repository to the hosting platform.
2.  Add the environment variables listed in step 2.
3.  Set the start command to: `gunicorn --bind 0.0.0.0:$PORT app:app`
4.  If the platform allows a build command, use: `pip install -r requirements.txt && python setup_prod_db.py`

---
### 💡 Pro Tip
If you already have 28,000 components in your local database and want to move them all to the cloud, use the **MongoDB Database Tools**:
`mongodump --db rigmaster` followed by `mongorestore --uri="YOUR_ATLAS_URI" dump/`
