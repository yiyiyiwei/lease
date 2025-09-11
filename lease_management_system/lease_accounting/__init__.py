"""
租赁合同核算模块
"""

from .core import LeaseAccounting
from .database import init_extended_db
from .income_tab import add_income_tab, query_monthly_income, export_income_table
from .vat_tab import add_vat_tab, query_vat_records, export_vat_table
from .stamp_duty import check_quarterly_stamp_duty

__version__ = "1.0.0"
__all__ = [
    'LeaseAccounting',
    'init_extended_db',
    'add_income_tab',
    'query_monthly_income', 
    'export_income_table',
    'add_vat_tab',
    'query_vat_records',
    'export_vat_table',
    'check_quarterly_stamp_duty'
]
