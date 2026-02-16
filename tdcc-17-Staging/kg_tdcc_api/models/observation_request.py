from odoo import models, fields, api, _
import random
import string


class KgObservationRequest(models.Model):
    _name = 'kg.observation.request'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Observation Request'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    """mandatory fields"""

    set_id_obr = fields.Char(string="Set ID – OBR", help="Put sequence number for each of the record as 1,2,3 etc.")
    placer_order_no = fields.Char(string="Placer Order Number")
    fillr_order_no = fields.Char(string="Filler Order Number",
                                 help="If Filler Number does not exist, please add Order Number here")
    universl_servc_idntfr = fields.Char(string="Universal Service Identifier",
                                        help="Identifier code for the requested observation")
    priorty_obr = fields.Char(string="Priority – OBR")
    specimn_action_code = fields.Char(string="Specimen Action Code")
    clinicl_info = fields.Char(string="Relevant Clinical Information")
    spcimen_name_code = fields.Char(string="Specimen Source Name or Code")
    orderng_provider = fields.Char(string="Ordering Provider")
    servc_sction_id = fields.Char(string="Diagnostic Service Section ID")
    result_status = fields.Char(string="Result Status")
    parent_result = fields.Char(string="Parent Result")
    parent = fields.Char(string="Parent")
    reason_study = fields.Char(string="Reason for Study")
    result_interprtr = fields.Char(string="Principal Result Interpreter")
    quantity_timing = fields.Char(string="Quantity / Timing", help="Order quantity details")
    result_to = fields.Char(string="Result Copies To",
                            help="Identifies the people who are to receive copies of the results")
    reqsted_date = fields.Datetime(string="Requested Date / Time", help="Start date and time of the Order")
    observation_date = fields.Datetime(string="Observation Date / Time", help="Date/time the specimen was collected")
    specimn_recvd_date = fields.Datetime(string="Specimen Received Date / Time")
    result_status_date = fields.Datetime(string="Results Rpt / Status Chng – Date / Time",
                                         help="If the associated order has a result, this must be a set")
    order_calbck_phnno = fields.Integer(string="Order Callback Phone Number")

    """non mandatory fields"""

    observation_end_date = fields.Datetime(string="Observation End Date / Time")
    scheduled_date = fields.Datetime(string="Scheduled Date/Time")
    collction_volum = fields.Char(string="Collection Volume")
    collction_identfr = fields.Char(string="Collection Identifier")
    danger_code = fields.Char(string="Danger Code")
    placer_field1 = fields.Char(string="Placer Field 1")
    placer_field2 = fields.Char(string="Placer Field 2")
    filler_field1 = fields.Char(string="Filler Field 1")
    filler_field2 = fields.Char(string="Filler Field 2")
    charge_parctice = fields.Char(string="Charge to Practice")
    transport_mode = fields.Char(string="Transportation Mode")
    assist_reslt_intrprtr = fields.Char(string="Assistant Result Interpreter")
    technician = fields.Char(string="Technician")
    transcriptionist = fields.Char(string="Transcriptionist")
    sample_container_no = fields.Char(string="Number of Sample Containers")
    transport_collctd_sample = fields.Char(string="Transport Logistics of Collected Sample")
    collector_comment = fields.Char(string="Collector's Comment")
    trans_arrngmnt_respo = fields.Char(string="Transport Arrangement Responsibility")
    trans_arrnged = fields.Char(string="Transport Arranged")
    escot_reqed = fields.Char(string="Escort Required")
    planed_patient_transpt = fields.Char(string="Planned Patient Transport Comment")
    procedure_code = fields.Char(string="Procedure Code")
    procedure_code_modfr = fields.Char(string="Procedure Code Modifier")
    placer_servc_info = fields.Char(string="Placer Supplemental Service Information")
    filler_servc_info = fields.Char(string="Filler Supplemental Service Information")
    duplicte_procdr_resn = fields.Char(string="Medically Necessary Duplicate Procedure Reason")
    result_handling = fields.Char(string="Result Handling")
    parnt_univrsl_idntfr = fields.Char(string="Parent Universal Service Identifier")

    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.observation.request') or _('New')
        request = super(KgObservationRequest, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_obr': self.set_id_obr,
            'placer_order_no': self.placer_order_no,
            'fillr_order_no': self.fillr_order_no,
            'universl_servc_idntfr': self.universl_servc_idntfr,
            'priorty_obr': self.priorty_obr,
            'specimn_action_code': self.specimn_action_code,
            'clinicl_info': self.clinicl_info,
            'spcimen_name_code': self.spcimen_name_code,
            'orderng_provider': self.orderng_provider,
            'servc_sction_id': self.servc_sction_id,
            'result_status': self.result_status,
            'parent_result': self.parent_result,
            'parent': self.parent,
            'reason_study': self.reason_study,
            'result_interprtr': self.result_interprtr,
            'quantity_timing': self.quantity_timing,
            'result_to': self.result_to,
            # 'reqsted_date': self.reqsted_date,
            # 'observation_date': self.observation_date,
            # 'specimn_recvd_date': self.specimn_recvd_date,
            # 'result_status_date': self.result_status_date,
            'order_calbck_phnno': self.order_calbck_phnno,
            # 'observation_end_date': self.observation_end_date,
            # 'scheduled_date': self.scheduled_date,
            'collction_volum': self.collction_volum,
            'collction_identfr': self.collction_identfr,
            'danger_code': self.danger_code,
            'placer_field1': self.placer_field1,
            'placer_field2': self.placer_field2,
            'filler_field1': self.filler_field1,
            'filler_field2': self.filler_field2,
            'charge_parctice': self.charge_parctice,
            'transport_mode': self.transport_mode,
            'assist_reslt_intrprtr': self.assist_reslt_intrprtr,
            'technician': self.technician,
            'transcriptionist': self.transcriptionist,
            'sample_container_no': self.sample_container_no,
            'transport_collctd_sample': self.transport_collctd_sample,
            'collector_comment': self.collector_comment,
            'trans_arrngmnt_respo': self.trans_arrngmnt_respo,
            'trans_arrnged': self.trans_arrnged,
            'escot_reqed': self.escot_reqed,
            'planed_patient_transpt': self.planed_patient_transpt,
            'procedure_code': self.procedure_code,
            'procedure_code_modfr': self.procedure_code_modfr,
            'placer_servc_info': self.placer_servc_info,
            'filler_servc_info': self.filler_servc_info,
            'duplicte_procdr_resn': self.duplicte_procdr_resn,
            'result_handling': self.result_handling,
            'parnt_univrsl_idntfr': self.parnt_univrsl_idntfr,
        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
