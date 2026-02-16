# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. LtdF
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api
import logging

_logger = logging.getLogger('odoo.addons.base.partner.merge')


class KGMergePatient(models.TransientModel):
    _name = 'merge.record'
    _description = 'Merger Patient'

    merge_patient_ids = fields.Many2many('res.partner',
                                         string='Merge patient')
    merged_patient_ids = fields.Many2many('res.partner', related='patient_id.merge_record_ids')
    patient_id = fields.Many2one('res.partner', string='Patient')
    merge_id = fields.Many2one('res.partner', 'Merge')


    def merge_record(self):
        partners = self.env['res.partner'].browse(self.merge_patient_ids.ids)

        for rec in partners:
            other_partners = rec
            main_partner = self.patient_id


            for partner in main_partner:

                partner.write({
                    'patient_identifer_ids': [(4, patient_identifier.id) for patient_identifier in
                                              other_partners.patient_identifer_ids],
                    'associated_parties_ids': [(4, associated_parties.id) for associated_parties in
                                              other_partners.associated_parties_ids],
                    'guarantor_ids': [(4, guarantor.id) for guarantor in
                                              other_partners.guarantor_ids],
                    'segment_family_history_ids': [(4, segment_family_history.id) for segment_family_history in
                                              other_partners.segment_family_history_ids],
                    'z_consent_ids': [(4, z_consent.id) for z_consent in
                                              other_partners.z_consent_ids],
                    'insurance_ids': [(4, insurance.id) for insurance in
                                              other_partners.insurance_ids],

                })

        self.patient_id.merge_patient()


class MergePartnerApi(models.TransientModel):

    _inherit = 'base.partner.merge.automatic.wizard'

    @api.model
    def default_get(self, fields):
        res = super(MergePartnerApi, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        if active_model == 'res.partner' and active_ids:
            partners = self.env['res.partner'].browse(active_ids)
            reference_email = partners[0].email if partners else False

            if reference_email:
                dupl_partners = self.env['res.partner'].search([('email', '=', reference_email)])

                if dupl_partners:
                    if 'partner_ids' in fields:
                        res['partner_ids'] = [(6, 0, dupl_partners.ids)]

            if 'state' in fields:
                res['state'] = 'selection'
            if 'partner_ids' in fields:
                res['partner_ids'] = [(6, 0, dupl_partners.ids)]

        if self.env.context.get('active_model') == 'merge.confirmation.wizard':
            wizards = self.env['merge.confirmation.wizard'].browse(self.env.context.get('active_ids', []))
            if wizards:
                reference_email = wizards[0].student_id.email
                reference_id = wizards[0].student_id.id
                if reference_email:
                    duplicate_partners = self.env['res.partner'].search([('email', '=', reference_email)])
                    print(duplicate_partners,"duplicate_partners")
                    if duplicate_partners:
                        if 'partner_ids' in fields:
                            res['partner_ids'] = [(6, 0, duplicate_partners.ids)]
                            res['dst_partner_id'] = reference_id
                            print( res['partner_ids']," res['partner_ids']")
                if 'state' in fields:
                    res['state'] = 'selection'
                if 'partner_ids' in fields:
                    res['partner_ids'] = [(6, 0, duplicate_partners.ids)]
                    print(res['partner_ids'],"res['partner_ids']")

        return res

    def _log_merge_operation(self, src_partners, dst_partner):

        dst_partner.write({
            'patient_identifer_ids': [(4, patient_identifier.id) for patient_identifier in
                                      src_partners.patient_identifer_ids],
            'associated_parties_ids': [(4, associated_parties.id) for associated_parties in
                                       src_partners.associated_parties_ids],
            'guarantor_ids': [(4, guarantor.id) for guarantor in
                              src_partners.guarantor_ids],
            'segment_family_history_ids': [(4, segment_family_history.id) for segment_family_history in
                                           src_partners.segment_family_history_ids],
            'z_consent_ids': [(4, z_consent.id) for z_consent in
                              src_partners.z_consent_ids],
            'insurance_ids': [(4, insurance.id) for insurance in
                              src_partners.insurance_ids],

        })

        rec = super(MergePartnerApi, self)._log_merge_operation(src_partners, dst_partner)
        dst_partner.merge_patient()
        return rec
