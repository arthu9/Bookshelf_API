import datetime
import random
from itsdangerous import TimestampSigner
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from sqlalchemy import *
from werkzeug import secure_filename
from engine_cloudinary import *


img_folder = 'app/static/uploads/img/'
audio_folder = 'app/static/uploads/audio/'
profile_folder = 'app/static/uploads/profile/'

img_folder_alter = '/static/uploads/img/'
audio_folder_alter = '/static/uploads/audio/'
profile_folder_alter = '/static/uploads/profile/'

app_dump = 'app/dumps'

available_extension = set(['png', 'jpg', 'PNG', 'JPG', 'mp3', 'm4a', 'flac', 'aac'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in available_extension
