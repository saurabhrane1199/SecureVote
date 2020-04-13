import datetime
from blockchain import Blockchain
import hashlib
import json
from flask import Flask, jsonify, request, redirect, url_for, render_template, flash, session
import requests
from uuid import uuid4
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
import sys

app = Flask(__name__)
app.secret_key = "secret"
node_address = str(uuid4()).replace('-', '')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

blockchain = Blockchain()

clear=0


def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(voter=-1, candidate=-1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'VotingTrans': block['VotingTrans']}
    return jsonify(response), 200

def is_valid():
    is_valid=blockchain.is_chain_valid()
    if is_valid:
        response = 1
    else:
        response = 0
    return response

class User(db.Model):
    """ Create user table"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    category = db.Column(db.Integer)

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        else:
            return render_template('index.html', user=request.args.get('user'))
    else:
        voterId = int(request.form['userId'])
        candidate = int(request.form['optradio'])
        if not voterId or not candidate:
            return render_template('success.html', flag=0, user=voterId)
        #blockchain.add_transaction(voterId,candidate)
        k=blockchain.get_previous_block()
        if k!=0:
            proof=blockchain.proof_of_work(k.get("proof", ""))    
        else:
            proof=1    
        #print(k)    
        index = blockchain.create_block(proof,blockchain.hash(k),voterId,candidate)
        print(blockchain.hash(k))
        b=blockchain.give_chain()
        print("chain is", b)
        if index == None:
            return render_template('success.html', flag=0, user=voterId)
        else:
            if len(blockchain.VotingTrans) == 10:
                mine_block()
            return render_template('success.html', flag=1, candidateId=candidate, user=voterId), 200


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login Form"""
    if request.method == 'GET':
        return render_template('login.html')
    else:
        name = request.form['username']
        passw = request.form['password']
        data = User.query.filter_by(username=name, password=passw).first()
        if data is not None:
            admin = data.category
            if admin == 0:
                userId = data.id
                session['logged_in'] = True
                return redirect(url_for('home', user=userId))
            else:
                session['logged_in'] = True
                return redirect(url_for('getResult'))
        else:
            # return "data is none"
            return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout Form"""
    session.pop('logged_in', None)
    return redirect(url_for('home'))


@app.route('/admin', methods=['GET'])
def getResult():
    isValid = is_valid()
    response=blockchain.getResult()
    finalResult = response
    print(type(finalResult), file=sys.stdout)
    return render_template('admin.html',data = finalResult,flag = isValid)


# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response={'chain': blockchain.give_chain(),
                'length': len(blockchain.give_chain())}
    return jsonify(response), 200


# # Checking if the Blockchain is valid
# @app.route('/is_valid', methods=['GET'])



# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json=request.get_json()
    nodes=json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response={'message': 'All the nodes are now connected. The Hadcoin Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201


# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced=blockchain.replace_chain()
    if is_chain_replaced:
        response={'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response={'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200


if __name__ == '__main__':
    app.debug=True
    db.create_all()
    app.secret_key="123"
    app.run(host='127.0.0.1', port=5000)


