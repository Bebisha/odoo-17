from odoo import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_type = fields.Selection([
        ('new', 'New Project'),
        ('existing', 'Existing Project')], string='Project Type',
        default='new', required=True)
    mode_of_shipment = fields.Char()

    project_id = fields.Many2one('project.project', default=False,copy=False)
    pro_id = fields.Many2one('project.project', string="Pro")
    terms_conditions_id = fields.Many2one('sale.terms.conditions', string='Terms and Conditions')
    terms_conditions = fields.Html(string='Terms and Conditions')

    your_reference = fields.Char(string='Reference')
    subject = fields.Text( string="Description")
    project_name = fields.Char(string='Project Name',copy=False)

    # project_count_new =  fields.Integer(string="Project Count", compute='_compute_project_count_new')
    #
    #
    # @api.depends('project_id')
    # def _compute_project_count_new(self):
    #     for order in self:
    #         order.project_count = self.env['project.project'].search_count([('project_id', '=', order.id)])
    button_invisible = fields.Boolean(string='Button Invisible', compute='_compute_button_invisible', default=True)

    # @api.depends('project_ids')
    # def _compute_project_count(self):
    #     for order in self:
    #         order.project_count = len(order.project_ids)

    @api.onchange('terms_conditions_id')
    def _onchange_terms_conditions_id(self):
        for rec in self:
            rec.terms_conditions = rec.terms_conditions_id.terms_condition

    @api.depends('state', 'project_type')
    def _compute_button_invisible(self):
        for order in self:
            order.button_invisible = order.state in ['draft', 'sent'] or order.project_type == 'existing'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New' and vals.get('state', 'draft') in ('draft', 'sent'):
            if vals.get('project_type') == 'new':
                vals['name'] = self.env['ir.sequence'].next_by_code('sales.orders') or 'New'
                # default_project = self.env['project.project'].search([], limit=1)
                # vals['project_id'] = default_project.id if default_project else False

            else:
                project = self.env['project.project'].browse(vals['project_id'])
                if project.project_sequence:
                    sequence = project.project_sequence
                    parts = sequence.split(" - ")

                    if len(parts) == 2:
                        part1, part2 = parts
                        last_letter = part1[-1]
                    else:
                        last_letter = sequence[-1]

                    next_letter = chr(ord(last_letter) + 1)
                    if next_letter > 'Z':
                        raise ValueError("Sequence letters exhausted")

                    if len(parts) == 2:
                        new_sequence = part1[:-1] + next_letter
                    else:
                        new_sequence = sequence[:-1] + next_letter

                    vals['name'] = new_sequence

        sale_order = super(SaleOrder, self).create(vals)

        # Link sale order to the project


        return sale_order

    def action_confirm(self):
        for order in self:
            # ✅ Open wizard only if project_type is 'new' AND project_name is empty
            if order.project_type == 'new' and not order.project_name:
                return order.action_open_confirm_wizard()

        # Otherwise continue normal confirmation
        result = super(SaleOrder, self).action_confirm()

        for order in self:
            sequence = order.name
            existing_project = order.project_id
            product_names = [line.product_id.name for line in order.order_line]
            product_names_str = ', '.join(product_names)

            # === CASE 1: Create new project (when project_name already exists) ===
            if order.project_type == 'new' and order.project_name:
                project_name = order.project_name or f"{sequence} - {product_names_str}"
                vals = {
                    'name': project_name,
                    'partner_id': order.partner_id.id,
                    'sale': order.id,
                    'user_id': order.user_id.id,
                    'company_id': order.company_id.id,
                    'allow_billable': True,
                    'project_sequence': order.name,
                }
                project = self.env['project.project'].sudo().create(vals)
                order.write({'project_id': project.id})

            # === CASE 2: Existing project ===
            elif order.project_type == 'existing' and existing_project:
                existing_project.write({'project_sequence': order.name})
                project = existing_project
            else:
                continue

            # === Create linked stock location ===
            stock_location = self.env['stock.location'].create({
                'name': f"Location for {project.name}",
                'usage': 'internal',
            })
            project.stock_location_id = stock_location.id

            if hasattr(stock_location, 'is_project_location'):
                stock_location.is_project_location = True

        return result

    def action_open_confirm_wizard(self):
        self.ensure_one()
        sequence = self.name
        product_names = [line.product_id.name for line in self.order_line]
        product_names_str = ', '.join(product_names)
        return {
            'name': 'Update Project Name',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_project_name':f"{sequence} - {product_names_str}"
            }
        }

    def get_bom_values(self):
        for rec in self:
            project_id = rec.project_id
            bom = self.env['bom.selection'].search([('project_id', '=', project_id.id)])
            bom_categories = bom.mapped('bom_category_id')
            product_categories = self.env['bom.master'].search([('bom_category_id', 'in', bom_categories.ids)]).mapped(
                'category_ids')
            category_product_details = {}
            product_categories = product_categories.sorted(key='id', reverse=False)

            for category in product_categories:
                products = bom.bom_selection_ids.mapped('product_id')

                if category not in category_product_details:
                    category_product_details[category] = []

                products = products.filtered(lambda x: x.categ_id == category)

                for product in products:
                    uom_id = None
                    product_details = {}

                    for bom_cat in bom_categories:
                        bom_line = self.env['bom.selection.line'].search([
                            ('bom_selection_id', 'in', bom.ids),
                            ('product_id', '=', product.id),
                            ('bom_selection_id.bom_category_id', '=', bom_cat.id)
                        ])
                        uom_id = bom_line.mapped('uom_id') or uom_id
                        qty = bom_line.mapped('qty')

                        product_details[bom_cat] = sum(qty) if qty else 0

                    if product_details:
                        category_product_details[category].append({
                            product: {'bom': product_details, 'uom': uom_id}
                        })

            # Return the final structured dictionary
            return category_product_details

    def action_view_projectss(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project',
            'view_mode': 'tree,form',
            'res_model': 'project.project',
            'context': "{'create':False}",
            'res_id': self.project_id.sale.id,
            'domain': [('id', '=', self.project_id.id)]
        }

    def action_view_variation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Variation',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'context': "{'create':False}",
            # 'res_id': self.project_id.sale.id,
            'domain': [('project_id', '=', self.project_id.id)]
        }


# def action_view_project(self):
#     return {
#         'name': 'Project',
#         'res_model': 'sale.order',
#         'type': 'ir.actions.act_window',
#         'views': [(False, 'tree'), (False, 'form')],
#         'view_mode': 'tree,form',
#         # 'context': {'default_project_id': self.id},
#         'domain': [('project_id', '=', self.project_id.sale_order_id)],
#         'target': 'current',
#
#     }

# def create_property_unit_location(self):
#     for order in self:
#         # Logic to create a project if needed (assuming the project is created here)
#         project = self.env['project.project']
#
#         # Logic to create a stock location linked to the project
#         stock_location = self.env['stock.location'].create({
#             'name': f"Location for {project.name}",
#             'usage': 'internal',  # or another usage type as needed
#             # other necessary stock location fields
#         })
#
#         # Store the created stock location in the project
#         project.stock_location_id = stock_location.id
#
#     return


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_project_location = fields.Boolean('Is Project location')
