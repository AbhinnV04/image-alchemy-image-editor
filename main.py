from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
import cv2
import os

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
def normalize_intensity(pixel, chars):
    return int(pixel * (len(chars) - 1) / 255)

def downscale_image(img, max_dimension=500):
    height, width = img.shape[:2]
    if max(height, width) > max_dimension:
        scale_factor = max_dimension / max(height, width)
        img = cv2.resize(img, None, fx=scale_factor, fy=scale_factor)
    return img

def convert_to_ascii(img):
    chars = '@%#*+=-:. '  
    scaled_img = downscale_image(img)
    gray_img = cv2.cvtColor(scaled_img, cv2.COLOR_BGR2GRAY)
    blurred_img = cv2.GaussianBlur(gray_img, (3, 3), 0)  
    ascii_image = ''
    for row in blurred_img:
        for pixel in row:
            normalized_intensity = normalize_intensity(pixel, chars)
            ascii_image += chars[normalized_intensity]
        ascii_image += '\n'  
    return ascii_image


def processImage(filename, operation):
    print(f"the operation is {operation} and filename is {filename}")
    img = cv2.imread(f"images/{filename}")
    new_filename_base = os.path.splitext(filename)[0] + '_new'
    match operation:
        case "cgray":
            img_processed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            new_filename = f"images/{new_filename_base}.jpg"
            cv2.imwrite(new_filename, img_processed)
            return new_filename
        case "cwebp": 
            new_filename = f"images/{new_filename_base}.webp"
            cv2.imwrite(new_filename, img)
            return new_filename
        case "cjpg": 
            new_filename = f"images/{new_filename_base}.jpg"
            cv2.imwrite(new_filename, img)
            return new_filename
        case "cpng": 
            new_filename = f"images/{new_filename_base}.png"
            cv2.imwrite(new_filename, img)
            return new_filename
        case "cinv":
            inverted_image = cv2.bitwise_not(img)
            new_filename = f"images/{new_filename_base}_inverted.jpg"
            cv2.imwrite(new_filename, inverted_image)
            return new_filename
        case "cascii":
            ascii_image = convert_to_ascii(img)
            new_filename = f"images/{new_filename_base}.txt"
            with open(new_filename, 'w') as f:
                f.write(ascii_image)
            return new_filename
        case "cflip":
            flipped_image = cv2.flip(img, 1)  # 1 for horizontal flip, 0 for vertical flip
            new_filename = f"images/{new_filename_base}_flipped.jpg"
            cv2.imwrite(new_filename, flipped_image)
            return new_filename
    pass


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == "POST": 
        operation = request.form.get("operation")
        if 'file' not in request.files:
            flash('No file part')
            return "error"
        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return "error no selected file"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new = processImage(filename, operation)
            flash(f"Your image has been processed: <a href='/{new}' target='_blank'>View</a>")
            return render_template("index.html")

    return render_template("index.html")


app.run(debug=True, port=5001)