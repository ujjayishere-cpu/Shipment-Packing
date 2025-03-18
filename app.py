from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import qrcode
import io
import base64
import json
import uuid
from PIL import Image, ImageDraw, ImageFont
from pyzbar.pyzbar import decode

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configurazione del database SQLite (dati permanenti)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///warehouse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelli per il database
class Product(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    shelf = db.Column(db.String(50), nullable=False)
    box_id = db.Column(db.String, db.ForeignKey('box.id'), nullable=True)

class Box(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=True)  # Nome opzionale per la scatola
    products = db.relationship('Product', backref='box', lazy=True)

with app.app_context():
    db.create_all()

# Funzioni di utilità
def normalize_product_name(name):
    return name.strip().upper().replace(' ', '_')

def generate_qr_code(data_dict):
    # Genera il QR code con i dati in formato JSON
    qr_data = json.dumps(data_dict)
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white').convert('RGB')

    # Se è presente un nome (per prodotto o scatola), lo aggiunge in alto all'immagine
    if "name" in data_dict and data_dict["name"]:
        text = data_dict["name"]
        try:
            # Prova a caricare un font bold di dimensione maggiore
            font = ImageFont.truetype("arialbd.ttf", 24)
        except Exception:
            font = ImageFont.load_default()
        dummy_img = Image.new("RGB", (1, 1))
        draw_dummy = ImageDraw.Draw(dummy_img)
        bbox = draw_dummy.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        new_width = max(img.width, text_width + 20)
        new_height = img.height + text_height + 10
        new_img = Image.new("RGB", (new_width, new_height), "white")
        draw = ImageDraw.Draw(new_img)
        text_x = (new_width - text_width) // 2
        # Disegna il testo in grassetto e più grande
        draw.text((text_x, 5), text, fill="black", font=font)
        qr_x = (new_width - img.width) // 2
        new_img.paste(img, (qr_x, text_height + 10))
        img = new_img

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# Funzione per generare il QR code come variabile globale
@app.context_processor
def utility_processor():
    return dict(generate_qr_code=generate_qr_code)


def decode_qr_code(file_stream):
    try:
        image = Image.open(file_stream)
    except Exception:
        return None, "File immagine non valido."
    decoded_objs = decode(image)
    if not decoded_objs:
        return None, "Nessun QR code trovato."
    qr_text = decoded_objs[0].data.decode('utf-8')
    try:
        data = json.loads(qr_text)
    except Exception:
        return None, "Il contenuto del QR code non è un JSON valido."
    return data, None

# Rotte

@app.route('/')
def index():
    return render_template('index.html')

# Creazione di un nuovo prodotto
@app.route('/product/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        name = request.form.get('name')
        shelf_number = request.form.get('shelf_number')
        shelf_level = request.form.get('shelf_level')
        if not name or not shelf_number or not shelf_level:
            flash("Tutti i campi sono obbligatori.")
            return redirect(url_for('new_product'))
        normalized_name = normalize_product_name(name)
        shelf = f"{shelf_number}.{shelf_level}"
        product = Product(name=normalized_name, shelf=shelf)
        db.session.add(product)
        db.session.commit()
        product_data = {
            "id": product.id,
            "name": product.name,
            "shelf": product.shelf
        }
        qr_code_img = generate_qr_code(product_data)
        return render_template('product_qr.html', product=product_data, qr_code_img=qr_code_img)
    return render_template('new_product.html')

# Scansione del QR code di un prodotto tramite upload
@app.route('/product/scan', methods=['GET', 'POST'])
def scan_product():
    if request.method == 'POST':
        if 'qr_image' not in request.files:
            flash("Nessun file caricato.")
            return redirect(request.url)
        file = request.files['qr_image']
        if file.filename == '':
            flash("Nessun file selezionato.")
            return redirect(request.url)
        data, error = decode_qr_code(file)
        if error:
            flash(error)
            return redirect(request.url)
        product = None
        if data.get("id"):
            product = Product.query.get(data.get("id"))
        if product:
            data = {
                "id": product.id,
                "name": product.name,
                "shelf": product.shelf
            }
        return render_template('product_qr.html', product=data, qr_code_img=None, scanned=True)
    return render_template('upload_qr.html', scan_type="Prodotto (Upload)")

# Scannerizzazione del QR code tramite fotocamera (Prodotto)
@app.route('/product/camera_scan', methods=['GET'])
def camera_scan():
    return render_template('camera_scan.html')

# Elaborazione del QR code scansionato via fotocamera (Prodotto)
@app.route('/product/process_scan', methods=['POST'])
def process_scan():
    qr_text = request.form.get('qr_text')
    if not qr_text:
        flash("Nessun dato ricevuto dalla scansione.")
        return redirect(url_for('camera_scan'))
    try:
        data = json.loads(qr_text)
    except Exception:
        flash("Il contenuto del QR code non è un JSON valido.")
        return redirect(url_for('camera_scan'))
    product = None
    if data.get("id"):
        product = Product.query.get(data.get("id"))
    if product:
        data = {
            "id": product.id,
            "name": product.name,
            "shelf": product.shelf
        }
    return render_template('product_qr.html', product=data, qr_code_img=None, scanned=True)

# Scannerizzazione del QR code tramite fotocamera (Scatola)
@app.route('/box/camera_scan', methods=['GET'])
def box_camera_scan():
    return render_template('box_camera_scan.html')

# Scannerizzazione del QR code di una scatola tramite upload
@app.route('/box/scan', methods=['GET', 'POST'])
def scan_box():
    if request.method == 'POST':
        if 'qr_image' not in request.files:
            flash("Nessun file caricato.")
            return redirect(request.url)
        file = request.files['qr_image']
        if file.filename == '':
            flash("Nessun file selezionato.")
            return redirect(request.url)
        data, error = decode_qr_code(file)
        if error:
            flash(error)
            return redirect(request.url)
        if data.get("type") == "box" and data.get("id"):
            return redirect(url_for('box_detail', box_id=data.get("id")))
        else:
            flash("QR code non valido per una scatola.")
            return redirect(request.url)
    return render_template('upload_qr.html', scan_type="Scatola (Upload)")

# Elaborazione del QR code scansionato via fotocamera (Scatola)
@app.route('/box/process_scan', methods=['POST'])
def box_process_scan():
    qr_text = request.form.get('qr_text')
    if not qr_text:
        flash("Nessun dato ricevuto dalla scansione.")
        return redirect(url_for('box_camera_scan'))
    try:
        data = json.loads(qr_text)
    except Exception:
        flash("Il contenuto del QR code non è un JSON valido.")
        return redirect(url_for('box_camera_scan'))
    if data.get("type") == "box" and data.get("id"):
        return redirect(url_for('box_detail', box_id=data.get("id")))
    else:
        flash("QR code non valido per una scatola.")
        return redirect(url_for('box_camera_scan'))

# Scannerizzazione tramite fotocamera per aggiungere un prodotto a una scatola
@app.route('/box/<box_id>/camera_scan', methods=['GET'])
def box_product_camera_scan(box_id):
    return render_template('box_product_camera_scan.html', box_id=box_id)

@app.route('/box/<box_id>/process_scan', methods=['POST'])
def box_product_process_scan(box_id):
    qr_text = request.form.get('qr_text')
    if not qr_text:
        flash("Nessun dato ricevuto dalla scansione.")
        return redirect(url_for('box_product_camera_scan', box_id=box_id))
    try:
        data = json.loads(qr_text)
    except Exception:
        flash("Il contenuto del QR code non è un JSON valido.")
        return redirect(url_for('box_product_camera_scan', box_id=box_id))
    product = None
    if data.get("id"):
        product = Product.query.get(data.get("id"))
    if not product or product.box_id is not None:
        flash("Prodotto non trovato o già assegnato.")
        return redirect(url_for('box_product_camera_scan', box_id=box_id))
    product.box_id = box_id
    db.session.commit()
    flash("Prodotto aggiunto alla scatola e rimosso dal magazzino.")
    return redirect(url_for('box_detail', box_id=box_id))

# Creazione di una nuova scatola (con nome opzionale)
@app.route('/box/new', methods=['GET', 'POST'])
def new_box():
    if request.method == 'POST':
        box_name = request.form.get('name')
        box = Box(name=box_name)
        db.session.add(box)
        db.session.commit()
        qr_box_data = {
            "id": box.id,
            "type": "box",
            "name": box.name
        }
        qr_code_img = generate_qr_code(qr_box_data)
        return render_template('box_detail.html', box=box, products_in_box=[], qr_code_img=qr_code_img)
    return render_template('new_box.html')

# Dettaglio della scatola e aggiunta di prodotto tramite upload
@app.route('/box/<box_id>', methods=['GET', 'POST'])
def box_detail(box_id):
    box = Box.query.get(box_id)
    if not box:
        flash("Scatola non trovata.")
        return redirect(url_for('index'))
    if request.method == 'POST':
        if 'qr_image' not in request.files:
            flash("Nessun file caricato.")
            return redirect(url_for('box_detail', box_id=box_id))
        file = request.files['qr_image']
        if file.filename == '':
            flash("Nessun file selezionato.")
            return redirect(url_for('box_detail', box_id=box_id))
        data, error = decode_qr_code(file)
        if error:
            flash(error)
            return redirect(url_for('box_detail', box_id=box_id))
        product = None
        if data.get("id"):
            product = Product.query.get(data.get("id"))
        if not product or product.box_id is not None:
            flash("Prodotto non trovato o già assegnato.")
            return redirect(url_for('box_detail', box_id=box_id))
        product.box_id = box.id
        db.session.commit()
        flash("Prodotto aggiunto alla scatola e rimosso dal magazzino.")
        return redirect(url_for('box_detail', box_id=box_id))
    products_in_box = Product.query.filter_by(box_id=box_id).all()
    return render_template('box_detail.html', box=box, products_in_box=products_in_box, qr_code_img=None)

# Rimozione di un prodotto dalla scatola (ritorno nel magazzino)
@app.route('/box/<box_id>/remove/<product_id>', methods=['POST'])
def remove_product_from_box(box_id, product_id):
    box = Box.query.get(box_id)
    if not box:
        flash("Scatola non trovata.")
        return redirect(url_for('index'))
    product = Product.query.get(product_id)
    if not product or product.box_id != box.id:
        flash("Prodotto non trovato nella scatola.")
        return redirect(url_for('box_detail', box_id=box_id))
    product.box_id = None
    db.session.commit()
    flash("Prodotto rimosso dalla scatola e restituito al magazzino.")
    return redirect(url_for('box_detail', box_id=box_id))

# Eliminazione di un prodotto dal magazzino (solo se non assegnato a una scatola)
@app.route('/product/delete/<product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product and product.box_id is None:
        db.session.delete(product)
        db.session.commit()
        flash("Prodotto rimosso dal magazzino.")
    else:
        flash("Prodotto non trovato o presente in una scatola.")
    return redirect(url_for('warehouse'))

# Eliminazione di una scatola (de-associa i prodotti)
@app.route('/box/delete/<box_id>', methods=['POST'])
def delete_box(box_id):
    box = Box.query.get(box_id)
    if not box:
        flash("Scatola non trovata.")
        return redirect(url_for('warehouse'))
    products_in_box = Product.query.filter_by(box_id=box_id).all()
    for product in products_in_box:
        product.box_id = None
    db.session.delete(box)
    db.session.commit()
    flash("Scatola eliminata.")
    return redirect(url_for('warehouse'))

# Visualizzazione schematica del magazzino (anche se vuoto)
@app.route('/warehouse')
def warehouse():
    products = Product.query.filter_by(box_id=None).all()
    boxes = Box.query.all()
    # Per ogni scatola, genera il QR code (con il nome in alto se presente)
    for box in boxes:
        qr_box_data = {"id": box.id, "type": "box", "name": box.name}
        box.qr_code_img = generate_qr_code(qr_box_data)
    return render_template('warehouse.html', products=products, boxes=boxes)

if __name__ == '__main__':
    app.run(debug=True)
