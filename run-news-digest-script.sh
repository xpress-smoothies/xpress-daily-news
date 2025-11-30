#!/bin/bash
# ----------------------------------------
# run_digest.sh — activate venv, load .env, run digest
# ----------------------------------------

# Go to project directory
cd /Users/jim/Git-Projects/xpress-daily-news || exit 1

# Activate virtual environment
source .venv/bin/activate

# Run the Python script (it will load .env itself via load_dotenv())
python news-digest-script.py