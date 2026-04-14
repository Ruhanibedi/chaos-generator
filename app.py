from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Chaos Engineering Platform - Target App v1'

@app.route('/health')
def health():
    return f'Chaos Target Running on pod: {os.environ.get("HOSTNAME", "unknown")}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
