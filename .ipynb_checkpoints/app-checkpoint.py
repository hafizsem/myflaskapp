from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, this app is running on Render!"

# health check for uptime robot
@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run()
