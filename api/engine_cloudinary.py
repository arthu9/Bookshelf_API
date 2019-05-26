import os
import cloudinary
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from controller import *

import shutil
from werkzeug import secure_filename
from app import db
from models import *

#the idea is that the cloudinary upload() function might not be able to find the file, so to be safe
#the file must be temporarily save somewhere inside the app folder and then be the one for the upload function
#then after the upload is successful, the temporary directory that was made will be remove from the app folder


def cloudinary_upload(acc_id, img_type, file, tempid, allowed_file, curr_folder, modelClass):
	cloud = cloudinary.config(
		cloud_name = 'dal7ygjnn',
		api_key = '244339543685643',
		api_secret = 'RPexuXeKVA5vxXJoO6_w7LcY7NI'
	)

	#to handle files that are not image by  default
	options = {"resource_type":"raw"}

	file_rename = ""
	msg = "not ok"
	result = upload(filename, **options)
	print(result)
	# if file and allowed_file(file.filename):
	# 	#we need to secure the filename first
	# 	filename = secure_filename(file.filename)
	

	# 	#make a current path
	# 	curr_path = curr_folder+'/'+str(tempid)

	# 	#check that path
	# 	if os.path.isdir(curr_path)==False:
	# 		os.makedirs(curr_path)

	# 	#save the file somewhere on our app
	# 	file.save(os.path.join(curr_path, filename))

	# 	#the upload function - upload(file, **options)
	# 	uploading = upload(curr_path+'/'+filename, **options)
		

	

	# 	exist = Images.query.filter_by(acc_id = acc_id).filter_by(story_id = story_id).first()

	# 	if exist:
			
	# 		exist.img = uploading['url']
	# 	else:
	# 		instance_ = modelClass(acc_id, img_type, story_id, img = uploading['url'],)
	# 		db.session.add(instance_)
			
	# 	db.session.commit()
	# 	msg = "ok"
	# 	#remove the directory we have created
	# 	shutil.rmtree(curr_path)

	# 	#returns the cloudinary url and msg
	# 	return  msg
	# return None, msg