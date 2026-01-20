# app.py - Flask REST API for Dim Sum Comparison
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dimsum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db = SQLAlchemy(app)

# Database Model
class DimSum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_name = db.Column(db.String(200), nullable=False)
    dish_name = db.Column(db.String(200), nullable=False)
    dish_type = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    price = db.Column(db.Float)
    notes = db.Column(db.Text)
    visit_date = db.Column(db.Date)
    location = db.Column(db.String(200))
    would_order_again = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_name': self.restaurant_name,
            'dish_name': self.dish_name,
            'dish_type': self.dish_type,
            'rating': self.rating,
            'price': self.price,
            'notes': self.notes,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'location': self.location,
            'would_order_again': self.would_order_again,
            'created_at': self.created_at.isoformat()
        }

# Create database tables
with app.app_context():
    db.create_all()

# REST API Endpoints

@app.route('/api/dimsum', methods=['GET'])
def get_dimsum():
    """Get all dim sum with optional search"""
    search = request.args.get('search', '')
    
    if search:
        items = DimSum.query.filter(
            (DimSum.restaurant_name.ilike(f'%{search}%')) | 
            (DimSum.dish_name.ilike(f'%{search}%')) |
            (DimSum.dish_type.ilike(f'%{search}%'))
        ).order_by(DimSum.created_at.desc()).all()
    else:
        items = DimSum.query.order_by(DimSum.created_at.desc()).all()
    
    return jsonify([item.to_dict() for item in items])

@app.route('/api/dimsum/<int:item_id>', methods=['GET'])
def get_dimsum_item(item_id):
    """Get a single dim sum item by ID"""
    item = DimSum.query.get_or_404(item_id)
    return jsonify(item.to_dict())

@app.route('/api/dimsum', methods=['POST'])
def create_dimsum():
    """Create a new dim sum entry"""
    data = request.get_json()
    
    visit_date = None
    if data.get('visit_date'):
        visit_date = datetime.fromisoformat(data['visit_date']).date()
    
    item = DimSum(
        restaurant_name=data['restaurant_name'],
        dish_name=data['dish_name'],
        dish_type=data.get('dish_type'),
        rating=data.get('rating', 0),
        price=data.get('price'),
        notes=data.get('notes'),
        visit_date=visit_date,
        location=data.get('location'),
        would_order_again=data.get('would_order_again', True)
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify(item.to_dict()), 201

@app.route('/api/dimsum/<int:item_id>', methods=['PUT'])
def update_dimsum(item_id):
    """Update an existing dim sum entry"""
    item = DimSum.query.get_or_404(item_id)
    data = request.get_json()
    
    item.restaurant_name = data.get('restaurant_name', item.restaurant_name)
    item.dish_name = data.get('dish_name', item.dish_name)
    item.dish_type = data.get('dish_type', item.dish_type)
    item.rating = data.get('rating', item.rating)
    item.price = data.get('price', item.price)
    item.notes = data.get('notes', item.notes)
    item.location = data.get('location', item.location)
    item.would_order_again = data.get('would_order_again', item.would_order_again)
    
    if data.get('visit_date'):
        item.visit_date = datetime.fromisoformat(data['visit_date']).date()
    
    db.session.commit()
    
    return jsonify(item.to_dict())

@app.route('/api/dimsum/<int:item_id>', methods=['DELETE'])
def delete_dimsum(item_id):
    """Delete a dim sum entry"""
    item = DimSum.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    return '', 204

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about dim sum"""
    total_items = DimSum.query.count()
    avg_rating = db.session.query(db.func.avg(DimSum.rating)).scalar() or 0
    avg_price = db.session.query(db.func.avg(DimSum.price)).scalar() or 0
    
    restaurants = db.session.query(
        DimSum.restaurant_name, 
        db.func.count(DimSum.id)
    ).group_by(DimSum.restaurant_name).all()
    
    dish_types = db.session.query(
        DimSum.dish_type, 
        db.func.count(DimSum.id)
    ).group_by(DimSum.dish_type).all()
    
    winners = DimSum.query.filter_by(would_order_again=True).count()
    losers = DimSum.query.filter_by(would_order_again=False).count()
    
    return jsonify({
        'total_items': total_items,
        'average_rating': round(avg_rating, 2),
        'average_price': round(avg_price, 2),
        'winners': winners,
        'losers': losers,
        'restaurants': [{'name': r[0], 'count': r[1]} for r in restaurants if r[0]],
        'dish_types': [{'type': d[0], 'count': d[1]} for d in dish_types if d[0]]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)