import cv2
from flask import Flask, Response, render_template, request, redirect, session, url_for, flash, jsonify
from flask_mail import Mail, Message
from numpy import diff
from werkzeug.utils import secure_filename
from facedetector import detectmask, detectface, faceencodingvalues, predata
import db
import os
import cv2
import datetime



app = Flask(__name__)
mail= Mail(app)
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.getenv('SECRET_KEY')

maskdetected = False
facedetected = False

dbconnect = db.connect()

@app.route("/")
@app.route("/home")
def home():
	predata()
	global maskdetected
	global facedetected
	maskdetected,facedetected = False, False
	return render_template("index.html")


# ============================================================================================================

cap = cv2.VideoCapture(0)
def gen_frames():
	global cap,maskdetected,facedetected
	while True:
		if maskdetected == "wait" and facedetected == "wait":
			continue
		sucess,img = cap.read()
		if facedetected == False:
			ans = detectface(img)
			if ans: facedetected = ans
			ret,buffer=cv2.imencode('.jpg',img)
		elif maskdetected == False:
			ans,box,pred = detectmask(img)
			if ans == "mask":maskdetected = True
			(startX, startY, endX, endY) = box
			color = (0, 255, 0) if ans == "mask" else (0, 0, 255)
			(mask, withoutMask) = pred
			cv2.putText(img, ans, (startX, startY - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
			cv2.rectangle(img, (startX, startY), (endX, endY), color, 2)
			ret,buffer=cv2.imencode('.jpg',img)

		frame=buffer.tobytes()
		yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route("/video_feed")
def video_feed():
	return Response(gen_frames(),
					mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/recorded')
def recorded():
	return jsonify({"mask":maskdetected, "face":facedetected})

@app.route('/recorddone', methods = ['POST', 'GET'])
def recorddone():
	print("recorddone")
	global maskdetected
	global facedetected
	ans = db.select("SELECT inside,fine FROM tarpusers WHERE email = '"+facedetected+"'")
	inside,fine = ans[0]
	if inside == "YES":
		now = datetime.datetime.now()
		now = now.strftime("%Y-%m-%d %H:%M:%S")
		db.insert("UPDATE tarpusers SET inside = '"+ now +"' WHERE email = '"+facedetected+"'")
	else:
		diff = datetime.datetime.now() - datetime.datetime.strptime(inside, "%Y-%m-%d %H:%M:%S")
		days, seconds = diff.days, diff.seconds
		hours = days * 24 + seconds // 3600
		if hours > 3:
			fine = fine + (hours - 3) * 10
			db.insert("UPDATE tarpusers SET fine = '"+ str(fine) +"', inside = 'YES'  WHERE email = '"+facedetected+"'")
		else:db.insert("UPDATE tarpusers SET inside = 'YES' WHERE email = '"+facedetected+"'")
	# cap.release()
	cv2.destroyAllWindows()
	x = facedetected
	maskdetected,facedetected = "wait", "wait"
	return render_template("redirect.html", email = x,fine = fine)
	# return redirect(url_for('redirect'))

# ============================================================================================================

@app.route("/admin", methods=['GET', 'POST'])
def admin():
	if request.method == "GET":
		if "admin" in session:
			q = "select email,regno,fine from tarpusers"
			details = db.select(q)
			return render_template("admin/admin.html",user=session["admin"],details = details)
		else:return render_template("admin/adminlogin.html")
	if request.method == "POST":
		values = request.form.to_dict()
		mode = values["mode"]
		if mode == "login":
			email,password = values["email"],values["password"]
			if email == "perumallasasank123@gmail.com" and password == "12345":
				session["admin"] = email
				return redirect(url_for("admin"))
			else:
				flash("Invalid email or password")
				return redirect(url_for("admin"))
		if mode == "add":
			regno = values["regno"]
			email = values["email"]
			result = db.select("select * from tarpusers where email = '{}'".format(email))
			if len(result) == 0:
				result = db.select("select * from tarpusers where regno = '{}'".format(regno))
				if len(result) == 0:
					file = request.files['file']
					if file:
						filename = regno+os.path.splitext(secure_filename(file.filename))[1]
						pathtoimg = os.path.join(app.config['UPLOAD_FOLDER'], filename)
						file.save(pathtoimg)
					faceencodings,facelocs = faceencodingvalues(pathtoimg)
					if len(facelocs)==0:
						flash("No face detected")
						return redirect(url_for("admin"))
					db.insert("insert into tarpusers(regno,email,encodings) values('{}','{}','{}')".format(regno,email,str(faceencodings.tolist())))
					flash("User added")
					return redirect(url_for("admin"))
				elif len(result) == 1:
					flash("regno already exists")
					return redirect(url_for("admin"))
				else:
					flash("Something went wrong")
					return redirect(url_for("admin"))
			elif len(result) == 1:
				flash("Email already exists")
				return redirect(url_for("admin"))
			else:
				flash("Something went wrong")
				return redirect(url_for("admin"))
# ============================================================================================================

@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("home"))


if __name__ == '__main__':
	app.run(debug=True,port=8000)