# **BioTime SMS Notifier**

**Parent Notification System**

---

## **📌 Table of Contents**

1. [**Overview**](#-overview)
2. [**Key Features**](#-key-features)
3. [**System Architecture**](#-system-architecture)
4. [**Installation Guide**](#-installation-guide)
5. [**Configuration**](#-configuration)
6. [**Usage**](#-usage)
7. [**Troubleshooting**](#-troubleshooting)
8. [**Security Considerations**](#-security-considerations)
9. [**API & Integration**](#-api--integration)
10. [**Contributing**](#-contributing)
11. [**License**](#-license)

---

## **🌐 Overview**

The **BioTime SMS Notifier** is an automated system that sends SMS alerts to parents when students check in or out of school using BioTime attendance logs.

### **Purpose**

- **Real-time notifications** via SMS
- **Automated tracking** of student attendance
- **Secure & reliable** message delivery

### **Supported Platforms**

- **Windows 10/11** (64-bit recommended)
- **Python 3.8+**

---

## **🚀 Key Features**

| Feature                     | Description                                             |
| --------------------------- | ------------------------------------------------------- |
| **Automated SMS Alerts**    | Sends messages when students check in/out               |
| **CSV Intergration**        | Reads parent contact details from `parent_contact.csv`  |
| **Log Tracking**            | Prevents duplicate messages with `sent_sms_tracker.txt` |
| **Error Handling**          | Retries failed SMS sends (configurable attempts)        |
| **Customizable Messages**   | Supports dynamic placeholders (`{name}`, `{time}`)      |
| **Windows Service Support** | Can run as a background service                         |

---

## **🏗 System Architecture**

### **📂 File Structure**

```plaintext
BioTimeSMSNotifier/
├── biotime_sms_notifier.py  # Main Python script
├── config.ini               # Configuration file
├── parent_contact.csv      # Student-parent database
├── sent_sms_tracker.txt     # Log of sent messages
├── logs/                    # BioTime attendance logs
│   └── *.csv                # BioTime-generated CSV files
└── biotime_sms_notifier.log # Application logs
```

### **🔧 Component Workflow**

1. **Log Monitor** → Watches for new BioTime CSV files
2. **Data Parser** → Extracts `EmpCode`, `Time`, and `Date`
3. **CSV Lookup** → Matches student with parent’s phone number
4. **SMS Gateway** → Sends message via EgoSMS API
5. **Logging** → Records sent messages to prevent duplicates

---

## **📥 Installation Guide**

### **Prerequisites**

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Pandas & Requests** (`pip install pandas requests`)

### **Step-by-Step Setup**

1. **Clone/Download the Repository**

   ```bash
   git clone https://github.com/kasimlyee/Biotime-SMS-Notifier.git
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure `config.ini`**

   ```ini
   [general]
   log_folder = "C:/BioTimeLogs"
   sent_log_file = "sent_sms_tracker.txt"

   [sms_gateway]
   url = "https://www.egosms.co/api/v1/json/"
   username = "your_username"
   password = "your_password"
   ```

4. **Prepare CSV File (`parent_contact.csv`)**

   - Must contain columns:
     - `EmpCode` (matches BioTime logs)
     - `ParentNumber` (e.g., `256784071324`)
     - `Name` (student’s name)

5. **Run the Application**
   ```bash
   python biotime_sms_notifier.py
   ```

---

## **⚙ Configuration**

### **`config.ini` Settings**

| Section       | Key                | Description            | Default                                              |
| ------------- | ------------------ | ---------------------- | ---------------------------------------------------- |
| `general`     | `log_folder`       | Path to BioTime logs   | `C:/BioTimeLogs`                                     |
| `general`     | `polling_interval` | Seconds between checks | `60`                                                 |
| `sms_gateway` | `url`              | EgoSMS API endpoint    | `https://www.egosms.co/api/v1/json/`                 |
| `messages`    | `check_in`         | Check-in SMS template  | `"Dear parent, {name} has reached school at {time}"` |

### **Dynamic Message Templates**

- `{name}` → Student’s name
- `{time}` → Check-in/out timestamp

---

## **🖥 Usage**

### **Running Manually**

```bash
python biotime_sms_notifier.py [--config custom_config.ini] [--simulate]
```

### **Running as a Windows Service**

1. **Install NSSM** ([Download](https://nssm.cc/download))
2. **Create Service**
   ```bash
   nssm install BioTimeSMSNotifier
   ```
3. **Configure Service**
   - Set path to Python executable
   - Set working directory

---

## **🔧 Troubleshooting**

### **Common Issues & Fixes**

| Error                   | Solution                                      |
| ----------------------- | --------------------------------------------- |
| **"No CSV file found"** | Verify `log_folder` path in `config.ini`      |
| **"EmpCode not found"** | Check `parent_contact.csv` for matching codes |
| **SMS not sending**     | Verify API credentials in `config.ini`        |

### **Logging & Debugging**

- Check `biotime_sms_notifier.log` for errors
- Enable debug mode:
  ```python
  logging.basicConfig(level=logging.DEBUG)
  ```

---

## **🔒 Security Considerations**

- **Encrypt `config.ini`** if storing sensitive credentials
- **Restrict file permissions** for `parent_contact.csv`
- **Use HTTPS** for API communications

---

## **📡 API & Integration**

### **Supported SMS Gateways**

- **EgoSMS** (default)
- **Twilio** (custom integration possible)

### **Webhook Support**

```python
# Extend send_sms() to include webhook calls
requests.post(webhook_url, json={"status": "sent"})
```

---

## **🤝 Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-option`)
3. Submit a **Pull Request**

---

## **📜 License**

**MIT License**  
© 2025 Kasim Lyee

---

### **📞 Contact**

- **Email:** [kasiimlyee@gmail.com](mailto:kasiimlyee@gmail.com)
- **Phone:** +256784071324 / +256701521269

---
