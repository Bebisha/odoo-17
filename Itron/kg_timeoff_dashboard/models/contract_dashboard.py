from datetime import date
from odoo import models, fields, api


class KgContractDashboard(models.Model):
    _inherit = 'project.contract.request'

    def contract_request(self):
        today = date.today()
        domain = [
            ('date_start', '<=', today),
        ]

        contracts = self.env['project.contract.request'].sudo().search(domain)
        amc_contracts = self.env['project.contract.request.amc'].search(domain)
        customers = [{"id": customer.id, "name": customer.name} for customer in contracts.sudo().mapped('partner_id')]
        customerss = [{"id": customer.id, "name": customer.name} for customer in
                      amc_contracts.sudo().mapped('partner_id')]
        used_states = list(set(amc_contracts.mapped('state')))
        used_state = list(set(contracts.mapped('state')))
        full_state_selection = dict(self.env['project.contract.request.amc']._fields['state'].selection)
        state_val = [(key, full_state_selection[key]) for key in used_states if key in full_state_selection]
        full_states_selection = dict(self.env['project.contract.request']._fields['state'].selection)
        state_vals = [(key, full_states_selection[key]) for key in used_state if key in full_states_selection]
        rebion_statuses = list(set(contracts.mapped('rebion_status')))
        rebion_status_selection = dict(self._fields['rebion_status'].selection)
        rebion_status_vals = [(key, rebion_status_selection[key]) for key in rebion_statuses if
                              key in rebion_status_selection]
        rebion_statuse = list(set(amc_contracts.mapped('rebion_status')))
        rebion_statu_selection = dict(self._fields['rebion_status'].selection)
        rebion_status_val = [(key, rebion_statu_selection[key]) for key in rebion_statuse if
                              key in rebion_statu_selection]

        contract_data = []
        user_company_ids = set(self.env.user.company_ids.ids)
        for contract in contracts.filtered(
                lambda c: any(cid.id in user_company_ids for cid in c.project_id.company_ids)):

            contract_data.append({
                'id': contract.id,
                'project_id': contract.project_id.name,
                'customer_id': contract.partner_id.id,
                'customer_name': contract.partner_id.name,
                'date_start': contract.date_start.strftime('%d/%m/%Y') if contract.date_start else '',
                'date_end': contract.date_end.strftime('%d/%m/%Y') if contract.date_end else '',
                'rebion_status': dict(contract._fields['rebion_status'].selection).get(contract.rebion_status),
                'contract_type': dict(contract._fields['contract_type'].selection).get(contract.contract_type),
                'state_key': contract.state,
                'rebion_status_key': contract.rebion_status,
            })

        amc_data = []
        for amc in amc_contracts.filtered(
            lambda amc: any(comp.id in user_company_ids for comp in amc.project_id.company_ids)
        ):
            amc_data.append({
                'id': amc.id,
                'project_id': amc.project_id.name,
                'customer_id': amc.partner_id.id,
                'customer_name': amc.partner_id.name,
                'date_start': amc.date_start.strftime('%d/%m/%Y') if amc.date_start else '',
                'date_end': amc.date_end.strftime('%d/%m/%Y') if amc.date_end else '',
                'contract_type': dict(amc._fields['contract_type'].selection).get(amc.contract_type),
                'state_key': amc.state,
                'rebion_status': dict(amc._fields['rebion_status'].selection).get(amc.rebion_status),
                'rebion_status_key': amc.rebion_status,
                'planned_hrs': round(amc.planned_hrs or 0.0, 2),
                'spent_hrs': round(amc.spent_hrs or 0.0, 2),
                'description': amc.description or '',
            })

        return {
            'contracts': contract_data,
            'amc_contracts': amc_data,
            'customers': customers,
            'state_val': list(state_val),
            'state_vals': list(state_vals),
            'customerss': customerss,
            'rebion_status_vals': rebion_status_vals,
            'rebion_status_val': rebion_status_val,
        }

