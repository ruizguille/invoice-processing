import os
import base64
from io import BytesIO
from pdf2image import convert_from_path
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio
from app.config import settings
from app.prompt import SYSTEM_PROMPT

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

def pdf_to_base64_images(pdf_path):
    imgs = convert_from_path(pdf_path, fmt='png')
    base64_imgs = []
    for image in imgs:
        buffered = BytesIO()
        image.save(buffered, format='PNG')
        img_str = base64.b64encode(buffered.getvalue()).decode()
        base64_imgs.append(img_str)
    
    return base64_imgs

async def extract_invoice_data(base64_img):
    response = await openai_client.chat.completions.create(
        model='gpt-4o',
        response_format={ 'type': 'json_object' },
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT.format(company=settings.COMPANY_NAME)},
            {'role': 'user', 'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{base64_img}'}}
            ]}
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content

async def extract_invoices_data(invoices_dir):
    invoices_filenames = []
    tasks = []
    print('Extracting the invoices data')
    for filename in sorted(os.listdir(invoices_dir)):
        if filename.endswith('.pdf'):
            print(filename)
            invoices_filenames.append(filename)
            pdf_path = os.path.join(invoices_dir, filename)
            base64_images = pdf_to_base64_images(pdf_path)
            task = extract_invoice_data(base64_images[0])
            tasks.append(task)
    invoices_json = await tqdm_asyncio.gather(*tasks)
    return invoices_filenames, invoices_json