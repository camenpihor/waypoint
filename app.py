"""
curl -X GET http://your-railway-app-url/trees
curl -X PUT http://your-railway-app-url/trees/remove/123 -H "Content-Type: application/json" -d '{"removed_by": "admin"}'
curl -X POST http://your-railway-app-url/trees -H "Content-Type: application/json" -d '{"tree_id": 1, "latin_name": "Quercus robur", "common_name": "English Oak", "is_native": true, "date_added": "2024-08-19T12:34:56", "latitude": 52.5170365, "longitude": 13.3888599, "source": "Survey"}'
"""

import os

from flask import Flask, jsonify, request

from waypoint import postgres

DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)


@app.route("/trees", methods=["GET"])
def get_trees():
    query = "SELECT * FROM tree_locations WHERE removed_by IS NULL;"
    with postgres.connect(DATABASE_URL) as cursor:
        cursor.execute(query)
        response = cursor.fetchall()

    tree_list = [
        {
            "location_id": tree[0],
            "tree_id": tree[1],
            "latin_name": tree[2],
            "common_name": tree[3],
            "is_native": tree[4],
            "date_added": tree[5],
            "latitude": tree[6],
            "longitude": tree[7],
            "source": tree[8],
            "removed_by": tree[9],
        }
        for tree in response
    ]
    return jsonify(tree_list), 200


@app.route("/trees/remove/<int:location_id>", methods=["PUT"])
def remove_tree(location_id):
    query = """
UPDATE tree_locations
SET removed_by = %s
WHERE location_id = %s
RETURNING location_id;
"""
    data = request.json
    removed_by = data.get("removed_by", None)
    if not removed_by:
        return jsonify({"message": 'Missing "removed_by" in request body'}), 400

    with postgres.connect(DATABASE_URL) as cursor:
        cursor.execute(query, (removed_by, location_id))
        updated_rows = cursor.rowcount

    if updated_rows == 0:
        return jsonify({"message": "Tree location not found"}), 404
    return jsonify({"message": f"Tree location {location_id} marked as removed"}), 200


@app.route("/trees", methods=["POST"])
def add_tree():
    query = """
INSERT INTO tree_locations (tree_id, latin_name, common_name, is_native, date_added, latitude, longitude, source, removed_by)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL)
RETURNING location_id;
"""
    data = request.json
    new_tree = (
        data["tree_id"],
        data["latin_name"],
        data["common_name"],
        data.get("is_native"),
        data.get("date_added"),
        data["latitude"],
        data["longitude"],
        data["source"],
    )
    with postgres.connect(DATABASE_URL) as cursor:
        cursor.execute(query, new_tree)
        new_location_id = cursor.fetchone()[0]

    return (
        jsonify({"message": f"New tree location added ({new_location_id})"}),
        201,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
