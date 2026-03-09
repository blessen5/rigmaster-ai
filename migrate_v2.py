import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load keys from current .env
load_dotenv()

# Atlas URI
MONGO_URI = 'mongodb+srv://rigmaster_user:MMdm2NPf8J737U8D@cluster0.99f5zmr.mongodb.net/rigmaster?retryWrites=true&w=majority&appName=Cluster0'

def migrate_keys():
    logs = []
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['rigmaster']
        settings = db['settings']
        
        # Test connection
        client.admin.command('ping')
        logs.append("Atlas connected successfully.")
        
        # Keys to migrate from .env
        keys_to_migrate = {
            'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'MISTRAL_API_KEY': os.getenv('MISTRAL_API_KEY'),
            'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY'),
            'HF_API_KEY': os.getenv('HF_API_KEY'),
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
            'COHERE_API_KEY': os.getenv('COHERE_API_KEY'),
            'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
            'SMTP_SERVER': os.getenv('SMTP_SERVER'),
            'SMTP_PORT': os.getenv('SMTP_PORT'),
            'SMTP_EMAIL': os.getenv('SMTP_EMAIL')
        }
        
        logs.append("Starting migration...")
        for key, value in keys_to_migrate.items():
            if value:
                res = settings.update_one(
                    {'key': key},
                    {'$set': {'value': value}},
                    upsert=True
                )
                status = "Created" if res.upserted_id else "Updated"
                logs.append(f"✓ {status} {key}")
            else:
                logs.append(f"⚠ Skipping {key} (not found in .env)")
        
        # Final count check
        count = settings.count_documents({})
        logs.append(f"Migration finished. Now have {count} settings documents.")
        
    except Exception as e:
        logs.append(f"Migration Error: {e}")
        
    print("\n".join(logs))
    with open('migration_status.log', 'w') as f:
        f.write("\n".join(logs))

if __name__ == "__main__":
    migrate_keys()
