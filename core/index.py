from libraries import start_time
from flask import render_template, Blueprint

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index():
    return render_template('index.html', start_time=start_time)