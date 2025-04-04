from flask import Flask, render_template, request, redirect, url_for
import os
import shutil
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = './'
SVG_FOLDER = 'static/svg'

@app.route("/", methods=["GET", "POST"])
def index():
    downloaded = False

    if request.method == "POST":
        # Choix d'une image exemple
        if "confirm_selection" in request.form:
            selected = request.form.get("example")
            if selected:
                shutil.copy(os.path.join(SVG_FOLDER, selected), "image_svg.svg")
                downloaded = True

        # Téléversement
        elif "upload" in request.form and "file" in request.files:
            file = request.files["file"]
            if file and file.filename.endswith(".svg"):
                file.save(os.path.join(UPLOAD_FOLDER, "image_svg.svg"))
                downloaded = True

        # Lancer le dessin
        elif "draw" in request.form:
            subprocess.Popen(["python3", "main.py"])
            return "<h1>Dessin lancé !</h1><a href='/'>Retour</a>"

    return render_template("index.html", downloaded=downloaded)

if __name__ == "__main__":
    app.run(debug=True)
