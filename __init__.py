# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import invoice
from . import commission


def register():
    Pool.register(
        invoice.InvoiceLine,
        module='account_invoice_3_discounts', type_='model')
    Pool.register(
        commission.Commission,
        depends=['commission'],
        module='account_invoice_3_discounts', type_='model')
