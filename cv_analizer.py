import json
import logging
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from dotenv import load_dotenv

import requests
import streamlit as st

# Settings class: load all values from environment variables
@dataclass(frozen=True, kw_only=True)
class Settings:
    endpoint: str
    api_version: str
    subscription_key: str | None = None
    aad_token: str | None = None
    analyzer_id: str
    file_location: str

    def __post_init__(self):
        if not self.endpoint:
            raise ValueError("AZURE_CONTENT_UNDERSTANDING_ENDPOINT is not set in environment variables.")
        if not self.analyzer_id:
            raise ValueError("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID is not set in environment variables.")
        key_not_provided = (
            not self.subscription_key or self.subscription_key == "AZURE_CONTENT_UNDERSTANDING_SUBSCRIPTION_KEY"
        )
        token_not_provided = (
            not self.aad_token or self.aad_token == "AZURE_CONTENT_UNDERSTANDING_AAD_TOKEN"
        )
        if key_not_provided and token_not_provided:
            raise ValueError("Either AZURE_CONTENT_UNDERSTANDING_SUBSCRIPTION_KEY or AZURE_CONTENT_UNDERSTANDING_AAD_TOKEN must be provided.")

    @property
    def token_provider(self) -> Callable[[], str] | None:
        if self.aad_token is None:
            return None
        return lambda: self.aad_token

# Azure Content Understanding Client
class AzureContentUnderstandingClient:
    def __init__(
        self,
        endpoint: str,
        api_version: str,
        subscription_key: str | None = None,
        token_provider: Callable[[], str] | None = None,
        x_ms_useragent: str = "cu-sample-code",
    ) -> None:
        if not subscription_key and token_provider is None:
            raise ValueError("Either subscription key or token provider must be provided.")
        if not api_version:
            raise ValueError("API version must be provided.")
        if not endpoint:
            raise ValueError("Endpoint must be provided.")

        self._endpoint: str = endpoint.rstrip("/")
        self._api_version: str = api_version
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)
        self._headers: dict[str, str] = self._get_headers(
            subscription_key, token_provider() if token_provider else None, x_ms_useragent
        )

    def begin_analyze(self, analyzer_id: str, file_location: str):
        """
        Starts analysis of a file or URL using the specified analyzer.
        """
        if Path(file_location).exists():
            with open(file_location, "rb") as file:
                data = file.read()
            headers = {"Content-Type": "application/octet-stream"}
        elif file_location.startswith("https://") or file_location.startswith("http://"):
            data = {"url": file_location}
            headers = {"Content-Type": "application/json"}
        else:
            raise ValueError("file_location must be a valid file path or URL.")

        headers.update(self._headers)
        analyze_url = self._get_analyze_url(self._endpoint, self._api_version, analyzer_id)
        if isinstance(data, dict):
            response = requests.post(url=analyze_url, headers=headers, json=data)
        else:
            response = requests.post(url=analyze_url, headers=headers, data=data)

        response.raise_for_status()
        self._logger.info(f"Started analysis for file {file_location} using analyzer: {analyzer_id}")
        return response

    def poll_result(
        self,
        response: requests.Response,
        timeout_seconds: int = 120,
        polling_interval_seconds: int = 2,
    ) -> dict[str, Any]:
        """
        Polls the asynchronous operation until it completes or the timeout is reached.
        """
        operation_location = response.headers.get("operation-location", "")
        if not operation_location:
            raise ValueError("Operation location not found in response headers.")

        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)
        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            self._logger.info("Waiting for result", extra={"elapsed": elapsed_time})
            if elapsed_time > timeout_seconds:
                raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds.")

            response = requests.get(operation_location, headers=self._headers)
            response.raise_for_status()
            result = cast(dict[str, Any], response.json())
            status = result.get("status", "").lower()
            if status == "succeeded":
                self._logger.info(f"Result ready after {elapsed_time:.2f} seconds.")
                return result
            elif status == "failed":
                self._logger.error(f"Request failed. Response: {result}")
                raise RuntimeError("Request failed.")
            else:
                self._logger.info(
                    f"Operation {operation_location.split('/')[-1].split('?')[0]} in progress..."
                )
            time.sleep(polling_interval_seconds)

    def _get_analyze_url(self, endpoint: str, api_version: str, analyzer_id: str):
        return f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={api_version}"

    def _get_headers(
        self, subscription_key: str | None, api_token: str | None, x_ms_useragent: str
    ) -> dict[str, str]:
        headers = (
            {"Ocp-Apim-Subscription-Key": subscription_key}
            if subscription_key
            else {"Authorization": f"Bearer {api_token}"}
        )
        headers["x-ms-useragent"] = x_ms_useragent
        return headers

# Main function for the Streamlit application
def main():
    load_dotenv()  # Load environment variables from .env file in the current directory
    st.title("Azure AI Content Understanding")
    st.markdown("Enter the document URL to analyze. The extracted fields **education**, **language**, and **work_skills** along with their confidence scores will be displayed.")

    # User input for document URL
    document_url = st.text_input("Document URL", value="https://example.com/sample.pdf")

    if st.button("Analyze") and document_url:
        try:
            # Load settings from environment variables
            settings = Settings(
                endpoint=os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT"),
                api_version=os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2024-12-01-preview"),
                subscription_key=os.getenv("AZURE_CONTENT_UNDERSTANDING_SUBSCRIPTION_KEY"),
                aad_token=os.getenv("AZURE_CONTENT_UNDERSTANDING_AAD_TOKEN"),
                analyzer_id=os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID"),
                file_location=document_url,
            )

            client = AzureContentUnderstandingClient(
                settings.endpoint,
                settings.api_version,
                subscription_key=settings.subscription_key,
                token_provider=settings.token_provider,
            )

            with st.spinner("Analyzing, please wait..."):
                response = client.begin_analyze(settings.analyzer_id, settings.file_location)
                result = client.poll_result(
                    response,
                    timeout_seconds=60 * 60,
                    polling_interval_seconds=2,
                )

            # Extract fields from the result; assuming result has a key "result" that contains "contents"
            result_obj = result.get("result", {})
            contents = result_obj.get("contents", [])
            if not contents:
                st.error("No contents found in the result.")
                return

            fields = contents[0].get("fields", {})

            # Extract value and confidence for education
            education_obj = fields.get("education", {})
            education_value = education_obj.get("valueString", "not found")
            education_confidence = education_obj.get("confidence", "N/A")

            # Extract value and confidence for language
            language_obj = fields.get("language", {})
            language_value = language_obj.get("valueString", "not found")
            language_confidence = language_obj.get("confidence", "N/A")

            # Extract value and confidence for work_skills
            work_skills_obj = fields.get("work_skills", {})
            work_skills_value = work_skills_obj.get("valueString", "not found")
            work_skills_confidence = work_skills_obj.get("confidence", "N/A")

            st.success("Analysis completed successfully!")
            st.markdown("**Extracted Data:**")
            st.write(f"**Education:** {education_value} (Confidence: {education_confidence})")
            st.write(f"**Language:** {language_value} (Confidence: {language_confidence})")
            st.write(f"**Work Skills:** {work_skills_value} (Confidence: {work_skills_confidence})")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            print(e, file=sys.stderr)

if __name__ == "__main__":
    main()
