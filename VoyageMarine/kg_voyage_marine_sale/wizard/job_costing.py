from odoo import models, fields, api, _


class KGJobcostingWizard(models.TransientModel):
    _name = 'job.costing'

    saleoder_id = fields.Many2many('sale.order', string="Sale order")
    calibration_ids = fields.Many2many('calibration.form','calibration_rel', string="Calibration ",
                                       domain="[('saleorder_id', 'in', saleoder_id)]")
    lsa_ids = fields.Many2many('lsa.form', 'lsa_rel',  string="LSA ", domain="[('saleorder_id', 'in', saleoder_id)]")
    ffa_ids = fields.Many2many('ffa.form', 'ffa_rel', string="FFA Forms", domain="[('saleorder_id', 'in', saleoder_id)]")
    navigation_communication_ids = fields.Many2many('navigation.communication','navcm_rel',
                                                    string="Navigation Communication",
                                                    domain="[('saleorder_id', 'in', saleoder_id)]")
    field_service_ids = fields.Many2many('field.service','field_serv_rel',  string="Field Service",
                                         domain="[('saleorder_id', 'in', saleoder_id)]")
    is_jobsheet = fields.Boolean(string="IS jobsheet")

    def load_job_costing_data(self):
        vals = []
        rep = []
        sale_order = self.saleoder_id
        if self.is_jobsheet:
            calibration_form = self.env['calibration.form'].search([('saleorder_id', '=', sale_order.ids)])
            lsa_form = self.env['lsa.form'].search([('saleorder_id', '=', sale_order.ids)])
            ffa_form = self.env['ffa.form'].search([('saleorder_id', '=', sale_order.ids)])
            navigation_communication_form = self.env['navigation.communication'].search(
                [('saleorder_id', '=', sale_order.ids)])
            field_service_form = self.env['field.service'].search([('saleorder_id', '=', sale_order.ids)])
            repair_orders = self.env['repair.order'].search([
                ('saleorder_id', '=', sale_order.ids),
                '|', '|', '|', '|',
                ('job_ref_lsa', "=", lsa_form.ids if lsa_form else False),
                ('job_ref_calibration', "=", calibration_form.ids if calibration_form else False),
                ('job_ref_ffa', "=", ffa_form.ids if ffa_form else False),
                ('job_ref_nav_comm', "=", navigation_communication_form.ids if navigation_communication_form else False),
                ('job_ref_field_service', "=", field_service_form.ids if field_service_form else False),
                ('state', '=', 'done')
            ])
            for repair_order in repair_orders:
                moves = repair_order.mapped('move_ids')
                mr_id = self.env['material.purchase.requisition'].search([('repair_id', '=', repair_order.id)])
                mr = mr_id.id
                purchase_order_lines = self.env['purchase.order'].search(
                    [('pr_requisition_ids', '=', mr), ('state', '=', 'purchase')])
                if purchase_order_lines:
                    price_unit_purchase = purchase_order_lines.order_line[0].price_unit
                else:
                    price_unit_purchase = None
                for move in moves:
                    name = move.name
                    product_id = move.product_id.name
                    qty = move.product_uom_qty
                    price_unit = move.price_unit
                    unit_price = "{:.2f}".format(price_unit_purchase) if price_unit_purchase else "{:.2f}".format(
                        price_unit)
                    rep.append({
                        'name': name,
                        'product_id': product_id,
                        'unit_price': unit_price,
                        'qty': "{:.2f}".format(qty),
                    })
            for form in [calibration_form, lsa_form, ffa_form, navigation_communication_form, field_service_form]:
                form_name = ''
                if form == calibration_form:
                    form_name = 'Calibration'
                elif form == lsa_form:
                    form_name = 'LSA'
                elif form == ffa_form:
                    form_name = 'FFA'
                elif form == navigation_communication_form:
                    form_name = 'Navigation Communication'
                elif form == field_service_form:
                    form_name = 'Field Service'
                for record in form:
                    name = record.name if hasattr(record, 'name') else ''
                    product_id = record.product_id.name if hasattr(record, 'product_id') else None
                    unit_price = 0.0
                    qty = 0
                    if form == calibration_form:
                        unit_price = record.price_unit if hasattr(record, 'price_unit') else 0.0
                        qty = record.qty_calibration if hasattr(record, 'qty_calibration') else 0.0
                    elif form == lsa_form:
                        unit_price = record.price_unit if hasattr(record, 'price_unit') else 0.0
                        qty = record.qty_lsa if hasattr(record, 'qty_lsa') else 0.0
                    elif form == ffa_form:
                        unit_price = record.price_unit if hasattr(record, 'price_unit') else 0.0
                        qty = record.qty_ffa if hasattr(record, 'qty_ffa') else 0.0
                    elif form == navigation_communication_form:
                        unit_price = record.price_unit if hasattr(record, 'price_unit') else 0.0
                        qty = record.qty_navigation if hasattr(record, 'qty_navigation') else 0.0
                    elif form == field_service_form:
                        unit_price = record.price_unit if hasattr(record, 'price_unit') else 0.0
                        qty = record.qty_field_service if hasattr(record, 'qty_field_service') else 0.0
                    vals.append({
                        'name': name,
                        'product_id': product_id,
                        'unit_price': "{:.2f}".format(unit_price),
                        'qty': "{:.2f}".format(qty),
                        'form_type': form_name
                    })
        else:
            sale_order_lines = sale_order.order_line
            for line in sale_order_lines:
                product_id = line.product_id.name
                qty = line.product_uom_qty
                unit_price = line.price_unit
                vals.append({
                    'name': line.name,
                    'product_id': product_id,
                    'unit_price': "{:.2f}".format(unit_price),
                    'qty': "{:.2f}".format(qty),
                    'form_type': ''
                })
            purchase_order_lines = self.env['purchase.order'].search(
                [('so_ids', '=', sale_order.ids),
                 ('state', '=', 'purchase')])
            for purchase_order in purchase_order_lines:
                stock_moves = self.env['stock.picking'].search([
                    ('purchase_id', '=', purchase_order.id),
                    ('state', '=', 'done')
                ])
                if stock_moves:
                    for move in stock_moves.move_ids_without_package:
                        purchase_line = purchase_order.order_line.filtered(lambda l: l.product_id == move.product_id)
                        unit_price = purchase_line.price_unit if purchase_line else 0.0

                        rep.append({
                            'name': move.name,
                            'product_id': move.product_id.name,
                            'unit_price': "{:.2f}".format(unit_price),
                            'qty': "{:.2f}".format(move.product_qty),
                        })
        data = {
            'values': vals,
            'rep': rep,
            'company_name': self.env.company.name,
            'company_zip': self.env.company.zip,
            'company_state': self.env.company.state_id.name,
            'company_country_code': self.env.company.country_id.code,
            'log_user_name': self.env.user.name,
        }
        return self.env.ref('kg_voyage_marine_sale.kg_action_job_costing_report').with_context(
            landscape=False).report_action(self, data=data)
