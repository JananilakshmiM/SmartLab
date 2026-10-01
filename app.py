from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    send_file,
    jsonify
)

from pymongo import MongoClient

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from bson.objectid import ObjectId

from datetime import datetime

from io import BytesIO, StringIO
import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.enums import TA_CENTER

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ==================================================
# FLASK APPLICATION
# ==================================================

app = Flask(__name__)

app.secret_key = "smartlab_secret_key_2026"


# ==================================================
# MONGODB CONNECTION
# ==================================================

client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000
)

try:

    client.admin.command("ping")

    print("MongoDB connection successful!")

except Exception as e:

    print("MongoDB connection failed!")
    print(e)


db = client["smartlab"]

patients = db["patients"]

lab_tests = db["lab_tests"]

lab_reports = db["lab_reports"]


# ==================================================
# DEFAULT LABORATORY TESTS
# ==================================================

DEFAULT_TESTS = [

    {
        "test_name": "Hemoglobin",
        "unit": "g/dL",
        "lower_limit": 12.0,
        "upper_limit": 17.0
    },

    {
        "test_name": "Fasting Blood Glucose",
        "unit": "mg/dL",
        "lower_limit": 70.0,
        "upper_limit": 99.0
    },

    {
        "test_name": "Total Cholesterol",
        "unit": "mg/dL",
        "lower_limit": 125.0,
        "upper_limit": 200.0
    },

    {
        "test_name": "HDL",
        "unit": "mg/dL",
        "lower_limit": 40.0,
        "upper_limit": 60.0
    },

    {
        "test_name": "LDL",
        "unit": "mg/dL",
        "lower_limit": 0.0,
        "upper_limit": 130.0
    },

    {
        "test_name": "Triglycerides",
        "unit": "mg/dL",
        "lower_limit": 0.0,
        "upper_limit": 150.0
    },

    {
        "test_name": "WBC",
        "unit": "cells/uL",
        "lower_limit": 4000.0,
        "upper_limit": 11000.0
    },

    {
        "test_name": "Platelets",
        "unit": "cells/uL",
        "lower_limit": 150000.0,
        "upper_limit": 450000.0
    }

]


# ==================================================
# INITIALIZE LABORATORY TESTS
# ==================================================

def initialize_tests():

    if lab_tests.count_documents({}) == 0:

        lab_tests.insert_many(
            DEFAULT_TESTS
        )

        print(
            "Default laboratory tests inserted."
        )

    else:

        print(
            "Laboratory tests already exist."
        )


initialize_tests()


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ==================================================
# REGISTER
# ==================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        age = request.form.get(
            "age"
        )

        gender = request.form.get(
            "gender"
        )


        # ------------------------------------------
        # BASIC VALIDATION
        # ------------------------------------------

        if not name or not email or not password:

            flash(
                "Please fill in all required fields.",
                "danger"
            )

            return redirect(
                "/register"
            )


        # ------------------------------------------
        # CHECK EXISTING EMAIL
        # ------------------------------------------

        existing_patient = patients.find_one({

            "email": email

        })


        if existing_patient:

            flash(
                "Email already registered.",
                "danger"
            )

            return redirect(
                "/register"
            )


        # ------------------------------------------
        # HASH PASSWORD
        # ------------------------------------------

        hashed_password = generate_password_hash(
            password
        )


        # ------------------------------------------
        # CONVERT AGE
        # ------------------------------------------

        try:

            age_value = (
                int(age)
                if age
                else None
            )

        except ValueError:

            age_value = None


        # ------------------------------------------
        # CREATE PATIENT
        # ------------------------------------------

        patient = {

            "name": name,

            "email": email,

            "password": hashed_password,

            "age": age_value,

            "gender": gender,

            "created_at": datetime.now()

        }


        patients.insert_one(
            patient
        )


        flash(
            "Registration successful! Please login.",
            "success"
        )


        return redirect(
            "/login"
        )


    return render_template(
        "register.html"
    )


