# 🧪 SmartLab

SmartLab is a web-based laboratory management application designed to simplify the process of managing laboratory reports, records, and user activities.

## 🚀 Features

* User Registration and Login
* Dashboard for managing laboratory information
* Add and manage reports
* Upload CSV files
* View detailed report information
* MongoDB database integration
* Simple and user-friendly web interface
* Secure environment configuration using `.env`

## 🛠️ Technologies Used

* **Frontend:** HTML, CSS, Jinja2 Templates
* **Backend:** Python, Flask
* **Database:** MongoDB
* **Data Processing:** Pandas
* **Report Generation:** ReportLab
* **Version Control:** Git & GitHub

## 📂 Project Structure

```text
SmartLab/
│
├── app.py
├── requirements.txt
├── test_mongodb.py
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── add_report.html
│   ├── report_detail.html
│   └── upload_csv.html
│
├── .gitignore
└── README.md
```

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/JananilakshmiM/SmartLab.git
cd SmartLab
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**

```powershell
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file and add the required MongoDB configuration.

Example:

```env
MONGO_URI=your_mongodb_connection_string
SECRET_KEY=your_secret_key
```

> Do not upload your `.env` file or expose your database credentials.

### 6. Run the application

```bash
python app.py
```

Open the application in your browser at:

```text
http://127.0.0.1:5000
```

## 📊 Application Workflow

```text
User
  ↓
Register / Login
  ↓
Dashboard
  ↓
Add Report / Upload CSV
  ↓
Store & Process Data
  ↓
View Report Details
```

## 🎯 Project Objective

The main objective of SmartLab is to provide a centralized platform for managing laboratory-related data and reports efficiently through a simple web application.

## 🔮 Future Enhancements

* Role-based access control
* Advanced analytics dashboard
* Automated report generation
* Data visualization
* Email notifications
* Cloud deployment
* AI-based laboratory report analysis

## 👩‍💻 Author

**Jananilakshmi M**

B.Tech – Artificial Intelligence and Data Science

## 📄 License

This project is developed for educational and project purposes.
