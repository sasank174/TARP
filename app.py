import cv2
from flask import Flask, Response, render_template, request, redirect, session, url_for, flash, jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from facedetector import detectmask, detectface, faceencodingvalues, predata
import db
import os



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
	return render_template("index.html")


# ============================================================================================================

cap = cv2.VideoCapture(0)
def gen_frames():
	global cap,maskdetected,facedetected
	while True:
		sucess,img = cap.read()
		if maskdetected == False and facedetected == False:
			ans = detectmask(img)
			if ans == "mask":maskdetected = True
			else:
				ans = detectface(img)
				if ans:facedetected = ans
		elif maskdetected == False:
			ans = detectmask(img)
			if ans == "mask":maskdetected = True
		else:
			ans = detectface(img)
			if ans:facedetected = ans
		yield(b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')

@app.route("/video_feed")
def video_feed():
	return Response(gen_frames(),
					mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/recorded')
def recorded():
	return jsonify({"mask":maskdetected, "face":facedetected})

@app.route('/recorddone', methods = ['POST', 'GET'])
def recorddone():
	global maskdetected,facedetected
	cap.release()
	maskdetected,facedetected = False, False
	return redirect(url_for('home'))

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
	return redirect(url_for("login"))


if __name__ == '__main__':
	app.run(debug=True,port=8000)