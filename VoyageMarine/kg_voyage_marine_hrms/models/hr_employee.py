from odoo import models, fields,_,api


class KGHREmployeeInherit(models.Model):
    _inherit = "hr.employee"

    outsource_employee = fields.Boolean(default=False, string="Outsource Employee")
    visa_designation_id = fields.Many2one("visa.designation", string="Visa Designation")
    joining_date = fields.Date(string='Date of Join', help="Employee joining date ")
    leaving_date = fields.Date(string='Date of Exit', help="Employee Leaving date ")
    branch = fields.Char(string="Branch")
    contract_type = fields.Selection([('limited', 'Limited'), ('unlimited', 'Unlimited')], string="Contract Type",
                                     default='limited')
    father_name = fields.Char(string="Father's Name")
    mother_name = fields.Char(string="Mother's Name")
    staff_worker = fields.Selection([('management', 'Management'), ('technical', 'Technical')], string="Staff/Worker",
                                    default='management')

    visa_type = fields.Selection([('permanent', 'Permanent'), ('temporary', 'Temporary')], string="Visa Type",
                                 default='permanent')
    visa_issue_date = fields.Date(string="Visa Issue Date")

    passport_issue_from = fields.Char(string="Passport Issue From")
    passport_issue_date = fields.Date(string="Passport Issue Date")
    passport_expiry_date = fields.Date(string="Passport Expiry Date")

    personal_no_from_labour_card = fields.Char(striing="Personal Number from Labor card")
    labour_card_no = fields.Char(string="Labour Card No")
    labour_card_issue_date = fields.Date(string="Labour Card Issue Date")
    labour_card_expiry_date = fields.Date(string="Labour Card Expiry Date")

    medical_insurance_no =fields.Char(string="Medical Insurance No")
    medical_insurance_category =fields.Char(string="Medical Insurance Category")
    medical_insurance_issue_date =fields.Date(string="Medical Insurance Card Issue Date")
    medical_insurance_expiry_date =fields.Date(string="Medical Insurance Card Expiry Date")

    accomodation = fields.Char(string="Accomodation")


    @api.model
    def create(self, vals):
        if vals.get('employee_no', _('New')) == _('New'):
            vals['employee_no'] = self.env['ir.sequence'].next_by_code('employee.seq') or _('New')
        return super(KGHREmployeeInherit, self).create(vals)

    employee_no = fields.Char('Employee Number',copy=False, index=True, readonly=False, default=lambda self: _('New'))

    # @api.model
    # def create(self, vals):
    #
    #     if vals.get('company_id'):
    #         company_obj = self.env['res.company'].browse(vals.get('company_id'))
    #         if company_obj.country_code == 'US':
    #             vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_us') or 'New'
    #         elif company_obj.country_code == 'BH':
    #             vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_bh') or 'New'
    #         elif company_obj.country_code == 'IN':
    #             vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_in') or 'New'
    #         elif company_obj.country_code == 'OM':
    #             vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_om') or 'New'
    #         elif company_obj.country_code == 'AE':
    #             vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_dubai') or 'New'
    #         else:
    #             vals['employee_id'] = 'New'
    #         if vals.get('employee_no', 'New') == 'New':
    #             if company_obj.employee_sequence_id:
    #                 vals['employee_no'] = company_obj.employee_sequence_id.next_by_id()
    #         return super(KGHREmployeeInherit, self).create(vals)


