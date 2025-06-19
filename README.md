# OceanRithm

**Official MSc Thesis Project – Zahra Kheiroddin | UE Germany**

OceanRithm is a production grade Django platform designed for centralized DevOps orchestration across Jenkins, GitHub Actions, and system level automation. Built as part of a master's thesis at the University of Europe for Applied Sciences, this project features real time Redis WebSocket notifications, cross-platform Jenkins installation, and fully integrated GitHub repository workflows.

> ⚠️ **License & Ownership**: This project is protected under a custom MIT License with Attribution. Unauthorized redistribution, modification, or submission to journals or academic institutions is strictly prohibited. Any use must include clear reference to Zahra Kheiroddin as the sole original creator.

## ✨ Highlights

- 📦 Fully automated Jenkins installation (Linux, Windows, macOS)
- ⚙️ GitHub Actions integration with workflow management
- 🔁 Real-time status via Redis Channels & WebSocket
- 🧠 Tailwind UI + Bootstrap 5 + AJAX dynamic components
- 🔒 Secure login, GitHub token storage, and environment configs

## 📘 IEEE & Academic Use

This project is under evaluation for academic publication (IEEE Conference Submission).
All intellectual property belongs to **Zahra Kheiroddin**, supervised by **Prof. Dr. Rand Kouatly**.

> To cite this software, use:
> `Z. Kheiroddin, "DevOps Hub: A Cross-Platform CI/CD Automation Framework," MSc Thesis, UE Germany, 2025.`

## 📄 License

```text
MIT License with Attribution

Copyright (c) 2025 Zahra Kheiroddin

Permission is granted for personal and non-commercial use with attribution.
Redistribution, commercial use, or academic submission without express written consent is strictly prohibited.
```

See `LICENSE` file for full terms.

---

### ✅ How to Use / Setup

#### 1. Clone the Project from GitHub
```bash
git clone https://github.com/zahrakheiroddin/devops-hub.git
cd devops-hub
```

#### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv env
source env/bin/activate          # macOS/Linux
# On Windows:
# env\Scripts\activate

pip install -r requirements.txt
```

#### 3. Set Up Database & Superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

#### 4. Run the Application
```bash
python manage.py runserver
```

#### 5. Access in Your Browser:
```
http://127.0.0.1:8000
```

#### 6. Redis & WebSocket (Optional Advanced Setup)
If you want to use real-time WebSocket updates:
- Install Redis: `sudo apt install redis` or use Docker: `docker run -p 6379:6379 redis`
- Run Django Channels worker
```bash
python manage.py runworker
```
- Confirm Redis is running on `localhost:6379`

---

### 📬 Contact / Support
- GitHub: [github.com/zahrakheiroddin](https://github.com/zahrakheiroddin)
- Email: `zahra.kheiroddin@ue-germany.de` *(for academic inquiries only)*

---

**OceanRithm - DevOps Hub** | Designed and Engineered by Zahra Kheiroddin

*Secure. Scalable. Academic-grade Automation.*
