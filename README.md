# 💰 FinanceSaathi — AI-Powered Expense Management System

🚀 FinanceSaathi is a smart expense tracking platform that enables users to **upload bills or manually enter expenses**, automatically **extracts key information**, categorizes spending, and provides **monthly insights with intelligent warnings**.

---

## 📌 Features

* 📸 **Bill Upload & OCR Processing**
  Upload images of bills and automatically extract expense details like amount and category.

* ✍️ **Manual Expense Entry**
  Users can manually add expenses for flexibility.

* 🧠 **Smart Categorization**
  Automatically classifies expenses into categories such as:

  * 🛒 Shopping
  * 🍔 Food
  * ✈️ Travel
  * 📦 Others

* 📊 **Monthly Expense Analytics**
  Provides a summary of total expenses per category at the end of each month.

* ⚠️ **Spending Alerts**
  Warns users if they are about to exceed their usual spending patterns based on historical data.

* 📈 **Data-Driven Insights**
  Helps users understand and optimize their spending behavior.

---

## 🛠️ Tech Stack

### ⚙️ Backend

* Python (Flask)

### 🗄️ Database

* MongoDB / SQL (depending on implementation)

### 🤖 AI / Processing

* OCR (for bill data extraction)
* Rule-based / logic-based categorization

---

## 🧩 System Architecture

* RESTful backend APIs built with Flask
* Image processing pipeline for extracting bill data
* Database-driven storage of user expenses and history
* Categorization engine for organizing expenses
* Analytics module for generating monthly summaries and alerts

---

## ⚡ Workflow

1. User uploads a bill OR manually enters expense
2. System extracts:

   * Amount
   * Category
3. Expense is stored in database
4. Categorization engine assigns it to a category
5. Monthly analytics calculates:

   * Total spending per category
6. Alert system compares:

   * Current spending vs historical patterns
   * Notifies if overspending risk is detected

---


## ⚡ Getting Started

### 1️⃣ Clone the repository

```bash id="a1b2c3"
git clone https://github.com/ajay5689pal/finance-saathi.git
cd finance-saathi
```

### 2️⃣ Create virtual environment

```bash id="d4e5f6"
python -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)
```

### 3️⃣ Install dependencies

```bash id="g7h8i9"
pip install -r requirements.txt
```

### 4️⃣ Configure database

* Setup MongoDB / SQL database
* Update connection settings in config file

### 5️⃣ Run the application

```bash id="j0k1l2"
python app.py
```

---

## 🔐 Future Improvements

* 🔹 AI-based expense prediction using ML models
* 🔹 Real-time notifications (email / push alerts)
* 🔹 Budget planning dashboard
* 🔹 Integration with bank APIs
* 🔹 Cloud deployment (AWS / Azure)

---

## 📈 Impact

* Helps users **track and control their spending habits**
* Encourages **financial discipline through alerts and insights**
* Provides **automation for expense management using AI concepts**

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork and submit pull requests.

---

## 📬 Contact

👤 Ajay Pal
📧 [Ajay5688pal@gmail.com](mailto:Ajay5688pal@gmail.com)
🔗 LinkedIn | GitHub

---

⭐ If you find this project useful, consider giving it a star!
