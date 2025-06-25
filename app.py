from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import pytesseract
from PIL import Image
import face_recognition
import os
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
app.secret_key = 'kuch_secret_key_jo_random_ho'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

def extract_dob_and_age(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    dob = re.search(r'\d{2}/\d{2}/\d{4}', text) or re.search(r'\d{4}', text)
    if dob:
        dob_val = dob.group()
        if len(dob_val) == 4:
            age = datetime.now().year - int(dob_val)
        else:
            try:
                birth_date = datetime.strptime(dob_val, "%d/%m/%Y")
                age = relativedelta(datetime.now(), birth_date).years
            except:
                return None, None
        return dob_val, age
    return None, None

def compare_faces(img1_path, img2_path):
    try:
        image1 = face_recognition.load_image_file(img1_path)
        image2 = face_recognition.load_image_file(img2_path)

        encodings1 = face_recognition.face_encodings(image1)
        encodings2 = face_recognition.face_encodings(image2)

        if not encodings1 or not encodings2:
            return False

        match = face_recognition.compare_faces([encodings1[0]], encodings2[0])[0]
        return match
    except Exception as e:
        print(f"Face comparison error: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        aadhaar = request.files.get('aadhaar')
        selfie = request.files.get('selfie')
        selfie_webcam_data = request.form.get('selfie_webcam')

        if not aadhaar:
            return render_template('index.html', error="Please upload Aadhaar image.")

        aadhaar_path = os.path.join(UPLOAD_FOLDER, 'aadhaar.jpg')
        aadhaar.save(aadhaar_path)

        if selfie_webcam_data:
            header, encoded = selfie_webcam_data.split(',', 1)
            data = base64.b64decode(encoded)
            selfie_path = os.path.join(UPLOAD_FOLDER, 'selfie.jpg')
            with open(selfie_path, 'wb') as f:
                f.write(data)
        elif selfie:
            selfie_path = os.path.join(UPLOAD_FOLDER, 'selfie.jpg')
            selfie.save(selfie_path)
        else:
            return render_template('index.html', error="Please provide selfie (upload or webcam).")

        dob, age = extract_dob_and_age(aadhaar_path)
        face_match = compare_faces(aadhaar_path, selfie_path)
        verified = age is not None and age >= 18 and face_match

        session['result'] = {
            'DOB': dob,
            'Age': age,
            'Face Match': bool(face_match),
            '18+': bool(age >= 18) if age is not None else False,
            'Verified': bool(verified),
            'aadhaar_path': 'aadhaar.jpg',
            'selfie_path': 'selfie.jpg'
        }
        return redirect(url_for('index'))

    result = session.pop('result', None)
    error = request.args.get('error')
    return render_template('index.html', result=result, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