# ==================================================
# LOGIN
# ==================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        # ------------------------------------------
        # FIND PATIENT
        # ------------------------------------------

        patient = patients.find_one({

            "email": email

        })


        # ------------------------------------------
        # CHECK PASSWORD
        # ------------------------------------------

        if patient and check_password_hash(

            patient["password"],

            password

        ):

            session["patient_id"] = str(
                patient["_id"]
            )

            session["patient_name"] = patient[
                "name"
            ]


            flash(
                "Login successful!",
                "success"
            )


            return redirect(
                "/dashboard"
            )


        flash(
            "Invalid email or password.",
            "danger"
        )


    return render_template(
        "login.html"
    )


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()


    flash(
        "You have been logged out.",
        "info"
    )


    return redirect("/")


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    # ----------------------------------------------
    # LOGIN CHECK
    # ----------------------------------------------

    if "patient_id" not in session:

        return redirect("/login")


    try:

        patient_id = ObjectId(
            session["patient_id"]
        )

    except Exception:

        session.clear()

        return redirect("/login")


    # ----------------------------------------------
    # GET PATIENT REPORTS
    # ----------------------------------------------

    reports = list(

        lab_reports.find({

            "patient_id": patient_id

        }).sort(

            "report_date",
            -1

        )

    )


    # ----------------------------------------------
    # DASHBOARD STATISTICS
    # ----------------------------------------------

    total_reports = len(
        reports
    )

    total_results = 0

    flagged_results = 0

    # New Health Status Summary counts
    within_count = 0
    below_count = 0
    above_count = 0


    for report in reports:

        for result in report.get(
            "results",
            []
        ):

            total_results += 1

            status = result.get(
                "status",
                ""
            )

            if status == "Within Range":

                within_count += 1

            elif status == "Below Range":

                below_count += 1

            elif status == "Above Range":

                above_count += 1


    # Total results outside the configured reference range
    flagged_results = (
        below_count
        + above_count
    )


    # ----------------------------------------------
    # RENDER DASHBOARD
    # ----------------------------------------------

    return render_template(

        "dashboard.html",

        reports=reports,

        total_reports=total_reports,

        total_results=total_results,

        flagged_results=flagged_results,

        within_count=within_count,

        below_count=below_count,

        above_count=above_count

    )


# ==================================================
# ADD LABORATORY REPORT
# ==================================================

@app.route(
    "/add-report",
    methods=["GET", "POST"]
)
def add_report():

    # ----------------------------------------------
    # LOGIN CHECK
    # ----------------------------------------------

    if "patient_id" not in session:

        return redirect("/login")


    # ----------------------------------------------
    # GET AVAILABLE TESTS
    # ----------------------------------------------

    tests = list(

        lab_tests.find().sort(

            "test_name",
            1

        )

    )


    # ----------------------------------------------
    # POST REQUEST
    # ----------------------------------------------

    if request.method == "POST":

        report_date = request.form.get(
            "report_date"
        )


        # ------------------------------------------
        # VALIDATE DATE
        # ------------------------------------------

        if not report_date:

            flash(
                "Please select the laboratory report date.",
                "danger"
            )

            return redirect(
                "/add-report"
            )


        results = []


        # ------------------------------------------
        # PROCESS EACH LAB TEST
        # ------------------------------------------

        for test in tests:

            field_name = (
                "test_"
                + str(
                    test["_id"]
                )
            )


            value = request.form.get(
                field_name
            )


            # --------------------------------------
            # SKIP EMPTY VALUES
            # --------------------------------------

            if (
                value is None
                or value.strip() == ""
            ):

                continue


            # --------------------------------------
            # CONVERT VALUE TO NUMBER
            # --------------------------------------

            try:

                value = float(
                    value
                )

            except ValueError:

                continue


            # --------------------------------------
            # REFERENCE RANGE
            # --------------------------------------

            lower = float(
                test["lower_limit"]
            )

            upper = float(
                test["upper_limit"]
            )


            # --------------------------------------
            # DETERMINE STATUS
            # --------------------------------------

            if value < lower:

                status = "Below Range"

            elif value > upper:

                status = "Above Range"

            else:

                status = "Within Range"


            # --------------------------------------
            # STORE RESULT
            # --------------------------------------

            results.append({

                "test_id":
                    str(
                        test["_id"]
                    ),

                "test_name":
                    test["test_name"],

                "value":
                    value,

                "unit":
                    test["unit"],

                "lower_limit":
                    lower,

                "upper_limit":
                    upper,

                "status":
                    status

            })


        # ------------------------------------------
        # CHECK RESULTS
        # ------------------------------------------

        if len(results) == 0:

            flash(
                "Please enter at least one test value.",
                "danger"
            )

            return redirect(
                "/add-report"
            )


        # ------------------------------------------
        # CREATE REPORT
        # ------------------------------------------

        report = {

            "patient_id":

                ObjectId(
                    session["patient_id"]
                ),

            "report_date":

                report_date,

            "results":

                results,

            "source":

                "Manual Entry",

            "created_at":

                datetime.now()

        }


        # ------------------------------------------
        # SAVE REPORT
        # ------------------------------------------

        lab_reports.insert_one(
            report
        )


        flash(
            "Laboratory report saved successfully!",
            "success"
        )


        return redirect(
            "/dashboard"
        )


    # ----------------------------------------------
    # SHOW PAGE
    # ----------------------------------------------

    return render_template(

        "add_report.html",

        tests=tests

    )


