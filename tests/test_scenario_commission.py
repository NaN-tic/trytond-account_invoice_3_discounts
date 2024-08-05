import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
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

        # Install commission
        activate_modules(['commission', 'account_invoice_3_discounts'])

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

        # Create customer
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = accounts['expense']
        account_category.account_revenue = accounts['revenue']
        account_category.save()

        # Create commission product
        Uom = Model.get('product.uom')
        Template = Model.get('product.template')
        unit, = Uom.find([('name', '=', 'Unit')])
        template = Template()
        template.name = 'Commission'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal(0)
        template.account_category = account_category
        template.save()
        commission_product, = template.products

        # Create commission plan
        Plan = Model.get('commission.plan')
        plan = Plan(name='Plan')
        plan.commission_product = commission_product
        plan.commission_method = 'payment'
        line = plan.lines.new()
        line.formula = 'amount * 0.1'
        plan.save()

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create agent
        Agent = Model.get('commission.agent')
        agent_party = Party(name='Agent')
        agent_party.supplier_payment_term = payment_term
        agent_party.save()
        agent = Agent(party=agent_party)
        agent.type_ = 'agent'
        agent.plan = plan
        agent.currency = company.currency
        agent.save()

        # Create principal
        principal_party = Party(name='Principal')
        principal_party.customer_payment_term = payment_term
        principal_party.save()
        principal = Agent(party=principal_party)
        principal.type_ = 'principal'
        principal.plan = plan
        principal.currency = company.currency
        principal.save()

        # Create product sold
        template = Template()
        template.name = 'Product'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal(100)
        template.account_category = account_category
        template.principals.append(principal)
        template.save()
        product, = template.products

        # Create invoice
        Invoice = Model.get('account.invoice')
        invoice = Invoice()
        invoice.party = customer
        invoice.payment_term = payment_term
        invoice.agent = agent
        line = invoice.lines.new()
        line.product = product
        line.quantity = 1
        line.unit_price = Decimal(100)
        invoice.save()

        # Post invoice
        invoice.click('post')
        line, = invoice.lines
        self.assertEqual(len(line.commissions), 2)
        self.assertEqual(
            [c.amount for c in line.commissions],
            [Decimal('10.0000'), Decimal('10.0000')])
        self.assertEqual([c.invoice_state for c in line.commissions], ['', ''])

        # Create commission invoices
        create_invoice = Wizard('commission.create_invoice')
        create_invoice.form.from_ = None
        create_invoice.form.to = None
        create_invoice.execute('create_')
        invoice, = Invoice.find([
            ('type', '=', 'in'),
        ])
        line, = invoice.lines
        self.assertEqual(line.discount1, Decimal('0'))
        self.assertEqual(line.discount2, Decimal('0'))
        self.assertEqual(line.discount3, Decimal('0'))
