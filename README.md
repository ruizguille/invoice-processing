# Automating Invoice Processing with GPT-4o

This repository contains the code for an automated invoice processing system using Python, OpenAI's GPT-4o and Pandas. The system can process multiple PDF invoices, extract relevant information, perform basic financial analysis, and generate an Excel report.

For a detailed explanation of the code and concepts, check out [this blog post](https://codeawake.com/blog/invoice-processing).

## Structure

The code is organized into the following files:

- `main.py`: The main script for the invoice processing pipeline.
- `extraction.py`: Extracts the data from PDF invoices using GPT-4o.
- `processing.py`: Validates the invoice data, performs the financial analysis and creates the Excel report.
- `config.py`: Configuration settings for the application.
- `prompt.py`: Defines the system prompt used for GPT-4o.

## Installation

### Prerequisites ✅

- Python 3.11 or higher
- Poetry (Python package manager)

### Instructions

1. Install the dependencies using Poetry:

    ```bash
    poetry install
    ```

2. Create a `.env` file by copying the provided `.env.example` file and set the required environment variable:
    - `OPENAI_API_KEY`: Your OpenAI API key.

## Running the Application

Before running the application:

1. Update the `COMPANY_NAME` in `app/config.py` to match your company's name. This is used for invoice type classification (incoming or outgoing).

2. Ensure your PDF invoices are placed in the directory specified by `INVOICES_DIR` in `app/config.py` (default is `data/invoices`).

To run the invoice processing application:

```bash
poetry run process-invoices
```
