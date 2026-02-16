# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError




class KGBonds(models.Model):
    _name = 'kg.bonds'
    _description = 'Bonds'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Doc Id', copy=False,
                       readonly=True, index=True, default=lambda self: _('/'))
    bond_name = fields.Char(string='Bond Name')
    investment_id = fields.Many2one('kg.investment.entry',)
    ISIN_code = fields.Char(string='ISIN')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date = fields.Date(string='Date', default=fields.Date.today)
    face_value = fields.Monetary(string='Purchase Value', required=True, compute='compute_face_value')
    total_cost = fields.Monetary(string='Total cost', required=True, compute='compute_total_cost')
    coupon_rate = fields.Float(string='Coupon Rate(CR)', required=True,digits=(10,6))
    coupon_periodicity = fields.Selection(
        selection=[
            ('semi', 'Semi Annually'),
            ('quarter', 'Quarterly'),
            ('annual', 'Annually'),
        ],
        string='Coupon Periodicity',
        required=True,
        default='semi',
    )
    coupon_payment = fields.Monetary(string='Coupon Payment(CP)', required=True, compute='compute_coupon_payment',
                                     readonly=True)
    coupon_begin_date = fields.Date(string='Coupon Begin Date', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    maturity_date = fields.Date(string='Maturity Date', required=True)
    yield_val = fields.Float(string='Effective Interest', required=True,digits=(10,9))
    # yield_value = fields.Float(string='Yield', required=True,digits=(10,10),compute='calculate_yield')
    payment_frequency = fields.Integer(string='Payment Frequency', required=True,compute='compute_payment_frequency')
    maturity_value = fields.Monetary(string='Maturity Value', required=True)
    bond_line_ids = fields.One2many('kg.bonds.amortization.line', 'bond_id')
    account_id = fields.Many2one('account.account', string='Amortization Account',required=True )
    journal_entry_ids = fields.One2many('account.move', 'bond_id', string='Journal Entries')
    purchase_price = fields.Float(string='Purchase Price',digits=(10,5))
    settlement_date = fields.Date(string='Settlement Date')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('to_approve', 'To Approve'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    manager_approved = fields.Boolean(string='Manager Approval', default=False,copy=False)
    brokerage= fields.Float(string='Brokerage')
    no_of_shares = fields.Float(string='No of Units')
    broker_bank = fields.Selection([('broker', 'Broker'),
                                    ('bank', 'Bank')],
                                   string="Broker/Bank",default="bank")
    broker_id = fields.Many2one('res.partner', string='Broker')
    bank_id = fields.Many2one('account.account', string='Bank')


    @api.onchange('investment_id')
    def _compute_investment_isin(self):
        for rec in self:
            rec.ISIN_code = rec.investment_id.isin_code

    # def year_fraction(self, start_date, end_date, basis):
    #     delta_days = (end_date - start_date).days
    #     # if end_date != self.maturity_date:
    #     #     d_days = (self.maturity_date-end_date).days
    #     #     delta_days = delta_days+d_days-3
    #     #     print("d_days",d_days)
    #
    #     # delta_days = relativedelta(end_date , start_date)
    #     print("end_date",end_date)
    #     print("start_date",start_date)
    #     # delta_days_inclusive = delta_days+1
    #     days_in_year = 365.25
    #     # print("delta_days",delta_days_inclusive)
    #     print("delta_days",delta_days)
    #
    #     if basis == 0:  # actual/actual
    #         return delta_days / days_in_year
    #     elif basis == 1:  # 30/360
    #         start_total_days = (start_date.year - 1900) * 360 + (start_date.month - 1) * 30 + start_date.day
    #         end_total_days = (end_date.year - 1900) * 360 + (end_date.month - 1) * 30 + end_date.day
    #         return (end_total_days - start_total_days) / 360
    #     elif basis == 2:  # actual/360
    #         dayyy= delta_days / 365.25
    #         print("dayyy",dayyy)
    #         return delta_days/ 365
    #     elif basis == 3:  # actual/365
    #         return delta_days / 365
    #     else:
    #         raise ValueError("Unsupported basis")
    #
    # def cash_flows(self, settlement, maturity, rate, redemption, frequency):
    #     days_per_year = 365
    #     days_per_period = days_per_year / frequency
    #     print("days_per_period",days_per_period)
    #     periods = int((maturity - settlement).days / days_per_period)
    #     # num_periods = (maturity.year - settlement.year) * 2 + (
    #     #         maturity.month - settlement.month) // 6 + 1
    #     # print("num_periods",num_periods)
    #
    #     coupon_payment = (rate / frequency) * redemption
    #     # dates = [settlement + timedelta(days=int(days_per_period) * i) for i in range(1, periods + 1)]
    #     dates = [settlement + relativedelta(months=6 * i) for i in range(1, periods + 1)]
    #     flows = [coupon_payment] * (periods - 1) + [coupon_payment + redemption]
    #
    #     return dates, flows
    #
    # def price_function(self, rate, settlement, maturity, coupon_rate, pr, redemption, frequency, basis):
    #     dates, flows = self.cash_flows(settlement, maturity, coupon_rate, redemption, frequency)
    #     discount_factors = [1 / (1 + rate / frequency) ** (frequency * self.year_fraction(settlement, date, basis)) for
    #                         date in dates]
    #
    #     bond_price = sum(flow * discount for flow, discount in zip(flows, discount_factors))
    #     return bond_price - pr
    #
    # def calculate_yield(self):
    #     if self.coupon_begin_date and self.purchase_price and self.maturity_date and self.coupon_rate and self.payment_frequency:
    #         # Use Newton-Raphson method to find yield
    #
    #         coupon_payment = self.maturity_value * self.coupon_rate/2
    #         # self.yield_value = npf.rate(16,coupon_payment,self.purchase_price,self.maturity_value)*2
    #         # self.yield_value = newton(self.price_function, 0.05, args=(
    #         #     self.coupon_begin_date, self.maturity_date, self.coupon_rate, self.purchase_price, 100,
    #         #     self.payment_frequency, 2))
    #         # print(f"Yield to Maturity: {self.yield_value * 100:.7f}%")
    #         self.yield_value = self.calculate_yield_value(self.coupon_begin_date, self.maturity_date, self.coupon_rate, self.purchase_price, 100,
    #             self.payment_frequency, 2)
    #         # self.yield_value = np.yield(self.coupon_begin_date, self.maturity_date, self.coupon_rate, self.purchase_price, 100,
    #         #     self.payment_frequency, 2)
    #         # np.irr
    #     else:
    #         self.yield_value = False
    #         print("Yield to Maturity: False")
    #
    # def calculate_days(self, date1, date2, basis=0):
    #     if basis == 0:
    #         d1 = min(date1.day, 30)
    #         d2 = min(date2.day, 30)
    #         return (date2.year - date1.year) * 360 + (date2.month - date1.month) * 30 + (d2 - d1)
    #     elif basis == 1:
    #         return (date2 - date1).days
    #     elif basis == 2:
    #         return (date2 - date1).days
    #     elif basis == 3:
    #         return (date2 - date1).days
    #     elif basis == 4:
    #         d1 = min(date1.day, 30)
    #         d2 = min(date2.day, 30)
    #         return (date2.year - date1.year) * 360 + (date2.month - date1.month) * 30 + (d2 - d1)
    #     else:
    #         raise ValueError("Invalid basis provided")
    #
    # def calculate_yield_value(self, settlement_date, maturity_date, annual_coupon_rate, price, redemption_value, frequency,
    #                     basis=0):
    #     """
    #     Calculate the yield of a bond based on parameters similar to Excel's YIELD function.
    #
    #     :param settlement_date: The settlement date of the bond (datetime object).
    #     :param maturity_date: The maturity date of the bond (datetime object).
    #     :param annual_coupon_rate: The annual coupon rate of the bond (as a decimal, e.g., 0.05 for 5%).
    #     :param price: The current price of the bond (per 100 units of face value).
    #     :param redemption_value: The redemption value of the bond (per 100 units of face value).
    #     :param frequency: Number of coupon payments per year (1 for annual, 2 for semi-annual, 4 for quarterly).
    #     :param basis: The day count basis to use (optional, default is 0).
    #     :return: The yield of the bond.
    #     """
    #     # Calculate the number of periods (coupon payments) remaining until maturity
    #     # settlement_date = datetime.strptime(settlement_date, '%Y-%m-%d')
    #     # maturity_date = datetime.strptime(maturity_date, '%Y-%m-%d')
    #
    #     DSR = self.calculate_days(settlement_date, maturity_date, basis)
    #
    #     num_periods = frequency * (DSR / 365)
    #     # num_periods = frequency * ((maturity_date.year - settlement_date.year) +
    #     #                            (maturity_date.month - settlement_date.month) / 12)
    #
    #     # Coupon payment per period
    #     coupon_payment = (annual_coupon_rate / frequency) * 100  # Assuming face value is 100
    #
    #     # Cash flow array: -price now, followed by coupon payments, and then redemption value at maturity
    #     cash_flows = [-price] + [coupon_payment] * int(num_periods - 2) + [coupon_payment + redemption_value]
    #     print('coupon_payment', coupon_payment)
    #     print('num_periods', num_periods)
    #     print('DSR', DSR)
    #     print('cash_flows', cash_flows)
    #
    #     # Calculate the yield (IRR) using numpy's irr function
    #     irr = np.irr(cash_flows)
    #
    #     # Convert IRR to annual yield depending on frequency
    #     annual_yield = (1 + irr) ** frequency - 1
    #
    #     return annual_yield

    # def calculate_yield_value(self, settlement, maturity, rate, pr, redemption, frequency, basis=0):
    #     settlement_date = settlement
    #     maturity_date = maturity
    #
    #     A = self.calculate_days(settlement_date - relativedelta(months=int(12 / frequency)), settlement_date, basis)
    #     E = self.calculate_days(settlement_date, settlement_date + relativedelta(months=int(12 / frequency)), basis)
    #     DSR = self.calculate_days(settlement_date, maturity_date, basis)
    #
    #     numerator_part1 = (redemption / 100) + (rate / frequency)
    #     numerator_part2 = (pr / 100) + (rate / frequency)
    #     numerator = (numerator_part1 - numerator_part2)
    #
    #     denominator = (pr / 100) + (rate / frequency)
    #
    #     yield_value = numerator / (denominator)
    #
    #     return yield_value

    #     payment_frequency = 2
    #     redemption = 100
    #     if self.purchase_price and self.settlement_date and self.maturity_date and self.coupon_rate:
    #         # Calculate time in years to maturity
    #         days_to_maturity = (self.maturity_date - self.settlement_date).days
    #         years_to_maturity = days_to_maturity / 365.0
    #
    #         # Generate cash flows
    #         cash_flows = []
    #
    #         # Calculate coupon payment
    #         coupon_payment = self.coupon_rate * redemption / payment_frequency
    #
    #         # Number of coupon payments
    #         num_coupons = int(payment_frequency * years_to_maturity)
    #
    #         # Add coupon payments
    #         for _ in range(num_coupons):
    #             cash_flows.append(coupon_payment)
    #
    #         # Add redemption value at maturity
    #         cash_flows.append(coupon_payment + redemption)
    #
    #         # Add initial negative cash flow (purchase price)
    #         cash_flows.insert(0, -self.purchase_price)
    #
    #         # Calculate yield to maturity (IRR of cash flows)
    #         self.yield_value = npf.irr(cash_flows)
    #     else:
    #         self.yield_value = 0.0
    @api.depends('coupon_periodicity')
    def compute_payment_frequency(self):
        for record in self:
            if record.coupon_periodicity == 'quarter':
                record.payment_frequency = 4
            elif record.coupon_periodicity == 'semi':
                record.payment_frequency = 2
            elif record.coupon_periodicity == 'annual':
                record.payment_frequency = 1
            else:
                record.payment_frequency = 0

    @api.depends('maturity_value', 'coupon_rate')
    def compute_coupon_payment(self):
        for rec in self:
            rec.coupon_payment = ((rec.maturity_value * rec.coupon_rate)/rec.payment_frequency)

    @api.depends('purchase_price', 'no_of_shares')
    def compute_face_value(self):
        for rec in self:
            rec.face_value = rec.purchase_price * rec.no_of_shares

    @api.depends('face_value', 'brokerage')
    def compute_total_cost(self):
        for rec in self:
            rec.total_cost= rec.face_value + rec.brokerage

    # @api.depends('purchase_price', 'settlement_date','payment_frequency','maturity_date','coupon_rate')
    # def compute_yield(self):
    #     redemption = 100.0
    #     basis = 2
    #     payment_frequency =2
    #     # self.yield_val = 0.0
    #
    #     if self.purchase_price and self.coupon_rate and self.settlement_date and self.maturity_date:
    #
    #         tolerance = 0.0001  # Tolerance for convergence
    #
    #         for bond in self:
    #             settlement = bond.settlement_date
    #             maturity = bond.maturity_date
    #             rate_guess = 0.05  # Initial guess for YTM
    #
    #             yield_value = self.calculate_ytm(settlement, maturity, rate_guess, bond, tolerance)
    #
    #             if yield_value is not None:
    #                 bond.yield_value = yield_value
    #                 print("Yield to Maturity (YTM):", bond.yield_val)
    #             else:
    #                 bond.yield_value = 0.0  # Default to 0.0 if calculation fails
    #
    # def calculate_ytm(self, settlement, maturity, rate_guess, bond, tolerance):
    #     try:
    #         max_iterations = 1000
    #         iteration = 0
    #         while iteration < max_iterations:
    #             iteration += 1
    #
    #             # Calculate present value of cash flows with current rate_guess
    #             pv = 0.0
    #             coupon_payment = bond.coupon_rate / 100.0 * bond.face_value / bond.payment_frequency
    #             discount_factor = 1 + rate_guess / bond.payment_frequency
    #
    #             # Check if discount_factor is positive before taking logarithm
    #             if discount_factor <= 0:
    #                 return None  # Avoid math domain error
    #
    #             log_discount_factor = math.log(discount_factor)
    #             for t in range(1, bond.payment_frequency * (maturity.year - settlement.year) + 1):
    #                 pv += coupon_payment / math.exp(log_discount_factor * t)
    #             pv += bond.face_value / math.exp(
    #                 log_discount_factor * (bond.payment_frequency * (maturity.year - settlement.year)))
    #
    #             # Include purchase price in PV calculation
    #             total_investment = bond.purchase_price / 100 * bond.face_value  # Adjust if purchase_price is per 100 units
    #             pv -= total_investment / math.exp(
    #                 log_discount_factor * (bond.payment_frequency * (settlement.year - maturity.year)))
    #
    #             # Calculate derivative of present value with respect to rate_guess
    #             derivative = 0.0
    #             for t in range(1, bond.payment_frequency * (maturity.year - settlement.year) + 1):
    #                 if discount_factor == 0:
    #                     derivative -= float('inf')
    #                 else:
    #                     derivative -= t * coupon_payment / discount_factor ** (t + 1)
    #             derivative -= (bond.payment_frequency * (maturity.year - settlement.year)) * bond.face_value / (
    #                     discount_factor ** (bond.payment_frequency * (maturity.year - settlement.year) + 1))
    #
    #             # Update rate_guess using Newton-Raphson method
    #             rate_guess = rate_guess - pv / derivative
    #
    #             # Check for convergence
    #             if abs(pv) < tolerance:
    #                 return rate_guess * bond.payment_frequency * 100.0  # Convert to percentage
    #
    #         # If max_iterations reached without convergence
    #         return None
    #     except ZeroDivisionError:
    #         # Handle division by zero error
    #         return None
    #     except ValueError as e:
    #         print(f"ValueError occurred: {e}")
    #         return None

                # yield_func = getattr(npf, 'yield')
                # rec.yield_val = npf.irr(rec.settlement_date, rec.maturity_date, rec.coupon_rate, rec.purchase_price, redemption, payment_frequency, basis)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('kg.bonds.seq')
        return super(KGBonds, self).create(vals_list)

    def action_submit_manager(self):
        for record in self:
            record.manager_approved = True

            receiver = record.env.ref('kg_investment.group_manager')
            partners = []
            subtype_ids = record.env['mail.message.subtype'].search([('res_model', '=', 'kg.purchase.order')]).ids
            if receiver.users:
                for user in receiver.users:
                    record.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                    partners.append(user.partner_id.id)
                    body = _(u'Dear ' + user.name + '. Please check and approve the Bond created.')
                self.message_post(body=body, partner_ids=partners)

            record.write({'state': 'to_approve'})

    #
    # def action_approve_bond(self):
    #     for record in self:
    #         rate = record.currency_id.rate
    #         journal = record.env['account.journal'].sudo().search([('name', '=', 'Bonds')], limit=1)
    #         if not journal:
    #             raise ValidationError("Bonds journal not found")
    #
    #         # Handling for 'approve bank broker'
    #         if record.broker_bank:
    #             if not record.settlement_date:
    #                 raise ValidationError("Please set Settlement Date")
    #             if record.broker_bank == 'broker' and not record.broker_id:
    #                 raise ValidationError("Please set the Broker Name")
    #             if record.broker_bank == 'bank' and not record.bank_id:
    #                 raise ValidationError("Please set the Bank Account")
    #             if not broker_bank :
    #                 raise ValidationError("Please choose Bank or Broke")

    #
    #             if record.bank_id:
    #                 # Create journal entry for bank
    #                 journal_entry = self.env['account.move'].create({
    #                     'journal_id': journal.id,
    #                     'date': record.settlement_date,
    #                     'ref': record.name,
    #                     'line_ids': [
    #                         (0, 0, {
    #                             'name': record.investment_id.name,
    #                             'account_id': record.investment_id.account_id.id,
    #                             'currency_id': record.currency_id.id,
    #                             'amount_currency': record.total_cost,
    #                         }),
    #                         (0, 0, {
    #                             'name': record.bank_id.name,
    #                             'account_id': record.bank_id.id,
    #                             'currency_id': record.currency_id.id,
    #                             'amount_currency': -record.total_cost,
    #                         })
    #                     ]
    #                 })
    #             else:
    #                 # Create journal entry for broker
    #                 journal_entry = self.env['account.move'].create({
    #                     'journal_id': journal.id,
    #                     'date': record.settlement_date,
    #                     'ref': record.name,
    #                     'line_ids': [
    #                         (0, 0, {
    #                             'name': record.investment_id.name,
    #                             'account_id': record.investment_id.account_id.id,
    #                             'currency_id': record.currency_id.id,
    #                             'amount_currency': record.total_cost,
    #                         }),
    #                         (0, 0, {
    #                             'name': record.broker_id.name,
    #                             'account_id': record.broker_id.property_account_payable_id.id,
    #                             'currency_id': record.currency_id.id,
    #                             'amount_currency': -record.total_cost,
    #                         })
    #                     ]
    #                 })
    #             journal_entry.write({'bond_id': record.id})
    #             record.write({'state': 'posted'})
    #
    #         # Handling for 'approve bond'
    #         if record.bond_line_ids:
    #             for line in record.bond_line_ids:
    #                 account_id = self.env['ir.config_parameter'].sudo().get_param('kg_investment.bond_account_id')
    #                 if not account_id:
    #                     raise ValidationError("Please set Account in Settings")
    #                 if not record.investment_id.account_id:
    #                     raise ValidationError("Please set Account in Investment Entry")
    #
    #                 # Create journal entry for bond
    #                 journal_entry = self.env['account.move'].create({
    #                     'journal_id': journal.id,
    #                     'date': line.period,
    #                     'ref': record.name,
    #                     'line_ids': [
    #                         (0, 0, {
    #                             'name': record.investment_id.name,
    #                             'account_id': record.investment_id.account_id.id,
    #                             # 'debit': line.amortization * rate,
    #                             # 'credit': 0.0,
    #                             'currency_id': record.currency_id.id,
    #                             'amount_currency': line.amortization
    #
    #                             # 'currency_rate':record.exchange_rate,
    #
    #                         }),
    #                         # (0, 0, {
    #                         #     'name': record.investment_id.name,
    #                         #     'account_id': account_id,
    #                         #     'debit': line.interest_accuired,
    #                         #     'credit': 0.0,
    #                         #     'amount_currency': record.net_value,
    #                         #     'currency_id': record.currency_id.id,
    #                         #     # 'currency_rate':record.exchange_rate,
    #                         #
    #                         # }),
    #                         (0, 0, {
    #                             'name': record.name,
    #                             'account_id': record.account_id.id,
    #                             # 'debit': 0.0,
    #                             # 'credit': line.amortization * rate,
    #                             'currency_id': record.currency_id.id,
    #                             # 'currency_rate': record.exchange_rate,
    #                             'amount_currency': -line.amortization
    #                         }),
    #                     ],
    #                 })
    #
    #                 journal_entry.write({'bond_id': record.id})
    #
    #             record.write({'state': 'posted'})

    def action_approve(self):
        for record in self:
            rate = record.currency_id.rate
            journal = record.env['account.journal'].sudo().search([('name', '=', 'Bonds')], limit=1)
            if not journal:
                raise ValidationError("Bonds journal not found")

            if not record.settlement_date:
                raise ValidationError("Please set Settlement Date")
            if record.broker_bank == 'broker' and not record.broker_id:
                raise ValidationError("Please set the Broker Name")
            if record.broker_bank == 'bank' and not record.bank_id:
                raise ValidationError("Please set the Bank Account")

            # Define the debit and credit lines based on bank or broker
            debit_line = {
                'name': record.investment_id.name,
                'account_id': record.investment_id.account_id.id,
                'currency_id': record.currency_id.id,
                'amount_currency': record.total_cost,
            }

            if record.bank_id:
                credit_line = {
                    'name': record.bank_id.name,
                    'account_id': record.bank_id.id,
                    'currency_id': record.currency_id.id,
                    'amount_currency': -record.total_cost,
                }
            else:
                credit_line = {
                    'name': record.broker_id.name,
                    'account_id': record.broker_id.property_account_payable_id.id,
                    'currency_id': record.currency_id.id,
                    'amount_currency': -record.total_cost,
                }

            # Create the journal entry
            journal_entry = self.env['account.move'].create({
                'journal_id': journal.id,
                'date': record.settlement_date,
                'ref': record.name,
                'line_ids': [
                    (0, 0, debit_line),
                    (0, 0, credit_line),
                ]
            })
            journal_entry.write({'bond_id': record.id})
            record.write({'state': 'posted'})

            # Handling for bond lines
            if record.bond_line_ids:
                for line in record.bond_line_ids:
                    account_id = self.env['ir.config_parameter'].sudo().get_param('kg_investment.bond_account_id')
                    if not account_id:
                        raise ValidationError("Please set Account in Settings")
                    if not record.investment_id.account_id:
                        raise ValidationError("Please set Account in Investment Entry")

                    # Create journal entry for bond line
                    journal_entry = self.env['account.move'].create({
                        'journal_id': journal.id,
                        'date': line.period,
                        'ref': record.name,
                        'line_ids': [
                            (0, 0, {
                                'name': record.investment_id.name,
                                'account_id': record.investment_id.account_id.id,
                                # 'debit': line.amortization * rate,
                                # 'credit': 0.0,
                                'currency_id': record.currency_id.id,
                                'amount_currency': line.amortization

                                # 'currency_rate':record.exchange_rate,

                            }),
                            # (0, 0, {
                            #     'name': record.investment_id.name,
                            #     'account_id': account_id,
                            #     'debit': line.interest_accuired,
                            #     'credit': 0.0,
                            #     'amount_currency': record.net_value,
                            #     'currency_id': record.currency_id.id,
                            #     # 'currency_rate':record.exchange_rate,
                            #
                            # }),
                            (0, 0, {
                                'name': record.name,
                                'account_id': record.account_id.id,
                                # 'debit': 0.0,
                                # 'credit': line.amortization * rate,
                                'currency_id': record.currency_id.id,
                                # 'currency_rate': record.exchange_rate,
                                'amount_currency': -line.amortization
                            }),
                        ],
                    })
                    journal_entry.write({'bond_id': record.id})

                record.write({'state': 'posted'})

    def calculate_amortisation(self):
        for rec in self:

            if rec.coupon_periodicity == 'semi':
                begin_date = rec.coupon_begin_date
                maturity_date = rec.maturity_date
                period = relativedelta(months=6)  # Semi-annual payment

                # Calculate the number of periods excluding the first date and adjust for the last period
                num_periods = (maturity_date.year - begin_date.year) * 2 + (
                            maturity_date.month - begin_date.month) // 6 + 1

                print(f"Begin Date: {begin_date}")
                print(f"Maturity Date: {maturity_date}")
                print(f"Period: {period}")
                print(f"Number of Semi-Annual Periods: {num_periods}")

                line_ids = []
                prev_carry_value = rec.total_cost
#                check num periods
#                 for i in range(num_periods):
#                 end to check num periods
                for i in range(num_periods-1):
                    if i == num_periods - 1:
                        # Last period calculation to maturity date
                        period_start_date = begin_date + relativedelta(months= 6 *i)
                        period_end_date = maturity_date

                        # Calculate cash paid for the last period
                        days_in_last_period1 = (period_end_date - period_start_date).days

                        months_in_last_period = (period_end_date.year - period_start_date.year) * 12 + (
                                    period_end_date.month - period_start_date.month)

                        # Calculate days in last period, assuming 30 days per month
                        days_in_last_period = months_in_last_period * 30
                        days_in_full_period = 180  # 6 months * 30 days/month
                        print("days_in_last_period",days_in_last_period)
                        cash_paid = rec.maturity_value * (rec.coupon_rate / rec.payment_frequency) * (
                                    days_in_last_period / days_in_full_period)
                        interest_accrued = prev_carry_value * (rec.yield_val / rec.payment_frequency) * (
                                days_in_last_period1 / days_in_full_period)


                    else:

                        period_start_date = begin_date + relativedelta(months=6 * i)
                        period_end_date = begin_date + relativedelta(months=6 * (i +1))

                        cash_paid = rec.maturity_value * (rec.coupon_rate / rec.payment_frequency)
                        interest_accrued = prev_carry_value * (rec.yield_val / rec.payment_frequency)

                    # interest_accrued = (prev_carry_value * rec.yield_val) / rec.payment_frequency
                    amortization = cash_paid - interest_accrued if rec.purchase_price > 100 else interest_accrued-cash_paid

                    carry_value = prev_carry_value - amortization if rec.maturity_value < prev_carry_value else prev_carry_value + amortization

                    line_ids.append((0, 0, {
                        'period': period_end_date,
                        'cash_paid': cash_paid,
                        'interest_accuired': interest_accrued,
                        'amortization': amortization,
                        'carry_value': carry_value,
                    }))
                    prev_carry_value = carry_value

                rec.bond_line_ids = False
                rec.bond_line_ids = line_ids

                print("rec.bond_line_ids", rec.bond_line_ids)


            elif rec.coupon_periodicity == 'quarter':
                begin_date = rec.coupon_begin_date
                maturity_date = rec.maturity_date
                num_periods = (maturity_date.year - begin_date.year) * 4 + (
                            maturity_date.month - begin_date.month) // 3 + 1
                prev_carry_value = rec.total_cost
                line_ids = []

                for i in range(num_periods):
                    if i == num_periods - 1:
                        # Last period calculation to maturity date
                        period_start_date = begin_date + relativedelta(months=3 * i)
                        period_end_date = maturity_date

                        # Calculate cash paid for the last period
                        days_in_last_period = (period_end_date - period_start_date).days
                        days_in_full_period = 90  # 3 months * 30 days/month

                        cash_paid = rec.maturity_value * (rec.coupon_rate / rec.payment_frequency) * (
                                    days_in_last_period / days_in_full_period)


                    else:
                        period_start_date = begin_date + relativedelta(months=3 * i)
                        period_end_date = begin_date + relativedelta(months=3 * (i + 1))

                        cash_paid = rec.maturity_value * (rec.coupon_rate / rec.payment_frequency)

                    interest_accrued = prev_carry_value * (rec.yield_val / rec.payment_frequency)
                    amortization = cash_paid - interest_accrued
                    carry_value = prev_carry_value - amortization if rec.maturity_value < prev_carry_value else prev_carry_value + amortization

                    line_ids.append((0, 0, {
                        'period': period_end_date,
                        'cash_paid': cash_paid,
                        'interest_accrued': interest_accrued,
                        'amortization': amortization,
                        'carry_value': carry_value,
                    }))
                    prev_carry_value = carry_value

                rec.bond_line_ids = False
                rec.bond_line_ids = line_ids



            elif rec.coupon_periodicity == 'annual':

                begin_date = rec.coupon_begin_date

                maturity_date = rec.maturity_date

                num_periods = maturity_date.year - begin_date.year + 1

                prev_carry_value = rec.total_cost

                line_ids = []

                for i in range(num_periods):

                    if i == num_periods - 1:

                        # Last period calculation to maturity date

                        period_start_date = begin_date + relativedelta(years=i)

                        period_end_date = maturity_date

                        # Calculate cash paid for the last period

                        days_in_last_period = (period_end_date - period_start_date).days

                        days_in_full_year = 365

                        cash_paid = rec.maturity_value * (rec.coupon_rate / rec.payment_frequency) * (
                                    days_in_last_period / days_in_full_year)


                    else:

                        period_start_date = begin_date + relativedelta(years=i)

                        period_end_date = begin_date + relativedelta(years=i + 1)

                        cash_paid = rec.maturity_value * (rec.coupon_rate / rec.payment_frequency)

                    interest_accrued = prev_carry_value * (rec.yield_val / rec.payment_frequency)

                    amortization = cash_paid - interest_accrued

                    carry_value = prev_carry_value - amortization if rec.maturity_value < prev_carry_value else prev_carry_value + amortization

                    line_ids.append((0, 0, {

                        'period': period_end_date,

                        'cash_paid': cash_paid,

                        'interest_accrued': interest_accrued,

                        'amortization': amortization,

                        'carry_value': carry_value,

                    }))

                    prev_carry_value = carry_value

                rec.bond_line_ids = False

                rec.bond_line_ids = line_ids

    def view_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.journal_entry_ids.ids)],
        }

    def post_bond_journal_entries(self):
        today = datetime.today().date()

        # Fetch all draft journal entries related to bonds that match today's date
        bond_entries = self.env['account.move'].sudo().search([
            ('state', '=', 'draft'),
            ('journal_id.name', '=', 'Bonds'),  # Adjust if needed
            ('date', '<=', today),
        ])

        # Post each draft journal entry found
        for entry in bond_entries:
            try:
                entry.action_post()
            except Exception as e:
                pass


class KGBondsAmortizationLine(models.Model):
    _name = 'kg.bonds.amortization.line'

    bond_id = fields.Many2one('kg.bonds', string='Bond')

    cash_paid = fields.Monetary(string='Cash Received', default=0.0)
    interest_accuired = fields.Monetary(string='Interest Accrued')
    amortization = fields.Monetary(string='Amortization')
    carry_value = fields.Monetary(string='Carry Value')
    currency_id = fields.Many2one('res.currency', string='Currency', )
    period = fields.Date(string='Period', required=True)
