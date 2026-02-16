from odoo import models, api


# class Project(models.Model):
#     _inherit = 'project.project'
#
#     @api.model
#     def action_create_project(self, vals_list=None):
#         """
#         This method will be called from button that we have created using owl js
#         """
#         if not vals_list:
#             vals_list = [{'name': 'Test Project'}]
#         project = self.create(vals_list)
#         return project
#


class Project(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def action_create_project(self, vals_list=None):
        current_user = self.env.user
        salespersons = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').ids)
        ])
        if not vals_list:
            vals_list = [{'name': 'Test Project'}]

        # Additional logic to use selected salesperson from vals_list
        if vals_list.get('salesperson_id'):
            vals_list['salesperson_id'] = int(vals_list['salesperson_id'])

        project = self.create(vals_list)
        return project

    @api.model
    def fetch_salespersons(self):
        # Fetch salespersons who belong to 'Salesman' group
        salespersons = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').ids)
        ])

        # Return a list of dictionaries with id and name
        return [{
            'id': salesperson.id,
            'name': salesperson.name,
        } for salesperson in salespersons]










    # @api.model
    # def action_create_project(self, project_data):
    #     selected_salesperson_id = project_data.get('salesperson_id')
    #     # Your logic to create project with selected salesperson
    #     project = self.create({
    #         'name': project_data.get('name'),
    #         'user_id': selected_salesperson_id,  # Assuming 'user_id' is the field for salesperson
    #         # Add other fields as needed
    #     })
    #     return project

