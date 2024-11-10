from math import ceil
from flask import request, Flask, jsonify
import uuid
import os
from datetime import datetime

receipt_app = Flask(__name__)
receipt_in_memory = {}
duplicate_receipt_check = {}

def calculate_points(data):
    points = 0
    points += sum(1 for c in data['retailer'] if c.isalnum())

    if float(data["total"]).is_integer():
        points += 50
    
    if float(data['total']) % 0.25 == 0:
        points += 25
    points += (len(data['items']) // 2) * 5
    points += sum(ceil(float(items['price']) * 0.2) for items in data['items'] if len(items['shortDescription'].strip()) % 3 == 0)
    
    date_of_purchase = datetime.strptime(data['purchaseDate'], "%Y-%m-%d")
    if int(date_of_purchase.day) % 2 != 0:
        points += 6

    purchase_time = datetime.strptime(data["purchaseTime"], "%H:%M")
    if datetime.strptime("14:00", "%H:%M") <= purchase_time < datetime.strptime("16:00", "%H:%M"):
        points += 10
    return points

def generate_key(data):
    items_summary = tuple((item['shortDescription'], item['price']) for item in data['items'])
    return (data['retailer'], data['purchaseDate'], data['purchaseTime'], data['total'], items_summary, len(items_summary))

@receipt_app.route("/receipts/process", methods=["POST"])
def generate_id():
    data = request.get_json()
    receipt_key = generate_key(data)
    if receipt_key in duplicate_receipt_check:
        return jsonify({"id": duplicate_receipt_check[receipt_key], "message": "Already Processed"}), 200
    receipt_id = str(uuid.uuid4())
    try:
        data["points"] = calculate_points(data)
    except (ValueError, KeyError) as err:
        return jsonify({"error": "Invalid data", "message": str(err)}), 400
    receipt_in_memory[receipt_id] = data
    duplicate_receipt_check[receipt_key] = receipt_id
    return jsonify({"id": receipt_id}), 200

@receipt_app.route("/receipts/<id>/points", methods=["GET"])
def get_points(id):
    if id not in receipt_in_memory:
        return jsonify({"error": "Receipt not found"}), 400
    print(receipt_in_memory)
    return jsonify({"points": receipt_in_memory[id]["points"]}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    receipt_app.run(debug=True, host='0.0.0.0')