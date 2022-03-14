import cv2
from flask import Flask, Response, render_template, request, redirect, session, url_for, flash, jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from facedetector import detect, faceencodingvalues, predata
import db
import os



app = Flask(__name__)
mail= Mail(app)
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.getenv('SECRET_KEY')

dbconnect = db.connect()

@app.route("/")
@app.route("/home")
def home():
	predata()
	return render_template("index.html")


# ============================================================================================================

cap = cv2.VideoCapture(0)
def gen_frames():
	global recorded,cap
	while True:
		sucess,img = cap.read()
		(frame,ans) = detect(img)
		recorded = ans
		if recorded == "YES":
			break
		yield(b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
	print("yield condition exit")
	cap.release()

@app.route("/video_feed")
def video_feed():
	return Response(gen_frames(),
					mimetype='multipart/x-mixed-replace; boundary=frame')

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

			q = "select * from tarpusers where email = '{}'".format(email)
			result = db.select(q)
			if len(result) == 0:
				q = "select * from tarpusers where regno = '{}'".format(regno)
				result = db.select(q)
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
					q = "insert into tarpusers(regno,email,encodings) values('{}','{}','{}')".format(regno,email,str(faceencodings.tolist()))
					db.insert(q)
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