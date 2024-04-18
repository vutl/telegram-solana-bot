from flask import Flask, jsonify
import json

app = Flask(__name__)
active_pool_folder = 'active_pool'

def get_pool_data(index0):
    json_file_path = f"{active_pool_folder}/{index0}.json"
    try:
        with open(json_file_path, 'r') as json_file:
            pool_data = json.load(json_file)
            return jsonify(pool_data)
    except FileNotFoundError:
        return jsonify({"error": "Pool data not found for the provided token_address"}), 404

@app.route('/<string:index0>')
def show_pool_data(index0):
    return get_pool_data(index0)

if __name__ == '__main__':
    app.run(debug=True)
