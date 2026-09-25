from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "employee-management-secret-key"

DATABASE = "employees.db"


# ===================================
# DATABASE
# ===================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def create_tables():

    conn = get_db()

    # USERS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # EMPLOYEES TABLE
    conn.execute("""
       CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    department TEXT,
    position TEXT,
    salary REAL,
    joining_date TEXT,
    address TEXT
)
    """)

    # ADD JOINING DATE TO EXISTING DATABASE
    try:

        conn.execute(
            "ALTER TABLE employees ADD COLUMN joining_date TEXT"
        )

        conn.commit()

    except sqlite3.OperationalError:

        # Column already exists
        pass

    conn.close()


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    if "username" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    employees = conn.execute(
        "SELECT * FROM employees ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "home.html",
        employees=employees
    )


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users
                (username, password)
                VALUES (?, ?)
                """,
                (
                    username,
                    hashed_password
                )
            )

            conn.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash(
                "Username already exists.",
                "danger"
            )

        finally:

            conn.close()

    return render_template("register.html")


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT * FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["username"] = username

            return redirect(url_for("home"))

        else:

            flash(
                "Invalid username or password.",
                "danger"
            )

    return render_template("login.html")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==================================================
# ADD EMPLOYEE
# ==================================================

@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():

    if "username" not in session:

        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        phone = request.form["phone"]

        department = request.form["department"]

        position = request.form["position"]

        salary = request.form["salary"]

        joining_date = request.form["joining_date"]

        address = request.form["address"]


        conn = get_db()

        conn.execute(
            """
            INSERT INTO employees
            (
                name,
                email,
                phone,
                department,
                position,
                salary,
                joining_date,
                address
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                phone,
                department,
                position,
                salary,
                joining_date,
                address
            )
        )

        conn.commit()

        conn.close()

        flash(
            "Employee added successfully.",
            "success"
        )

        return redirect(url_for("employee"))

    return render_template(
        "add_employee.html"
    )


# ==================================================
# VIEW EMPLOYEES
# ==================================================

@app.route("/employee")
def employee():

    if "username" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    employees = conn.execute(
        """
        SELECT *
        FROM employees
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "employee.html",
        employees=employees
    )


# ==================================================
# EDIT EMPLOYEE
# ==================================================

@app.route(
    "/edit_employee/<int:id>",
    methods=["GET", "POST"]
)
def edit_employee(id):

    if "username" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    employee = conn.execute(
        """
        SELECT *
        FROM employees
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    if employee is None:

        conn.close()

        flash(
            "Employee not found.",
            "danger"
        )

        return redirect(
            url_for("employee")
        )

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        phone = request.form["phone"]

        department = request.form["department"]

        position = request.form["position"]

        salary = request.form["salary"]

        joining_date = request.form["joining_date"]

        address = request.form["address"]
                

        conn.execute(
            """
            UPDATE employees

            SET
                name = ?,
                email = ?,
                phone = ?,
                department = ?,
                position = ?,
                salary = ?,
                joining_date = ?,
                address = ?

            WHERE id = ?
            """,
            (
                name,
                email,
                phone,
                department,
                position,
                salary,
                joining_date,
                address,
                id
            )
        )

        conn.commit()

        conn.close()

        flash(
            "Employee updated successfully.",
            "success"
        )

        return redirect(
            url_for("employee")
        )

    conn.close()

    return render_template(
        "edit_employee.html",
        employee=employee
    )


# ==================================================
# DELETE EMPLOYEE
# ==================================================

@app.route("/delete_employee/<int:id>")
def delete_employee(id):

    if "username" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM employees
        WHERE id = ?
        """,
        (id,)
    )

    conn.commit()

    conn.close()

    flash(
        "Employee deleted successfully.",
        "success"
    )

    return redirect(
        url_for("employee")
    )


# ==================================================
# SEARCH
# ==================================================

@app.route("/search")
def search():

    if "username" not in session:

        return redirect(url_for("login"))

    query = request.args.get(
        "query",
        ""
    )

    conn = get_db()

    employees = conn.execute(
        """
        SELECT *
        FROM employees

        WHERE name LIKE ?
        OR email LIKE ?
        OR department LIKE ?
        OR position LIKE ?

        ORDER BY id DESC
        """,
        (
            "%" + query + "%",
            "%" + query + "%",
            "%" + query + "%",
            "%" + query + "%"
        )
    ).fetchall()

    conn.close()

    return render_template(
        "search.html",
        employees=employees,
        query=query
    )


# ==================================================
# START APPLICATION
# ==================================================
create_tables()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
