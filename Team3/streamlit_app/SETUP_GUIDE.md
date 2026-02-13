# Team 3 Dashboard — Local Setup Guide

A quick guide to run the compiled multi-page dashboard on your local machine.

---

## Prerequisites

- **Python 3.10+** (3.12 or 3.13 recommended)
- **Git** (to clone the repo)
- The `SGJobData.db` database file (already in `Team3/data/raw/`)

---

## Step 1: Clone the Repository

Skip this if you already have the repo on your machine.

**Mac / Linux:**
```bash
git clone https://github.com/tehmenghai/SGJobData-Visualization-Assignment.git
cd SGJobData-Visualization-Assignment
```

**Windows (Command Prompt or PowerShell):**
```cmd
git clone https://github.com/tehmenghai/SGJobData-Visualization-Assignment.git
cd SGJobData-Visualization-Assignment
```

---

## Step 2: Install Dependencies

**Mac / Linux:**
```bash
pip3 install streamlit duckdb plotly pandas numpy scikit-learn
```

**Windows:**
```cmd
pip install streamlit duckdb plotly pandas numpy scikit-learn
```

> **Tip:** If you use a virtual environment (recommended), create and activate it first:
>
> **Mac / Linux:**
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip install streamlit duckdb plotly pandas numpy scikit-learn
> ```
>
> **Windows:**
> ```cmd
> python -m venv venv
> venv\Scripts\activate
> pip install streamlit duckdb plotly pandas numpy scikit-learn
> ```

---

## Step 3: Run the Dashboard

Navigate to the `streamlit_app` folder and run `main.py`:

**Mac / Linux:**
```bash
cd Team3/streamlit_app
streamlit run main.py
```

**Windows:**
```cmd
cd Team3\streamlit_app
streamlit run main.py
```

The app will open automatically in your browser at **http://localhost:8501**.

---

## Running on a Custom Port

If port 8501 is already in use:

**Mac / Linux:**
```bash
streamlit run main.py --server.port 8502
```

**Windows:**
```cmd
streamlit run main.py --server.port 8502
```

---

## Running Your Individual Dashboard (Standalone)

You can still run your own dashboard independently for development:

**Mac / Linux:**
```bash
# Example: run MengHai's app standalone
cd Team3/streamlit_app/MengHai
streamlit run app.py

# Example: run LikHong's app standalone
cd Team3/streamlit_app/LikHong
streamlit run sgjobs.py
```

**Windows:**
```cmd
cd Team3\streamlit_app\MengHai
streamlit run app.py

cd Team3\streamlit_app\LikHong
streamlit run sgjobs.py
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named ..."

Install the missing package:
```bash
pip install <package_name>
```

### "Database not found" error

Make sure the database file exists at:
```
Team3/data/raw/SGJobData.db
```

If the file is tracked with Git LFS, run:
```bash
git lfs pull
```

### "Address already in use" error

Another Streamlit instance is using the port. Either:
- Stop the other instance, or
- Use a different port: `streamlit run main.py --server.port 8502`

### Streamlit asks for email on first run

Press **Enter** to skip, or run with headless mode:
```bash
streamlit run main.py --server.headless true
```

---

## Project Structure

```
Team3/streamlit_app/
├── main.py                              # Landing page (run this)
├── pages/
│   ├── 1_Dashboard_(Lanson).py          # Lanson's dashboard
│   ├── 2_Salary_Explorer_(Meng_Hai).py  # Meng Hai's dashboard
│   ├── 3_Job_Concierge_(Lik_Hong).py    # Lik Hong's dashboard
│   ├── 4_Dashboard_(Ben_Au).py          # Ben Au's dashboard
│   ├── 5_Dashboard_(Huey_Ling).py       # Huey Ling's dashboard
│   └── 6_Dashboard_(Kendra_Lai).py      # Kendra Lai's dashboard
├── BenAu/                               # Individual folder
├── HueyLing/                            # Individual folder
├── KendraLai/                           # Individual folder
├── Lanson/                              # Individual folder
├── LikHong/                             # Individual folder
└── MengHai/                             # Individual folder
```

---

## Adding Your Dashboard to the Compiled App

1. Build your dashboard in your own folder (e.g., `BenAu/app.py`)
2. Create or update your wrapper page in `pages/` (e.g., `4_Dashboard_(Ben_Au).py`)
3. The wrapper imports your code and calls your main rendering logic
4. Test by running `streamlit run main.py` from `Team3/streamlit_app/`

See `pages/2_Salary_Explorer_(Meng_Hai).py` for a wrapper example.