# ==================================================
# UPLOAD LABORATORY REPORT FROM CSV
# ==================================================

@app.route(
    "/upload-csv",
    methods=["GET", "POST"]
)
def upload_csv():

    # ----------------------------------------------
    # LOGIN CHECK
    # ----------------------------------------------

    if "patient_id" not in session:
        return redirect("/login")

    # ----------------------------------------------
    # POST REQUEST
    # ----------------------------------------------

    if request.method == "POST":

        report_date = request.form.get(
            "report_date",
            ""
        ).strip()

        csv_file = request.files.get(
            "csv_file"
        )

        # ------------------------------------------
        # VALIDATE DATE
        # ------------------------------------------

        if not report_date:

            flash(
                "Please select the laboratory report date.",
                "danger"
            )

            return redirect("/upload-csv")

        # ------------------------------------------
        # VALIDATE FILE
        # ------------------------------------------

        if (
            csv_file is None
            or not csv_file.filename
        ):

            flash(
                "Please select a CSV file.",
                "danger"
            )

            return redirect("/upload-csv")

        if not csv_file.filename.lower().endswith(".csv"):

            flash(
                "Only CSV files are allowed.",
                "danger"
            )

            return redirect("/upload-csv")

        try:

            # --------------------------------------
            # READ UPLOADED FILE
            # --------------------------------------
            # IMPORTANT:
            # Do NOT wrap csv_file.stream in TextIOWrapper.
            # Flask uses a SpooledTemporaryFile and that caused:
            # "'SpooledTemporaryFile' object has no attribute 'readable'"
            #
            # Reading the bytes first and then using StringIO
            # avoids that problem.

            file_bytes = csv_file.read()

            if not file_bytes:
                flash(
                    "The CSV file is empty.",
                    "danger"
                )
                return redirect("/upload-csv")

            csv_text = file_bytes.decode(
                "utf-8-sig"
            )

            reader = csv.DictReader(
                StringIO(csv_text)
            )

            # --------------------------------------
            # CHECK CSV HEADER
            # --------------------------------------

            if not reader.fieldnames:

                flash(
                    "CSV file is empty or has no header row.",
                    "danger"
                )

                return redirect("/upload-csv")

            # Normalize headers so these variations work:
            # Test Name / test name / TEST NAME
            # Value / value / VALUE

            normalized_headers = {}

            for field in reader.fieldnames:

                if field is not None:

                    normalized_headers[
                        field.strip().lower()
                    ] = field

            if (
                "test name" not in normalized_headers
                or "value" not in normalized_headers
            ):

                flash(
                    "CSV must contain 'Test Name' and 'Value' columns.",
                    "danger"
                )

                return redirect("/upload-csv")

            test_name_column = normalized_headers[
                "test name"
            ]

            value_column = normalized_headers[
                "value"
            ]

            # --------------------------------------
            # GET LAB TESTS
            # --------------------------------------

            tests = list(
                lab_tests.find()
            )

            test_lookup = {}

            for test in tests:

                test_name = str(
                    test.get(
                        "test_name",
                        ""
                    )
                ).strip().lower()

                if test_name:

                    test_lookup[
                        test_name
                    ] = test

            # --------------------------------------
            # PROCESS CSV ROWS
            # --------------------------------------

            results = []

            row_number = 1

            for row in reader:

                row_number += 1

                test_name = str(
                    row.get(
                        test_name_column,
                        ""
                    )
                ).strip()

                value_text = str(
                    row.get(
                        value_column,
                        ""
                    )
                ).strip()

                # Skip completely empty rows

                if (
                    not test_name
                    and not value_text
                ):
                    continue

                # Test name validation

                if not test_name:

                    flash(
                        f"Test name missing in CSV row {row_number}.",
                        "danger"
                    )

                    return redirect("/upload-csv")

                # Value validation

                if not value_text:

                    flash(
                        f"Value missing for {test_name} in CSV row {row_number}.",
                        "danger"
                    )

                    return redirect("/upload-csv")

                try:

                    value = float(
                        value_text
                    )

                except ValueError:

                    flash(
                        f"Invalid value for {test_name} in CSV row {row_number}.",
                        "danger"
                    )

                    return redirect("/upload-csv")

                # ----------------------------------
                # FIND CONFIGURED TEST
                # ----------------------------------

                test = test_lookup.get(
                    test_name.lower()
                )

                if test is None:

                    flash(
                        f"Test '{test_name}' is not configured in SmartLab.",
                        "danger"
                    )

                    return redirect("/upload-csv")

                # ----------------------------------
                # REFERENCE RANGE
                # ----------------------------------

                lower = float(
                    test.get(
                        "lower_limit",
                        0
                    )
                )

                upper = float(
                    test.get(
                        "upper_limit",
                        0
                    )
                )

                # ----------------------------------
                # DETERMINE STATUS
                # ----------------------------------

                if value < lower:

                    status = "Below Range"

                elif value > upper:

                    status = "Above Range"

                else:

                    status = "Within Range"

                # ----------------------------------
                # STORE RESULT
                # ----------------------------------

                results.append({

                    "test_id":
                        str(
                            test["_id"]
                        ),

                    "test_name":
                        test.get(
                            "test_name",
                            test_name
                        ),

                    "value":
                        value,

                    "unit":
                        test.get(
                            "unit",
                            ""
                        ),

                    "lower_limit":
                        lower,

                    "upper_limit":
                        upper,

                    "status":
                        status

                })

            # --------------------------------------
            # CHECK RESULTS
            # --------------------------------------

            if not results:

                flash(
                    "No valid laboratory results were found in the CSV.",
                    "danger"
                )

                return redirect("/upload-csv")

            # --------------------------------------
            # CREATE REPORT
            # --------------------------------------

            report = {

                "patient_id":
                    ObjectId(
                        session["patient_id"]
                    ),

                "report_date":
                    report_date,

                "results":
                    results,

                "source":
                    "CSV Upload",

                "created_at":
                    datetime.now()

            }

            # --------------------------------------
            # SAVE REPORT
            # --------------------------------------

            lab_reports.insert_one(
                report
            )

            flash(
                "CSV laboratory report uploaded successfully!",
                "success"
            )

            return redirect(
                "/dashboard"
            )

        except UnicodeDecodeError:

            flash(
                "Unable to read the CSV file. Please save it as UTF-8 CSV.",
                "danger"
            )

            return redirect(
                "/upload-csv"
            )

        except Exception as e:

            print(
                "CSV upload error:",
                repr(e)
            )

            flash(
                "Unable to process the CSV file.",
                "danger"
            )

            return redirect(
                "/upload-csv"
            )

    # ----------------------------------------------
    # SHOW UPLOAD PAGE
    # ----------------------------------------------

    return render_template(
        "upload_csv.html"
    )


