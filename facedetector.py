import face_recognition
from maskdetect import detect_and_predict_mask
import numpy as np
import cv2
import db

dbconnect = db.connect()

knownencodings = []
allmails = []

def faceencodingvalues(img):
	print("===============start=====================================================")
	imgload = face_recognition.load_image_file(img)
	imgload = cv2.cvtColor(imgload,cv2.COLOR_BGR2RGB)
	try:
		faceloc = face_recognition.face_locations(imgload)[0]  # (260, 825, 528, 557)
	except:
		return [],[]
	encodeimg = face_recognition.face_encodings(imgload)[0]
	# print("===============faceloc=====================================================")
	# print(faceloc)
	# print("==================encodeimg==================================================")
	# print(encodeimg)

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
		if mask > withoutmask:
			return "mask"
		else:
			return "withoutmask"

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
# def detect(img,maskdetected,facedetected):
# 	if maskdetected == False and facedetected == False:
# 		(locs, preds) = detect_and_predict_mask(img)
# 		for (box, pred) in zip(locs, preds):
# 			(startX, startY, endX, endY) = box
# 			(mask, withoutMask) = pred
# 			if mask > withoutMask:
# 				return "mask"
# 	elif maskdetected == False and facedetected == True:
# 		(locs, preds) = detect_and_predict_mask(img)
# 		for (box, pred) in zip(locs, preds):
# 			(startX, startY, endX, endY) = box
# 			(mask, withoutMask) = pred
# 			if mask > withoutMask:
# 				return "mask"
		# else:

		# label = "Mask" if mask > withoutMask else "No Mask"
		# color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
		# label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)
		# cv2.putText(frame, label, (startX, startY - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
		# cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

	# cv2.imshow('frame', frame)
	# if cv2.waitKey(1) & 0xFF == ord('q'):
	# 	break
	


# def detect(img):
# 	imgS = cv2.resize(img,(0,0),None,0.25,0.25)
# 	imgS = cv2.cvtColor(imgS,cv2.COLOR_BGR2RGB)
# 	facesS = face_recognition.face_locations(imgS)
# 	encodeS = face_recognition.face_encodings(imgS,facesS)

# 	for encodeFace,faceLoc in zip(encodeS,facesS):
# 		matches = face_recognition.compare_faces(knownencodings,encodeFace)
# 		faceDis = face_recognition.face_distance(knownencodings,encodeFace)
# 		matchindex = np.argmin(faceDis)
# 		# print("=======matchindex========================================")
# 		print(matchindex)
# 		# print(count)
# 		print(matches[matchindex])
# 		print(faceDis[matchindex])
# 		# if matches[matchindex] and count == matchindex and faceDis[matchindex]<0.6:
# 		if matches[matchindex] and faceDis[matchindex]<0.6:
# 			print("================detect=================================================================")
# 			ret,buffer = cv2.imencode('.jpg',img)
# 			frame = buffer.tobytes()
# 			return (frame,"YES")
# 	ret,buffer = cv2.imencode('.jpg',img)
# 	frame = buffer.tobytes()
# 	return (frame,"NO")