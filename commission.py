# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta

class Commission:
    __name__ = 'commission'
    __metaclass__ = PoolMeta

    @classmethod
    def _get_invoice_line(cls, key, invoice, commissions):
        invoice_line = super(Commission, cls)._get_invoice_line(key, invoice, commissions)
        invoice_line.discount1 = 0
        invoice_line.discount2 = 0
        invoice_line.discount3 = 0
        return invoice_line
