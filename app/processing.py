import json
from enum import Enum
from datetime import date
from pydantic import BaseModel, ConfigDict, ValidationError
import pandas as pd

class InvoiceType(str, Enum):
    incoming = 'incoming'
    outgoing = 'outgoing'

class InvoiceItem(BaseModel):
    description: str
    total: float

class Company(BaseModel):
    name: str
    address: str
    phone: str | None = None
    email: str | None = None

class Invoice(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    invoice_number: str
    invoice_date: date
    invoice_type: InvoiceType | None = None
    issuer: Company
    recipient: Company
    invoice_items: list[InvoiceItem]
    subtotal: float
    tax_rate: float = 0
    tax: float = 0
    total: float
    terms: str | None = None

def flatten_invoice_structure(invoice):
    flat = {
        'Invoice Number': invoice.invoice_number,
        'Invoice Date': invoice.invoice_date,
        'Invoice Type': invoice.invoice_type,
        'Issuer Name': invoice.issuer.name,
        'Issuer Address': invoice.issuer.address,
        'Issuer Phone': invoice.issuer.phone,
        'Issuer Email': invoice.issuer.email,
        'Recipient Name': invoice.recipient.name,
        'Recipient Address': invoice.recipient.address,
        'Recipient Phone': invoice.recipient.phone,
        'Recipient Email': invoice.recipient.email,
        'Subtotal': invoice.subtotal,
        'Tax Rate': invoice.tax_rate,
        'Tax': invoice.tax,
        'Total': invoice.total,
        'Terms': invoice.terms
    }
    
    for i, item in enumerate(invoice.invoice_items, 1):
        flat[f'Item {i} Description'] = item.description
        flat[f'Item {i} Total'] = item.total
    
    return flat

def build_invoices_dataframe(invoices_filenames, invoices_json):
    flat_invoices = []
    for filename, invoice_json in zip(invoices_filenames, invoices_json):
        try:
            invoice_data = json.loads(invoice_json)
            validated_invoice = Invoice(**invoice_data)
            flat_invoice = flatten_invoice_structure(validated_invoice)
            flat_invoices.append(flat_invoice)
        except json.JSONDecodeError as e:
            print(f'JSON parsing error in invoice {filename}: {e}')
        except ValidationError as e:
            print(f'Validation error in invoice {filename}: {e}')
        except Exception as e:
            print(f'Unexpected error in invoice {filename}: {e}')
    
    invoices_df = pd.DataFrame(flat_invoices)
    invoices_df['Invoice Date'] = pd.to_datetime(invoices_df['Invoice Date'])
    invoices_df.insert(2, 'Year-Month', invoices_df['Invoice Date'].dt.to_period('M'))
    return invoices_df

def generate_financial_summary(invoices_df):
    total_s = pd.Series(dtype='object')

    # Total
    total_s['Period'] = f"{invoices_df['Invoice Date'].min().strftime('%Y-%m')} to {invoices_df['Invoice Date'].max().strftime('%Y-%m')}"
    total_s['Invoices'] = len(invoices_df)

    revenue = invoices_df[invoices_df['Invoice Type'] == 'outgoing']['Total'].sum()
    expenses = invoices_df[invoices_df['Invoice Type'] == 'incoming']['Total'].sum()
    total_s['Revenue'] = revenue
    total_s['Expenses'] = expenses
    total_s['Net Income'] = revenue - expenses

    total_tax_collected = invoices_df[invoices_df['Invoice Type'] == 'outgoing']['Tax'].sum()
    total_tax_paid = invoices_df[invoices_df['Invoice Type'] == 'incoming']['Tax'].sum()
    total_s['Tax Collected'] = total_tax_collected
    total_s['Tax Paid'] = total_tax_paid
    total_s['Net Tax'] = total_tax_collected - total_tax_paid

    # Monthly
    monthly_df = invoices_df.groupby('Year-Month').agg(**{
        'Invoices': ('Invoice Number', 'count'),
        'Revenue': ('Total', lambda x: x[invoices_df['Invoice Type'] == 'outgoing'].sum()),
        'Expenses': ('Total', lambda x: x[invoices_df['Invoice Type'] == 'incoming'].sum()),
        'Tax Collected': ('Tax', lambda x: x[invoices_df['Invoice Type'] == 'outgoing'].sum()),
        'Tax Paid': ('Tax', lambda x: x[invoices_df['Invoice Type'] == 'incoming'].sum())
    })
    monthly_df = monthly_df.reset_index()
    monthly_df['Year-Month'] = monthly_df['Year-Month'].astype(str)
    monthly_df.insert(4, 'Net Income', monthly_df['Revenue'] - monthly_df['Expenses'])
    monthly_df['Net Tax'] = monthly_df['Tax Collected'] - monthly_df['Tax Paid']

    return total_s, monthly_df.T

def create_excel_report(invoices_df, total_s, monthly_df, filepath):
    with pd.ExcelWriter(filepath, engine='xlsxwriter', datetime_format='YYYY-MM-DD') as writer:
        # Write invoice data sheet
        invoices_df.to_excel(writer, sheet_name='Invoices', index=False)

        # Create summary sheet
        workbook = writer.book
        worksheet = workbook.add_worksheet('Summary')

        # Define formats
        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        money_format = workbook.add_format({'num_format': '#,##0.00'})

        # Write total summary
        worksheet.write('A1', 'TOTAL', title_format)
        total_s.to_frame().to_excel(writer, sheet_name='Summary', startrow=1, startcol=0, header=False)

        # Write monthly summary
        worksheet.write('A12', 'MONTHLY', title_format)
        monthly_df.to_excel(writer, sheet_name='Summary', startrow=12, startcol=0, header=False)

        # Money formatting
        money_rows = list(range(3, 9)) + list(range(14, 20))
        for row in money_rows:
            worksheet.set_row(row, None, money_format)

        # Create chart
        chart = workbook.add_chart({'type': 'line'})

        num_cols = monthly_df.shape[1]
        for i, metric in enumerate(['Revenue', 'Expenses', 'Net Income']):
            chart.add_series({
                'name': metric,
                'categories': ['Summary', 12, 1, 12, num_cols],
                'values': ['Summary', 14 + i, 1, 14 + i, num_cols],
            })

        chart.set_x_axis({'name': 'Month'})
        chart.set_y_axis({'name': 'Amount', 'major_gridlines': {'visible': False}})

        worksheet.insert_chart('A23', chart)
