import os, json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "change-me"  # needed if you later use flash()

# --- Mongo connection ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["flask_demo"]
users_col = db["users"]
todos_col = db["todos"]

# ---------- 1) API route that reads from a backend file ----------
@app.route("/api/users")
def users_api():
    """
    Returns a JSON list from a backend file.
    """
    path = "flask_assignment/data/users.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": f"{path} not found"}), 404
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON in {path}: {e}"}), 500

# ---------- Pages ----------
@app.route("/")
def home():
    return render_template("home.html")

# 2) Create form -> insert into MongoDB -> success page or inline error
@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        form = request.form
        doc = {
            "email": form.get("email", "").strip(),
            "password": form.get("password", ""),   # hash in real apps!
            "address1": form.get("address1", "").strip(),
            "address2": form.get("address2", "").strip(),
            "city": form.get("city", "").strip(),
            "state": form.get("state", "").strip(),
            "zip": form.get("zip", "").strip(),
            "checked": bool(form.get("check")),
        }

        # minimal validation
        if not doc["email"]:
            return render_template("create_user.html",
                                   error="Email is required",
                                   old=form)
        try:
            users_col.insert_one(doc)
            return redirect(url_for("success"))
        except Exception as e:
            # show the error on the same page (no redirect)
            return render_template("create_user.html",
                                   error=str(e),
                                   old=form)

    return render_template("create_user.html", error=None, old={})

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/view_users")
def view_users():
    # fetch all users (hide _id so Jinja can print easily)
    rows = list(users_col.find({}, {"_id": 0}))
    return render_template("view_users.html", rows=rows)

@app.route("/submittodoitem", methods=["POST"])
def submit_todo_item():
    item_name = request.form.get("itemName", "").strip()
    item_desc = request.form.get("itemDescription", "").strip()

    if not item_name:
        return render_template("todo.html", error="Item Name is required", old={"itemName": item_name, "itemDescription": item_desc}), 400
    try:
        todos_col.insert_one({
            "itemName": item_name,
            "itemDescription": item_desc
        })
        return redirect(url_for("list_todos"))
    except Exception as e:
        return render_template("todo.html", error=f"Failed to save: {e}", old={"itemName": item_name, "itemDescription": item_desc}), 500

## ToDo code start here
@app.route("/todo", methods=["GET"])
def todo_page():
    # form page
    return render_template("todo.html", error=None, old={})

@app.route("/todos", methods=["GET"])
def list_todos():
    items = list(todos_col.find({}, {"_id": 0}))
    return render_template("todos.html", items=items)

if __name__ == "__main__":
    app.run(debug=True)
