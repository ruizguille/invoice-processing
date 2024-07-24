from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    COMPANY_NAME: str = 'TechNova Solutions, Inc.'
    INVOICES_DIR: str = 'data/invoices'
    REPORT_FILEPATH: str = 'data/invoices-report.xlsx'

    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()