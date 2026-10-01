# VeriMed Mani

## Project Setup and Run Guide

Follow the steps below to set up and run the project on Ubuntu/Linux.

---

## 1. Go to the Project Folder

Open the terminal and go to the project directory:

```bash
cd ~/ReactLearn/verimedmani
```

Check the project files:

```bash
ls
```

You should see files such as:

```text
requirements.txt
manage.py
```

---

## 2. Create Virtual Environment

Create a Python virtual environment named `venv`:

```bash
python3 -m venv venv
```

If `venv` is not available, install it:

```bash
sudo apt update
sudo apt install python3-venv
```

Then create the virtual environment again:

```bash
python3 -m venv venv
```

---

## 3. Activate Virtual Environment

Activate the virtual environment:

```bash
source venv/bin/activate
```

After activation, your terminal should look similar to:

```text
(venv) ramaraja@ramaraja-ThinkPad-E14-Gen-5:~/ReactLearn/verimedmani$
```

---

## 4. Upgrade pip

After activating the virtual environment:

```bash
python -m pip install --upgrade pip
```

---

## 5. Install Requirements

Install all required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Important

Do NOT use:

```bash
pip install r> requirements.txt
```

The correct command is:

```bash
pip install -r requirements.txt
```

Here `-r` means **read the requirements from the file**.

---

## 6. Check Installed Packages

After installation:

```bash
pip list
```

You can also check:

```bash
pip freeze
```

---

## 7. Run Database Migrations

If this is a Django project, run:

```bash
python manage.py migrate
```

---

## 8. Create Superuser (Optional)

If you need Django admin access:

```bash
python manage.py createsuperuser
```

Follow the instructions in the terminal.

---

## 9. Run the Django Project

Start the development server:

```bash
python manage.py runserver
```

You should see something similar to:

```text
Starting development server at http://127.0.0.1:8000/
```

---

## 10. Open the Project in Browser

Open:

```text
http://127.0.0.1:8000/
```

For Django admin:

```text
http://127.0.0.1:8000/admin/
```

---

## 11. Complete Setup Commands

For a fresh setup, you can follow these commands in order:

```bash
cd ~/ReactLearn/verimedmani

python3 -m venv venv

source venv/bin/activate

python -m pip install --upgrade pip

pip install -r requirements.txt

python manage.py migrate

python manage.py runserver
```

---

## 12. Deactivate Virtual Environment

When you finish working on the project:

```bash
deactivate
```

---

## 13. Next Time You Open the Project

You do not need to create the virtual environment again.

Just run:

```bash
cd ~/ReactLearn/verimedmani

source venv/bin/activate

python manage.py runserver
```

---

## Project Structure

A basic Django project should look similar to:

```text
verimedmani/
│
├── venv/
├── manage.py
├── requirements.txt
├── README.md
│
├── project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
└── app/
    ├── migrations/
    ├── models.py
    ├── views.py
    ├── urls.py
    └── serializers.py
```

---

## Git Commands

Check the current Git status:

```bash
git status
```

Pull the latest code:

```bash
git pull origin main
```

After making changes:

```bash
git add .
git commit -m "Update project"
git push origin main
```
