import os
from audithunter import create_app, db, login_manager
from config import config

config_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=61337, ssl_context=("audithunter.cert.pem","audithunter.key.pem"))