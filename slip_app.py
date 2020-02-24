from dotenv import load_dotenv

from flask_app import create_app

load_dotenv()
app = create_app()
