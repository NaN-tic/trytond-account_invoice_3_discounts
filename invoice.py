# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond.config import config
DISCOUNT_DIGITS = (16, config.getint('product', 'price_decimal', default=4))

__all__ = ['InvoiceLine']

STATES = {
    'invisible': Eval('type') != 'line',
    'required': Eval('type') == 'line',
    }
DEPENDS = ['type']
_ZERO = Decimal(0)


class InvoiceLine:
    __name__ = 'account.invoice.line'
    __metaclass__ = PoolMeta
    discount1 = fields.Numeric('Discount 1', digits=DISCOUNT_DIGITS,
        states=STATES, depends=DEPENDS)
    discount2 = fields.Numeric('Discount 2', digits=DISCOUNT_DIGITS,
        states=STATES, depends=DEPENDS)
    discount3 = fields.Numeric('Discount 3', digits=DISCOUNT_DIGITS,
        states=STATES, depends=DEPENDS)

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        discounts = set(['discount1', 'discount2', 'discount3'])
        cls.amount.on_change_with |= discounts
        cls.product.on_change |= discounts
        cls.gross_unit_price.on_change |= discounts
        cls.discount.on_change |= discounts

    @staticmethod
    def default_discount1():
        return 0

    @staticmethod
    def default_discount2():
        return 0

    @staticmethod
    def default_discount3():
        return 0

    def update_prices(self):
        discount1 = self.discount1 or Decimal(0)
        discount2 = self.discount2 or Decimal(0)
        discount3 = self.discount3 or Decimal(0)
        self.discount = 1 - ((1 - discount1) * (1 - discount2) * (1 -
                discount3))
        digits = self.__class__.discount.digits[1]
        self.discount = self.discount.quantize(Decimal(str(10.0 ** -digits)))
        super(InvoiceLine, self).update_prices()

    @fields.depends('discount1', 'discount2', 'discount3',
        methods=['discount'])
    def on_change_discount1(self):
        self.update_prices()

    @fields.depends('discount1', 'discount2', 'discount3',
        methods=['discount'])
    def on_change_discount2(self):
        self.update_prices()

    @fields.depends('discount1', 'discount2', 'discount3',
        methods=['discount'])
    def on_change_discount3(self):
        self.update_prices()

    def _credit(self):
        '''Add discount1, discount2 and discount 3 to credit line'''
        res = super(InvoiceLine, self)._credit()
        for field in ('discount1', 'discount2', 'discount3'):
            res[field] = getattr(self, field)
        return res
