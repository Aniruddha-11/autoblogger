from flask import Flask
from flask_cors import CORS
from config import Config
from routes.keyword_routes import keyword_bp
from routes.scraping_routes import scraping_bp
from routes.image_routes import image_bp
from routes.blog_routes import blog_bp
from routes.batch_routes import batch_bp
from flask import Flask
from flask_cors import CORS
from config import Config  # Add this import

app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

# Register blueprints
app.register_blueprint(keyword_bp, url_prefix='/api')
app.register_blueprint(scraping_bp, url_prefix='/api')
app.register_blueprint(image_bp, url_prefix='/api')
app.register_blueprint(blog_bp, url_prefix='/api')
app.register_blueprint(batch_bp, url_prefix='/api')  # Add this line

@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "healthy"}, 200

if __name__ == '__main__':
    app.run(debug=True, port=Config.PORT)