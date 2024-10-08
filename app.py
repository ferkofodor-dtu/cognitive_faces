from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'secret'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ferkofodor:vYbU5PTZtOaIS31IG0NrTIYW4k6g8VAe@dpg-crg3lsaj1k6c739cbolg-a.frankfurt-postgres.render.com/cognitive_faces"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the database model
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    image_index = db.Column(db.Integer, nullable=False)
    mood = db.Column(db.Integer, nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form['username']
    #check if the user already exists in the database
    user = Rating.query.filter_by(username=username).first()
    if user is not None:
        return redirect('/already_exists')
    
    if username:
        session['username'] = username
        return redirect('/0')
    
    return redirect('/')

@app.route('/<int:image_index>')
def index(image_index=0):
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect('/')

    # List all images in the folder
    image_list = os.listdir('static/images')
    total_images = len(image_list)
    
    # Ensure index is within bounds
    if image_index < 0:
        image_index = 0
    elif image_index >= total_images:
        image_index = total_images - 1
    
    # Load the current image
    current_image = url_for('static', filename=f'images/{image_list[image_index]}')
    
    # Get all ratings for the current user
    username = session['username']
    
    ratings = Rating.query.filter_by(username=username).all()
    rated_images = {rating.image_index for rating in ratings}
    try:
        current_rating = Rating.query.filter_by(username=username, image_index=image_index).first()
        current_rating = current_rating.mood
    except:
        current_rating = None
    
    # Calculate progress
    progress = round(len(rated_images) / total_images * 100, 2)
    is_goodbye = len(rated_images) == total_images
    print(progress, is_goodbye)
    
    if is_goodbye:
        return redirect('/goodbye')
    else:    
        return render_template('index.html', 
                           image=current_image, 
                           image_index=image_index, 
                           total_images=total_images, 
                           progress=progress,
                           current_rating=current_rating)

@app.route('/goodbye')
def goodbye():
    avg_rating = Rating.query.filter_by(username=session['username']).with_entities(db.func.avg(Rating.mood)).scalar()
    avg_rating = round(avg_rating, 2) if avg_rating else 0
    return render_template('goodbye.html', avg_rating=avg_rating)

@app.route('/already_exists')
def already_exists():
    return render_template('already_exists.html')

@app.route('/rate', methods=['POST'])
def rate():
    if 'username' not in session:
        return redirect('/')
    
    rating = request.form['mood']
    image_index = int(request.form['image_index'])
    username = session['username']
    
    # Store the rating in the database
    new_rating = Rating(username=username, image_index=image_index, mood=rating)
    old_rating = Rating.query.filter_by(username=username, image_index=image_index).first()
    if old_rating:
        old_rating.mood = rating
        db.session.commit()
    else:
        db.session.add(new_rating)
        db.session.commit()
    
    # Redirect to the next image or stay on the last one
    return redirect(f'/{image_index + 1}' if image_index < len(os.listdir('static/images')) - 1 else f'/{image_index}')

@app.route('/reset', methods=['POST'])
def reset():
    if 'username' not in session:
        return redirect('/')
    
    username = session['username']
    Rating.query.filter_by(username=username).delete()
    db.session.commit()
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
