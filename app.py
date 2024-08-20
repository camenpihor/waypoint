"""
curl -X GET http://127.0.0.1:5000/trees
curl -X PUT http://127.0.0.1:5000/trees/remove/123 -H "Content-Type: application/json" -d '{"removed_by": "admin"}'
curl -X POST http://127.0.0.1:5000/trees -H "Content-Type: application/json" -d '{"tree_id": 1, "latin_name": "Quercus robur", "common_name": "English Oak", "is_native": true, "date_added": "2024-08-19T12:34:56", "latitude": 52.5170365, "longitude": 13.3888599, "source": "Survey"}'
"""

import os

from flask import Flask, jsonify, request
from flask_talisman import Talisman

from waypoint import postgres, trees

DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)
Talisman(app)


@app.route("/", methods=["GET"])
def ping() -> tuple[dict, int]:
    return jsonify({"message": "welcome traveller"}), 200


@app.route("/trees", methods=["GET"])
def get_trees() -> tuple[dict, int]:
    with postgres.connect(DATABASE_URL) as client:
        tree_locations = trees.fetch_all(client)
    return jsonify([location.to_dict() for location in tree_locations]), 200


@app.route("/trees/remove/<int:location_id>", methods=["PUT"])
def remove_tree(location_id: int) -> tuple[dict, int]:
    removed_by = request.json.get("removed_by", None)
    if not removed_by:
        return jsonify({"message": 'Missing "removed_by" in request body'}), 400

    with postgres.connect(DATABASE_URL) as client:
        is_success = trees.mark_removed(location_id, removed_by, client=client)

    if not is_success:
        return jsonify({"message": "Tree location not found"}), 404
    return jsonify({"message": f"Tree location {location_id} marked as removed"}), 200


@app.route("/trees", methods=["POST"])
def add_tree() -> tuple[dict, int]:
    necessary_keys = trees.INSERT_KEYS
    if necessary_keys - set(request.json):
        return jsonify({"message": f"Request data must include {necessary_keys}"}), 404
    with postgres.connect(DATABASE_URL) as client:
        new_location = trees.insert(client=client, **request.json)
    return jsonify(new_location.to_dict()), 201


if __name__ == "__main__":
    app.run()
