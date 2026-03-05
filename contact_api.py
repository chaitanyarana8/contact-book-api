from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'contacts_api.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return jsonify({
        'message': 'Contact Book API',
        'endpoints': {
            'GET /contacts': 'Get all contacts',
            'POST /contacts': 'Add contact',
            'GET /contacts/<id>': 'Get one contact',
            'PUT /contacts/<id>': 'Update contact',
            'DELETE /contacts/<id>': 'Delete contact'
        }
    })

@app.route('/contacts', methods=['GET'])
def get_contacts():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts')
    contacts = cursor.fetchall()
    conn.close()
    
    contact_list = []
    for contact in contacts:
        contact_list.append({
            'id': contact[0],
            'name': contact[1],
            'phone': contact[2],
            'email': contact[3],
            'created_at': contact[4]
        })
    
    return jsonify({'success': True, 'contacts': contact_list})

@app.route('/contacts/<int:id>', methods=['GET'])
def get_contact(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE id = ?', (id,))
    contact = cursor.fetchone()
    conn.close()
    
    if not contact:
        return jsonify({'success': False, 'message': 'Not found'}), 404
    
    return jsonify({
        'success': True,
        'contact': {
            'id': contact[0],
            'name': contact[1],
            'phone': contact[2],
            'email': contact[3],
            'created_at': contact[4]
        }
    })

@app.route('/contacts', methods=['POST'])
def add_contact():
    data = request.get_json()
    
    # Validate: Check if data exist
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided.'
        }),400
    
    # Validate: Name required.
    if 'name' not in data or not data['name'].strip():
        return jsonify({
            'success': False,
            'message': 'Name is required.'
        }),400
        
    # Validate: Phone required
    if 'phone' not in data or not data['phone'].strip():
        return jsonify({
            'success': False,
            'message': 'Phone is required.'
        }),400
    
    
    name = data['name'].strip()
    phone = data['phone'].strip()
    email = data.get('email', '').strip()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Validate: phone must be 10 digits.
    if  not phone.isdigit() or len(phone)!=10:
        return jsonify({
            'success': False,
            'message': 'Phone  must be 10 digits.'
        }),400
    
    
    # Check duplicate phone
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE phone = ?',(phone,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Contact with  this phone  already exists.'
        }),400
    
    # Insert contact
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO contacts (name, phone, email, created_at) VALUES (?, ?, ?, ?)',
        (name, phone, email, created_at)
    )
    conn.commit()
    contact_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Contact added Successfully',
        'contact': {
            'id': contact_id, 
            'name': name, 
            'phone': phone, 
            'email': email,
            'created_at': created_at}
    }), 201

@app.route('/contacts/<int:id>', methods=['PUT'])
def update_contact(id):
    data = request.get_json()
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE id = ?', (id,))
    contact = cursor.fetchone()
    
    if not contact:
        conn.close()
        return jsonify({'success': False, 'message': 'Not found'}), 404
    
    name = data.get('name', contact[1])
    phone = data.get('phone', contact[2])
    email = data.get('email', contact[3])
    
    cursor.execute(
        'UPDATE contacts SET name = ?, phone = ?, email = ? WHERE id = ?',
        (name, phone, email, id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Updated',
        'contact': {'id': id, 'name': name, 'phone': phone, 'email': email}
    })

@app.route('/contacts/<int:id>', methods=['DELETE'])
def delete_contact(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE id = ?', (id,))
    contact = cursor.fetchone()
    
    if not contact:
        conn.close()
        return jsonify({'success': False, 'message': 'Not found'}), 404
    
    cursor.execute('DELETE FROM contacts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Deleted'})


# Search contacts by name
@app.route('/contacts/search', methods = ['GET'])
def search_contact():
    query = request.args.get('name','')
    
    if not query:
        return jsonify({
            'success': False,
            'message': 'Please provide name parameter.'
        }),400
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE name LIKE ?',('%'+query+'%',))
    
    contacts = cursor.fetchall()
    conn.close()
    
    contact_list = []
    for contact in contacts:
        contact_list.append({
            'id': contact[0],
            'name': contact[1],
            'phone': contact[2],
            'email': contact[3],
            'created_at': contact[4]
        })
        
    return jsonify({
        'success': True,
        'count': len(contact_list),
        'contacts': contact_list
    })
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT',5001))
    app.run(host='0.0.0.0',debug=False, port=port)