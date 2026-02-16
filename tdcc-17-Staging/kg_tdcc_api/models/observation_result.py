from odoo import models, fields, api, _
import random
import string


class KgObservation(models.Model):
    _name = 'kg.observation'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Observation / Result'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    set_id_box = fields.Char(string="Set ID – OBX")
    value_type = fields.Char(string="Value Type")
    observation_identifier = fields.Char(string="Observation Identifier")
    observation_sub_id = fields.Char(string="Observation Sub-ID")
    observation_value = fields.Binary(string="Observation Value")
    units = fields.Char(string="Units")
    references_range = fields.Integer(string="References Range")
    abnormal_flags = fields.Char(string="Abnormal Flags")

    observation_result_status = fields.Selection(
        [('C', 'C'), ('D', 'D'), ('F', 'F'), ('I', 'I'), ('N', 'N'), ('O', 'O'), ('P', 'P'), ('R', 'R'),
         ('S', 'S'), ('U', 'U'), ('W', 'W'), ('X', 'X'), ],
        help="",
        string="Observation Result Status")
    observation_date = fields.Datetime(string="Date/Time of the Observation")
    analysis_date = fields.Datetime(string="Date/Time of the Analysis")
    procedures_refernc = fields.Char(string="Producer's Reference")
    responsible_observer = fields.Char(string="Responsible Observer")
    observation_method = fields.Char(string="Observation Method")
    perfrmng_orgnzn_name = fields.Char(string="Performing Organization Name")
    perfrmng_orgnzn_addres = fields.Text(string="Performing Organization Address")
    perfrmng_orgnzn_med_dirctor = fields.Char(string="Performing Organization Medical Director")

    """non mandatory fields"""

    probability = fields.Char(string="Probability")
    nature_abnormal_test = fields.Char(string="Nature of Abnormal Test")
    effct_date_ref_rang = fields.Date(string="Effective Date of Reference Range Values")
    user_defnd_acces_check = fields.Char(string="User Defined Access Checks")
    equip_instanc_identifr = fields.Char(string="Equipment Instance Identifier")
    reserved_harmonizatn = fields.Char(string="Reserved for harmonization with v2.6.")

    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.observation') or _('New')
        request = super(KgObservation, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_box': self.set_id_box,
            'value_type': self.value_type,
            'observation_identifier': self.observation_identifier,
            'observation_sub_id': self.observation_sub_id,
            # 'observation_value': self.observation_value,
            'units': self.units,
            'references_range': self.references_range,
            'abnormal_flags': self.abnormal_flags,
            'observation_result_status': self.observation_result_status,
            # 'observation_date': self.observation_date,
            # 'analysis_date': self.analysis_date,
            'procedures_refernc': self.procedures_refernc,
            'responsible_observer': self.responsible_observer,
            'observation_method': self.observation_method,
            'perfrmng_orgnzn_name': self.perfrmng_orgnzn_name,
            'perfrmng_orgnzn_addres': self.perfrmng_orgnzn_addres,
            'perfrmng_orgnzn_med_dirctor': self.perfrmng_orgnzn_med_dirctor,
            'probability': self.probability,
            'nature_abnormal_test': self.nature_abnormal_test,
            # 'effct_date_ref_rang': self.effct_date_ref_rang,
            'user_defnd_acces_check': self.user_defnd_acces_check,
            'equip_instanc_identifr': self.equip_instanc_identifr,
            'reserved_harmonizatn': self.reserved_harmonizatn,

        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
