# Contributing to Verbum

Thank you for taking the time to improve Verbum! A few quick reminders will help you get productive fast:

## Local Environment

- Python 3.10 or newer is required.
- Install editable dependencies for both the CLI and API:

  ```bash
  pip install -e .
  ```

## Running Tests

- Execute the automated suite (including CLI smoke tests) with:

  ```bash
  pytest -v
  ```

  Please add coverage for any new behaviour you introduce.

## Launching the API

- Start the FastAPI application locally with:

  ```bash
  uvicorn api.main:app --reload
  ```

- Visit `http://127.0.0.1:8000/docs` for interactive exploration of the `/lookup` endpoint.

## Submitting Changes

- Format and lint your code before opening a pull request.
- Describe the motivation for the change and include testing notes or screenshots where relevant.
- Be mindful of the shared service layer between CLI and API—changes to repositories or services may affect both entry points.

We appreciate your contributions!
