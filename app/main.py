import asyncio
from app.extraction import extract_invoices_data
from app.processing import (
    parse_and_normalize_invoices, generate_financial_summary, create_excel_report
)

INVOICES_DIR = 'data/invoices'
REPORT_FILEPATH = 'data/invoices-report.xlsx'

async def process_invoices():
    invoices_filenames, invoices_json = await extract_invoices_data(INVOICES_DIR)
    invoices_df = parse_and_normalize_invoices(invoices_filenames, invoices_json)
    total_s, monthly_df = generate_financial_summary(invoices_df)
    create_excel_report(invoices_df, total_s, monthly_df, REPORT_FILEPATH)

def main():
    asyncio.run(process_invoices())


if __name__ == '__main__':
    main()