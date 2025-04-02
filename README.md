# INF2009-Project-T13

## Project Documentation/Timeline can be found in Documentation Diary.docx.

**HawkerScan** is a combined Streamlit + Flask application that:
- Recognizes local Singaporean dishes in images via an AI model.
- Calculates nutritional data based on dish weight.
- Lets users view and edit their personal nutritional intake via Streamlit.
- Provides a /api/process-image endpoint for external devices (e.g., Raspberry Pi) to upload food images.

---

## Features

- **User Registration & Login**  
  - Uses Flask-Login for authentication against a SQLite database.
- **Dish Image Recognition**  
  - Automatically classifies an uploaded dish image using a custom AI model (`analyze_image()`).
- **Nutritional Intake Tracking**  
  - Stores recognized dishes and their macro data in a `nutritional_intake` table.
  - Displays daily, weekly, or monthly summaries in a Streamlit UI.
- **REST API**  
  - `/api/process-image` endpoint allows remote devices (e.g., Raspberry Pi) to send images + weight data.
  - Associates each request with a user via a unique API key.

---

## This is what your directory should look like

![image](https://github.com/user-attachments/assets/e35e247d-2a26-4014-8236-b8cac7e845b2)


## Ensure a virtual enviroment is created wherever the project folder is created:

python -m venv .venv
### On Windows:
.venv\Scripts\activate

or if using pycharm, you can use terminal in pycharm and check if a venv is already created. (It should be if you configured a python interpreter, if not run the code above)

##  Install Dependencies

pip install -r requirements.txt


## Running the application
An example would be like "(.venv) PS C:\Users\Kingston\PycharmProjects\HawkerScan> streamlit run app.py"

streamlit run app.py

## Troubleshooting

### A couple problems you might encounter:

Wrong version or missing libraries, the console should tell you which libraries you might be missing ("pip install -r requirements.txt", sometimes doesn't install some libraries properly, so I also had to manually pip install some libraries, sometimes you do have the libraries but it still says not found, in that case pip uninstall and pip install again, if the same error occurs again, try a different version of that library)

Ensure Transformers version is 4.41.1 (transformers==4.41.1), otherwise when uploading you might encounter some errors with dimensions or cache error.
