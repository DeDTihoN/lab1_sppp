# Azure AI Content Understanding Streamlit Demo

This project is a simple and elegant web application built with Streamlit that demonstrates the use of Azure AI Content Understanding service. The app allows a user to input a document URL and, after analysis, displays the extracted fields (education, language, and work_skills) along with their confidence scores.

---

## Overview

The application uses the Azure AI Content Understanding service to analyze a document (provided as a URL or file path) and extract predefined fields from it based on a custom analyzer. All critical settings, such as the endpoint, API version, subscription key (or AAD token), and analyzer ID, are loaded from environment variables (or a `.env` file using the `python-dotenv` library).

The key features include:
- **User Input:** A simple text box where the user can enter the URL of the document.
- **Real-time Analysis:** Initiates an analysis request to the Azure service and polls for the result until completion.
- **Field Extraction:** Extracts specific fields (education, language, work_skills) with their corresponding confidence scores.
- **Clean Interface:** Built with Streamlit to provide a clear and user-friendly interface.

---

## Prerequisites

- **Python 3.10+**
- **pip** package installer

---

## Dependencies

The project relies on the following Python libraries:
- [Streamlit](https://streamlit.io/) – for the web interface.
- [requests](https://docs.python-requests.org/) – for making HTTP requests.
- [python-dotenv](https://pypi.org/project/python-dotenv/) – for loading environment variables from a `.env` file.
- Standard libraries such as `os`, `logging`, `time`, `dataclasses`, and others.

You can install all dependencies using:
```bash
pip install streamlit requests python-dotenv
```

---

## Setup Instructions

1. **Clone the Repository**

2. **Create a .env File**

   In the root directory of the project, create a file named `.env` with the following variables (replace placeholder values with your actual credentials):
   ```env
   AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   AZURE_CONTENT_UNDERSTANDING_API_VERSION=2024-12-01-preview
   AZURE_CONTENT_UNDERSTANDING_SUBSCRIPTION_KEY=your_subscription_key
   AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID=CV_analizer
   # Optionally, if using AAD token instead of subscription key:
   # AZURE_CONTENT_UNDERSTANDING_AAD_TOKEN=your_aad_token
   ```

3. **Run the Application**

   Launch the Streamlit app by running:
   ```bash
   streamlit run streamlit_app.py
   ```
   This command will open your default web browser with the application's interface.

---

## Usage

1. **Enter Document URL:**
   On the main page, enter the URL of the document you want to analyze (e.g., a link to a PDF file).

2. **Start Analysis:**
   Click the "Analyze" button to initiate the analysis. The app will show a spinner while waiting for the analysis to complete.

3. **View Results:**
   Once the analysis is finished, the app displays the extracted fields for:
   - **Education** (with its confidence score)
   - **Language** (with its confidence score)
   - **Work Skills** (with its confidence score)

   If any of these fields are not found, an appropriate error message will be displayed.

---

## Customization

- **Schema & Analyzer Settings:**
  The analyzer (configured in Azure AI Foundry) should have a schema defined to extract the desired fields (`education`, `language`, `work_skills`, etc.). Adjust the schema in your analyzer if the expected fields do not appear in the results.

- **Environment Variables:**
  You may customize the app's behavior by changing the environment variables in the `.env` file.

- **Polling Parameters:**
  The timeout and polling interval for the analysis result can be tweaked in the code (see parameters `timeout_seconds` and `polling_interval_seconds` in the `poll_result` method).

---

## Troubleshooting

- **Environment Variables Not Loaded:**
  Ensure that the `.env` file is located in the root directory and that `load_dotenv()` is being called at the beginning of the script.

- **Invalid Credentials:**
  Verify that your Azure credentials and endpoint are correct and that the resource has the Content Understanding service enabled.

- **Missing Fields:**
  If certain fields such as `language` do not return a value, review your analyzer schema and confirm that the document contains sufficient data for extraction.

---