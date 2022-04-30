import face_recognition
from maskdetect import detect_and_predict_mask
import numpy as np
import cv2
import db

dbconnect = db.connect()

knownencodings = []
allmails = []

def faceencodingvalues(img):
	imgload = face_recognition.load_image_file(img)
	imgload = cv2.cvtColor(imgload,cv2.COLOR_BGR2RGB)
	try:
		faceloc = face_recognition.face_locations(imgload)[0]  # (260, 825, 528, 557)
	except:
		return [],[]
	encodeimg = face_recognition.face_encodings(imgload)[0]

	return (encodeimg,faceloc)

def predata():
	encodinglist = []
	emaillist = []
	q = "select email,encodings from tarpusers"
	result = db.select(q)
	for i in result:
		emaillist.append(i[0])
		encodinglist.append(np.array(eval(i[1])))
	global knownencodings,allmails
	knownencodings = encodinglist
	allmails = emaillist

def detectmask(img):
	(locs,preds) = detect_and_predict_mask(img)
	for (box,pred) in zip(locs,preds):
		(mask,withoutmask) = pred
		if mask > withoutmask:return ("mask",box,pred)
		else:return ("withoutmask",box,pred)

def detectface(img):
	imgS = cv2.resize(img,(0,0),None,0.25,0.25)
	imgS = cv2.cvtColor(imgS,cv2.COLOR_BGR2RGB)
	facesS = face_recognition.face_locations(imgS)
	encodeS = face_recognition.face_encodings(imgS,facesS)

	for encodeFace,faceLoc in zip(encodeS,facesS):
		matches = face_recognition.compare_faces(knownencodings,encodeFace)
		faceDis = face_recognition.face_distance(knownencodings,encodeFace)
		matchindex = np.argmin(faceDis)
		if faceDis[matchindex]<0.6:
			return allmails[matchindex]