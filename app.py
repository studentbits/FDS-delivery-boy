from flask import Flask, jsonify, request
import os
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI') 

try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')  # Verify connection
    print("Database connected successfully.")
    db = client["FoodDeliveryApp"]
    users = db["user"]
    menus = db["menu"]
    orders = db["order"]
except ConnectionFailure:
    print("Failed to connect to the database.")


############### Order Section #################################

# Add a new order
@app.route('/order/<user_id>/<restaurant_id>', methods=['POST'])
def add_order(user_id, restaurant_id):
    try:
        # Get data from request body
        data = request.get_json()

        # Validate required fields
        required_fields = ["status", "menu_detail", "total_price", "delivery_person_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"msg": f"Missing required field: {field}"}), 400

        # Prepare the order document
        order_data = {
            "user_id": ObjectId(user_id),
            "restaurant_id": ObjectId(restaurant_id),
            "status": data["status"],
            "menu_detail": data["menu_detail"],  # Assume this is a list or detailed object
            "total_price": data["total_price"],
            "delivery_person_id": ObjectId(data["delivery_person_id"])
        }

        # Insert the order into the database
        order_id = orders.insert_one(order_data).inserted_id

        # Fetch the inserted order to include all fields
        inserted_order = orders.find_one({"_id": order_id})

        # Convert ObjectId fields to strings for the response
        inserted_order["_id"] = str(inserted_order["_id"])
        inserted_order["user_id"] = str(inserted_order["user_id"])
        inserted_order["restaurant_id"] = str(inserted_order["restaurant_id"])
        inserted_order["delivery_person_id"] = str(inserted_order["delivery_person_id"])

        return jsonify({"msg": "Order added successfully", "order_data": inserted_order}), 201

    except Exception as e:
        return jsonify({"msg": "Error adding order", "error": str(e)}), 500

# Change status of order
@app.route('/order/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    try:
        # Get the delivery_person_id and new status from the request body
        data = request.get_json()

        # Validate the required fields
        if "delivery_person_id" not in data or "status" not in data:
            return jsonify({"msg": "Missing required fields: 'delivery_person_id' and 'status'"}), 400

        # Fetch the order by order_id
        order = orders.find_one({"_id": ObjectId(order_id)})

        if not order:
            return jsonify({"msg": "Order not found"}), 404

        # Check if the delivery person is valid for this order
        if str(order["delivery_person_id"]) != data["delivery_person_id"]:
            return jsonify({"msg": "Unauthorized: You are not assigned to this order"}), 403

        # Update the order status
        result = orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": data["status"]}}
        )

        if result.modified_count > 0:
            # Fetch the updated order to return
            updated_order = orders.find_one({"_id": ObjectId(order_id)})
            updated_order["_id"] = str(updated_order["_id"])
            updated_order["user_id"] = str(updated_order["user_id"])
            updated_order["restaurant_id"] = str(updated_order["restaurant_id"])
            updated_order["delivery_person_id"] = str(updated_order["delivery_person_id"])

            return jsonify({"msg": "Order status updated successfully", "order": updated_order}), 200
        else:
            return jsonify({"msg": "No changes made to the order"}), 400

    except Exception as e:
        return jsonify({"msg": "Error updating order status", "error": str(e)}), 500



# Start the Flask app
if __name__ == "__main__":
    print("Starting the server...")
    app.run(host="0.0.0.0", port=8082, debug=True)