# ==================================================
# VIEW INDIVIDUAL LAB REPORT
# ==================================================

@app.route(
    "/report/<report_id>"
)
def view_report(report_id):

    # ----------------------------------------------
    # LOGIN CHECK
    # ----------------------------------------------

    if "patient_id" not in session:

        return redirect("/login")


    # ----------------------------------------------
    # VALIDATE REPORT ID
    # ----------------------------------------------

    try:

        report_object_id = ObjectId(
            report_id
        )

    except Exception:

        return "Invalid report ID", 400


    # ----------------------------------------------
    # GET REPORT
    # ----------------------------------------------

    try:

        report = lab_reports.find_one({

            "_id":
                report_object_id,

            "patient_id":
                ObjectId(
                    session["patient_id"]
                )

        })

    except Exception:

        return "Unable to retrieve report.", 500


    # ----------------------------------------------
    # REPORT NOT FOUND
    # ----------------------------------------------

    if report is None:

        return "Report not found.", 404


    # ----------------------------------------------
    # GET RESULTS
    # ----------------------------------------------

    results = report.get(
        "results",
        []
    )


    # ----------------------------------------------
    # CALCULATE SUMMARY
    # ----------------------------------------------

    total_tests = len(
        results
    )

    within_count = 0

    below_count = 0

    above_count = 0


    for result in results:

        status = result.get(
            "status",
            ""
        )


        if status == "Within Range":

            within_count += 1


        elif status == "Below Range":

            below_count += 1


        elif status == "Above Range":

            above_count += 1


    # ----------------------------------------------
    # REPORT SOURCE
    # ----------------------------------------------

    source = report.get(
        "source",
        "Manual Entry"
    )


    # ----------------------------------------------
    # SHOW REPORT
    # ----------------------------------------------

    return render_template(

        "report_detail.html",

        report=report,

        total_tests=total_tests,

        within_count=within_count,

        below_count=below_count,

        above_count=above_count,

        source=source

    )


