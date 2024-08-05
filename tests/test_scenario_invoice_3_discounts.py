import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear, create_tax,
                                                 create_tax_code, get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install account_invoice_3_discounts
        config = activate_modules('account_invoice_3_discounts')

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create tax
        tax = create_tax(Decimal('.10'))
        tax.save()
        invoice_base_code = create_tax_code(tax, 'base', 'invoice')
        invoice_base_code.save()
        invoice_tax_code = create_tax_code(tax, 'tax', 'invoice')
        invoice_tax_code.save()
        credit_note_base_code = create_tax_code(tax, 'base', 'credit')
        credit_note_base_code.save()
        credit_note_tax_code = create_tax_code(tax, 'tax', 'credit')
        credit_note_tax_code.save()

        # Create party
        Party = Model.get('party.party')
        party = Party(name='Party')
        party.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.customer_taxes.append(tax)
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal('40')
        template.account_category = account_category
        template.save()
        product.template = template
        product.save()

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create invoice
        Invoice = Model.get('account.invoice')
        invoice = Invoice()
        invoice.party = party
        invoice.payment_term = payment_term
        line1 = invoice.lines.new()
        line1.product = product
        line1.quantity = 5
        line1.unit_price = Decimal('40')
        line2 = invoice.lines.new()
        line2.account = revenue
        line2.description = 'Test'
        line2.quantity = 1
        line2.gross_unit_price = Decimal(20)
        line2.discount1 = Decimal('.5')
        line2.discount2 = Decimal('.1')
        line2.discount3 = Decimal('.05')
        self.assertEqual(line2.unit_price, Decimal('8.55000000'))
        self.assertEqual(invoice.untaxed_amount, Decimal('208.55'))
        self.assertEqual(invoice.tax_amount, Decimal('20.00'))
        self.assertEqual(invoice.total_amount, Decimal('228.55'))
        invoice.save()
        Invoice.post([invoice.id], config.context)
        invoice.reload()
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(invoice.untaxed_amount, Decimal('208.55'))
        self.assertEqual(invoice.tax_amount, Decimal('20.00'))
        self.assertEqual(invoice.total_amount, Decimal('228.55'))
        self.assertEqual(line2.discount, Decimal('0.5725'))

        # Credit invoice with refund
        credit = Wizard('account.invoice.credit', [invoice])
        credit.form.with_refund = True
        credit.execute('credit')
        invoice.reload()
        self.assertEqual(invoice.untaxed_amount, Decimal('208.55'))
        self.assertEqual(invoice.tax_amount, Decimal('20.00'))
        self.assertEqual(invoice.total_amount, Decimal('228.55'))
        invoice_credit, = Invoice.find([('type', '=', 'out'),
                                        ('untaxed_amount', '<', 0)])
        line1, line2 = invoice_credit.lines
        self.assertEqual(line2.discount, Decimal('0.5725'))
        self.assertEqual(line2.discount1, Decimal('0.5'))
        self.assertEqual(line2.discount2, Decimal('0.1'))
        self.assertEqual(line2.discount3, Decimal('0.05'))
