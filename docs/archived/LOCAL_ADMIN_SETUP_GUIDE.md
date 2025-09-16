# VeriFast Local Admin Setup Guide

This guide explains how to run the VeriFast application in a special "local admin" mode. This allows you to use the full power of the Django admin panel on your local machine to manage content, while the live production server runs a lighter, user-facing version of the application.

## Architecture Overview

The project now supports two run modes, controlled by the `DJANGO_RUN_MODE` environment variable:

-   **`LIGHT` Mode**: This is for the production server. It runs the user-facing website and processes user-submitted articles, but it **disables** the heavyweight content acquisition admin panel and its related background tasks. This makes the server lighter and more focused.
-   **`FULL` Mode**: This is for your local machine. It enables the complete admin panel, allowing you to perform all administrative tasks, including running the content motor. Your local instance will connect directly to the **production database**.

---

## ⚠️ Important Security Notice

Your local admin instance will connect directly to your **production database**. This requires you to put your production database URL and other secrets into a local `.env.local` file.

-   **NEVER** commit the `.env.local` file to Git or share it publicly.
-   Ensure your local machine is secure.
-   Always be careful when working with live production data.

---

## Local Setup Instructions

Follow these steps to set up and run your local admin environment.

### Step 1: Install Dependencies

Ensure you have all the project's Python dependencies installed on your local machine.

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 2: Create Your Local Environment File

The project includes a template file named `.env.local.example`.

1.  **Copy the template:**
    ```bash
    cp .env.local.example .env.local
    ```

2.  **Edit `.env.local`:** Open the new `.env.local` file in a text editor and fill in the following values with your **production credentials**:
    -   `DATABASE_URL`: The full URL for your production PostgreSQL database.
    -   `CELERY_BROKER_URL`: The URL for your production Redis or other Celery broker.
    -   `GEMINI_API_KEY`: Your Google Gemini API key.
    -   `NEWSDATA_API_KEY`: (Optional) Your NewsData.io API key if you use it.

### Step 3: Make the Runner Script Executable

You only need to do this once. This command gives you permission to run the script.

```bash
chmod +x run_local_admin.sh
```

### Step 4: Run the Local Admin Environment

Now you can start the entire local admin environment with a single command:

```bash
./run_local_admin.sh
```

This script will:
1.  Load your secret credentials from `.env.local`.
2.  Start the Django web server on `http://localhost:8000`.
3.  Start a Celery worker that listens for all task queues, including the `acquisition` queue.

You should see output indicating that the server and the Celery worker are running.

### Step 5: Access the Admin Panel

1.  Open your web browser and go to **`http://localhost:8000/admin`**.
2.  Log in with your admin username and password.
3.  You will now see the full admin panel, including the "Content Acquisition" sections and the "Start Content Motor" action on the Articles page. You can now manage your production data and trigger content acquisition directly from your local machine.

### Step 6: Stopping the Environment

To stop the local server and the Celery worker, simply press **`Ctrl+C`** in the terminal where the `./run_local_admin.sh` script is running. The script will handle shutting down both processes gracefully.
