import os

from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///family_news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class FamilyPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=True)
    file_path = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


with app.app_context():
    db.create_all()
    print("Database tables created.")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/info')
def info():
    return render_template('info.html')


@app.route('/contacts')
def contacts():
    return render_template('contacts.html')


@app.route('/news')
def news():
    news_posts = News.query.order_by(News.created_at.desc()).all()
    return render_template('news.html', news_posts=news_posts)


@app.route('/SubmitNews', methods=['POST'])
def upload_news():
    name = request.form['name']
    title = request.form['title']
    content = request.form['content']
    file = request.files.get('file')

    file_path = None
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

    new_news = News(name=name, title=title, content=content, file_path=file_path)
    db.session.add(new_news)
    db.session.commit()

    return redirect(url_for('news'))


@app.route('/upload_family_photo', methods=['POST'])
def upload_family_photo():
    description = request.form.get('description', '')
    year = request.form.get('year')
    file = request.files.get('file')

    if file and year:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file.save(file_path)

        new_photo = FamilyPhoto(description=description, file_path=file_path, year=int(year))
        db.session.add(new_photo)
        db.session.commit()

    return redirect(url_for('year_page', year=year))


@app.route('/year/<int:year>', methods=['GET', 'POST'])
def year_page(year):
    event_details = {
        2022: 'Fort Lauderdale, Florida, August 5-7, 2022',
        2020: 'Example Location, Example Date',
        2016: 'Atlanta, Georgia, August 4-7, 2016',
    }
    photos = FamilyPhoto.query.filter_by(year=year).order_by(FamilyPhoto.created_at.desc()).all()
    event_detail = event_details.get(year, 'Event details not available')
    return render_template('year.html', year=year, photos=photos, event_detail=event_detail)


@app.route('/delete_news/<int:news_id>', methods=['POST'])
def delete_news(news_id):
    news_to_delete = News.query.get_or_404(news_id)
    if news_to_delete.file_path:
        try:
            os.remove(news_to_delete.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

    db.session.delete(news_to_delete)
    db.session.commit()
    return redirect(url_for('news'))


@app.route('/delete_photo/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    photo_to_delete = FamilyPhoto.query.get_or_404(photo_id)
    if photo_to_delete.file_path:
        try:
            os.remove(photo_to_delete.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

    db.session.delete(photo_to_delete)
    db.session.commit()
    return redirect(url_for('year_page', year=photo_to_delete.year))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/familyphotos_main')
def family_photos_main():
    year_thumbnails = {}
    photos = FamilyPhoto.query.order_by(FamilyPhoto.year, FamilyPhoto.created_at).all()
    for photo in photos:
        if photo.year not in year_thumbnails:
            year_thumbnails[photo.year] = photo
    return render_template('family_photos.html', year_thumbnails=year_thumbnails)


if __name__ == '__main__':
    app.run(debug=True)