# ==================================================
# HISTORICAL TREND DATA API
# ==================================================

@app.route(
    "/api/trends"
)
def get_trends():

    # ----------------------------------------------
    # LOGIN CHECK
    # ----------------------------------------------

    if "patient_id" not in session:

        return jsonify({

            "error":
                "Please login first."

        }), 401


    # ----------------------------------------------
    # GET PATIENT ID
    # ----------------------------------------------

    try:

        patient_id = ObjectId(
            session["patient_id"]
        )

    except Exception:

        return jsonify({

            "error":
                "Invalid patient session."

        }), 400


    # ----------------------------------------------
    # GET REPORTS
    # ----------------------------------------------

    reports = list(

        lab_reports.find({

            "patient_id":
                patient_id

        }).sort(

            "report_date",
            1

        )

    )


    # ----------------------------------------------
    # CREATE TREND STRUCTURE
    # ----------------------------------------------

    trends = {}


    # ----------------------------------------------
    # PROCESS REPORTS
    # ----------------------------------------------

    for report in reports:

        report_date = report.get(
            "report_date",
            ""
        )


        for result in report.get(
            "results",
            []
        ):

            test_name = result.get(
                "test_name"
            )


            if not test_name:

                continue


            # --------------------------------------
            # CREATE TEST ENTRY
            # --------------------------------------

            if test_name not in trends:

                trends[test_name] = {

                    "unit":
                        result.get(
                            "unit",
                            ""
                        ),

                    "lower_limit":
                        result.get(
                            "lower_limit",
                            0
                        ),

                    "upper_limit":
                        result.get(
                            "upper_limit",
                            0
                        ),

                    "dates": [],

                    "values": [],

                    "statuses": [],

                    "units": []

                }


            # --------------------------------------
            # ADD DATE
            # --------------------------------------

            trends[test_name][
                "dates"
            ].append(

                report_date

            )


            # --------------------------------------
            # ADD VALUE
            # --------------------------------------

            trends[test_name][
                "values"
            ].append(

                result.get(
                    "value",
                    0
                )

            )


            # --------------------------------------
            # ADD STATUS
            # --------------------------------------

            trends[test_name][
                "statuses"
            ].append(

                result.get(
                    "status",
                    "Unknown"
                )

            )


            # --------------------------------------
            # ADD UNIT
            # --------------------------------------

            trends[test_name][
                "units"
            ].append(

                result.get(
                    "unit",
                    ""
                )

            )


    # ----------------------------------------------
    # RETURN JSON
    # ----------------------------------------------

    return jsonify(
        trends
    )


# ==================================================
# DOWNLOAD LABORATORY REPORT AS PDF
# ==================================================

@app.route(
    "/download-report/<report_id>"
)
def download_report(report_id):

    # ----------------------------------------------
    # LOGIN CHECK
    # ----------------------------------------------

    if "patient_id" not in session:

        return redirect("/login")


    # ----------------------------------------------
    # VALIDATE REPORT ID
    # ----------------------------------------------

    try:

        report_object_id = ObjectId(
            report_id
        )

    except Exception:

        return "Invalid report ID", 400


    # ----------------------------------------------
    # GET REPORT
    # ----------------------------------------------

    report = lab_reports.find_one({

        "_id":
            report_object_id,

        "patient_id":
            ObjectId(
                session["patient_id"]
            )

    })


    # ----------------------------------------------
    # REPORT NOT FOUND
    # ----------------------------------------------

    if report is None:

        return "Report not found.", 404


    # ----------------------------------------------
    # GET PATIENT
    # ----------------------------------------------

    patient = patients.find_one({

        "_id":
            ObjectId(
                session["patient_id"]
            )

    })


    if patient is None:

        return "Patient not found.", 404


    # ----------------------------------------------
    # CREATE PDF BUFFER
    # ----------------------------------------------

    buffer = BytesIO()


    # ----------------------------------------------
    # CREATE PDF DOCUMENT
    # ----------------------------------------------

    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=40,

        leftMargin=40,

        topMargin=40,

        bottomMargin=40

    )


    # ----------------------------------------------
    # PDF STYLES
    # ----------------------------------------------

    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(

        "TitleStyle",

        parent=styles["Title"],

        fontSize=22,

        leading=26,

        alignment=TA_CENTER,

        textColor=colors.HexColor(
            "#0f766e"
        ),

        spaceAfter=10

    )


    subtitle_style = ParagraphStyle(

        "SubtitleStyle",

        parent=styles["Normal"],

        fontSize=10,

        leading=14,

        alignment=TA_CENTER,

        textColor=colors.HexColor(
            "#64748b"
        ),

        spaceAfter=20

    )


    heading_style = ParagraphStyle(

        "HeadingStyle",

        parent=styles["Heading2"],

        fontSize=14,

        leading=18,

        textColor=colors.HexColor(
            "#0f766e"
        ),

        spaceBefore=10,

        spaceAfter=10

    )


    disclaimer_style = ParagraphStyle(

        "DisclaimerStyle",

        parent=styles["Normal"],

        fontSize=8,

        leading=12,

        textColor=colors.HexColor(
            "#854d0e"
        ),

        alignment=TA_CENTER

    )


    # ----------------------------------------------
    # PDF ELEMENTS
    # ----------------------------------------------

    elements = []


    # ----------------------------------------------
    # TITLE
    # ----------------------------------------------

    elements.append(

        Paragraph(
            "SmartLab",
            title_style
        )

    )


    elements.append(

        Paragraph(
            "Laboratory Report",
            subtitle_style
        )

    )


    # ----------------------------------------------
    # PATIENT INFORMATION
    # ----------------------------------------------

    elements.append(

        Paragraph(
            "Patient Information",
            heading_style
        )

    )


    patient_name = patient.get(
        "name",
        "N/A"
    )

    patient_email = patient.get(
        "email",
        "N/A"
    )

    patient_age = patient.get(
        "age",
        "N/A"
    )

    patient_gender = patient.get(
        "gender",
        "N/A"
    )


    patient_data = [

        [
            "Patient Name",
            patient_name
        ],

        [
            "Email",
            patient_email
        ],

        [
            "Age",
            str(patient_age)
        ],

        [
            "Gender",
            str(patient_gender)
        ],

        [
            "Report Date",
            report.get(
                "report_date",
                "N/A"
            )
        ],

        [
            "Report Source",
            report.get(
                "source",
                "Manual Entry"
            )
        ]

    ]


    patient_table = Table(

        patient_data,

        colWidths=[
            150,
            340
        ]

    )


    patient_table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#f0fdfa"
                )
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#0f766e"
                )
            ),

            (
                "FONTNAME",
                (0, 0),
                (0, -1),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor(
                    "#cbd5e1"
                )
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])

    )


    elements.append(
        patient_table
    )


    elements.append(
        Spacer(1, 20)
    )


    # ----------------------------------------------
    # TEST RESULTS
    # ----------------------------------------------

    elements.append(

        Paragraph(
            "Laboratory Test Results",
            heading_style
        )

    )


    table_data = [

        [
            "Test",
            "Value",
            "Unit",
            "Reference Range",
            "Status"
        ]

    ]


    for result in report.get(
        "results",
        []
    ):

        test_name = result.get(
            "test_name",
            "N/A"
        )

        value = result.get(
            "value",
            "N/A"
        )

        unit = result.get(
            "unit",
            "N/A"
        )

        lower = result.get(
            "lower_limit",
            "N/A"
        )

        upper = result.get(
            "upper_limit",
            "N/A"
        )

        status = result.get(
            "status",
            "N/A"
        )


        reference_range = (

            str(lower)
            + " - "
            + str(upper)

        )


        table_data.append([

            test_name,

            str(value),

            unit,

            reference_range,

            status

        ])


    results_table = Table(

        table_data,

        colWidths=[
            115,
            60,
            65,
            100,
            100
        ],

        repeatRows=1

    )


    # ----------------------------------------------
    # TABLE STYLE
    # ----------------------------------------------

    table_style = [

        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor(
                "#0f766e"
            )
        ),

        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),

        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold"
        ),

        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            8
        ),

        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor(
                "#cbd5e1"
            )
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),

        (
            "PADDING",
            (0, 0),
            (-1, -1),
            7
        )

    ]


    # ----------------------------------------------
    # STATUS COLORS
    # ----------------------------------------------

    for row_index, result in enumerate(

        report.get(
            "results",
            []
        ),

        start=1

    ):

        status = result.get(
            "status",
            ""
        )


        if status == "Within Range":

            table_style.append(

                (
                    "TEXTCOLOR",
                    (4, row_index),
                    (4, row_index),
                    colors.HexColor(
                        "#15803d"
                    )
                )

            )


        elif status == "Below Range":

            table_style.append(

                (
                    "TEXTCOLOR",
                    (4, row_index),
                    (4, row_index),
                    colors.HexColor(
                        "#b45309"
                    )
                )

            )


        elif status == "Above Range":

            table_style.append(

                (
                    "TEXTCOLOR",
                    (4, row_index),
                    (4, row_index),
                    colors.HexColor(
                        "#b91c1c"
                    )
                )

            )


    results_table.setStyle(

        TableStyle(
            table_style
        )

    )


    elements.append(
        results_table
    )


    elements.append(
        Spacer(1, 25)
    )


    # ----------------------------------------------
    # PDF SUMMARY
    # ----------------------------------------------

    elements.append(

        Paragraph(
            "Report Summary",
            heading_style
        )

    )


    pdf_total_tests = len(

        report.get(
            "results",
            []
        )

    )


    pdf_within_count = 0

    pdf_below_count = 0

    pdf_above_count = 0


    for result in report.get(
        "results",
        []
    ):

        status = result.get(
            "status",
            ""
        )


        if status == "Within Range":

            pdf_within_count += 1


        elif status == "Below Range":

            pdf_below_count += 1


        elif status == "Above Range":

            pdf_above_count += 1


    pdf_outside_range = (

        pdf_below_count
        + pdf_above_count

    )


    summary_data = [

        [
            "Total Tests",
            str(pdf_total_tests)
        ],

        [
            "Within Range",
            str(pdf_within_count)
        ],

        [
            "Below Range",
            str(pdf_below_count)
        ],

        [
            "Above Range",
            str(pdf_above_count)
        ],

        [
            "Outside Reference Range",
            str(pdf_outside_range)
        ]

    ]


    summary_table = Table(

        summary_data,

        colWidths=[
            250,
            240
        ]

    )


    summary_table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#f0fdfa"
                )
            ),

            (
                "FONTNAME",
                (0, 0),
                (0, -1),
                "Helvetica-Bold"
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#0f766e"
                )
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor(
                    "#cbd5e1"
                )
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])

    )


    elements.append(
        summary_table
    )


    elements.append(
        Spacer(1, 25)
    )


    # ----------------------------------------------
    # DISCLAIMER
    # ----------------------------------------------

    elements.append(

        Paragraph(

            "<b>Important:</b> SmartLab organizes "
            "laboratory results and displays "
            "reference-range information. This "
            "application does not diagnose medical "
            "conditions. Please discuss abnormal "
            "results with a qualified healthcare "
            "professional.",

            disclaimer_style

        )

    )


    # ----------------------------------------------
    # BUILD PDF
    # ----------------------------------------------

    document.build(
        elements
    )


    # ----------------------------------------------
    # RESET BUFFER
    # ----------------------------------------------

    buffer.seek(0)


    # ----------------------------------------------
    # PDF FILE NAME
    # ----------------------------------------------

    filename = (

        "SmartLab_Report_"

        + str(
            report.get(
                "report_date",
                "report"
            )
        )

        + ".pdf"

    )


    # ----------------------------------------------
    # SEND PDF
    # ----------------------------------------------

    return send_file(

        buffer,

        as_attachment=True,

        download_name=filename,

        mimetype="application/pdf"

    )


# ==================================================
# RUN FLASK APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        use_reloader=False
    )