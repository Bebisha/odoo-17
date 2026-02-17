from base64 import encodebytes
from io import BytesIO

import xlsxwriter
from odoo import models, fields


class UserAccessWizard(models.TransientModel):
    _name = "user.access.wizard"
    _description = "User Access Report Wizard"

    user_ids = fields.Many2many('res.users', string="Users",
                                help="Select specific users to include in the report. Leave empty for all users.")
    menu_ids = fields.Many2many('ir.ui.menu', string="Menus",
                                help="Select specific menus to include in the report. Leave empty for all menus.")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def action_menu_access_report(self):
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {
            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_menu_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        report_name = 'Users Access Report'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_menu_xlsx_report(self, workbook, data=None, objs=None):
        if self.user_ids:
            users = self.user_ids
        else:
            users = self.env['res.users'].search([])

        center_orange_color = workbook.add_format({
            'bold': True, 'align': 'center', 'bg_color': '#ffb84d', 'border': 1
        })
        left_blue_color = workbook.add_format({
            'bold': True, 'align': 'left', 'bg_color': '#4db8ff', 'border': 1
        })
        left_no_color = workbook.add_format({'align': 'left', 'border': 1})

        used_names = set()

        for user in users:
            # --- Filter menus based on menu_ids if provided ---
            if self.menu_ids:
                selected_menus = self.env['ir.ui.menu'].search([('id', 'child_of', self.menu_ids.ids)])
            else:
                selected_menus = self.env['ir.ui.menu'].search([])

            # Only menus accessible by this user
            accessible_menus = selected_menus.with_user(user).sudo()._filter_visible_menus()
            if not accessible_menus:
                continue

            # Top-level menus accessible by user
            # Only top-level menus that are accessible by user
            top_menus = accessible_menus.filtered(lambda m: not m.parent_id or m.parent_id not in accessible_menus)
            # Then remove top menus if the user has no access at all (parent menu not in accessible_menus)
            top_menus = top_menus.filtered(lambda m: m in accessible_menus)

            if not top_menus:
                continue

            # --- Prepare safe sheet name ---
            base_name = user.name[:28] if user.name else f"User-{user.id}"
            sheet_name = base_name
            counter = 1
            while sheet_name.lower() in used_names:
                sheet_name = f"{base_name}_{counter}"[:31]
                counter += 1
            used_names.add(sheet_name.lower())

            # --- Create worksheet ---
            sheet = workbook.add_worksheet(sheet_name)
            sheet.set_column(0, 0, 30)  # Main Menu
            sheet.set_column(1, 1, 60)  # Sub Menu
            sheet.write(0, 0, 'Main Menu', center_orange_color)
            sheet.write(0, 1, 'Sub Menu', center_orange_color)
            sheet.freeze_panes(1, 0)

            row = 1

            # --- Recursive function to write menus ---
            def write_menu(menu, top_menu=None, path=None):
                nonlocal row
                if path is None:
                    path = []

                current_path = path + [menu.name]

                # Column 1: top-level menu
                if not top_menu:
                    sheet.write(row, 0, menu.name, left_blue_color)
                    top_menu = menu.name
                else:
                    sheet.write(row, 0, '', left_no_color)

                # Column 2: submenu path if child
                if path:
                    sheet.write(row, 1, "/".join(current_path), left_no_color)
                row += 1

                # Only write children if parent is accessible
                children = menu.child_id.filtered(lambda m: m in accessible_menus)
                for child in children:
                    write_menu(child, top_menu, current_path)

            # --- Write each top-level menu ---
            for menu in top_menus:
                write_menu(menu)

    def action_model_access_report(self):
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {
            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_model_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        report_name = 'Users Access Report'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    # def generate_model_xlsx_report(self, workbook, data=None, objs=None):
    #     if self.user_ids:
    #         users = self.user_ids
    #     else:
    #         users = self.env['res.users'].search([])
    #
    #     center_orange_color = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#ffb84d', 'border': 1})
    #     left_blue_color = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#4db8ff', 'border': 1})
    #     left_no_color = workbook.add_format({'align': 'left', 'border': 1})
    #     center_no_color = workbook.add_format({'align': 'center', 'border': 1})
    #     menu_color = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#d9d9d9', 'border': 1})
    #
    #     used_names = set()
    #
    #     for user in users:
    #         base_name = (user.name or f"User-{user.id}")[:28]
    #         sheet_name = base_name
    #         counter = 1
    #         while sheet_name.lower() in used_names:
    #             sheet_name = f"{base_name}_{counter}"[:31]
    #             counter += 1
    #         used_names.add(sheet_name.lower())
    #
    #         sheet = workbook.add_worksheet(sheet_name)
    #         sheet.set_column(0, 0, 40)
    #         sheet.set_column(1, 1, 50)
    #         sheet.set_column(2, 2, 50)
    #         sheet.set_column(3, 6, 10)
    #
    #         sheet.write(0, 0, 'User', center_orange_color)
    #         sheet.write(0, 1, 'Menu', center_orange_color)
    #         sheet.write(0, 2, 'Model', center_orange_color)
    #         sheet.write(0, 3, 'Read', center_orange_color)
    #         sheet.write(0, 4, 'Write', center_orange_color)
    #         sheet.write(0, 5, 'Create', center_orange_color)
    #         sheet.write(0, 6, 'Delete', center_orange_color)
    #         sheet.freeze_panes(2, 0)
    #
    #         row = 1
    #         sheet.merge_range(row, 0, row, 6, user.name, left_blue_color)
    #         row += 1
    #
    #         rights_by_name = {}
    #         for access in user.groups_id.mapped('model_access'):
    #             mname = access.model_id.name
    #             if mname not in rights_by_name:
    #                 rights_by_name[mname] = {'read': False, 'write': False, 'create': False, 'unlink': False}
    #             rights_by_name[mname]['read'] |= bool(access.perm_read)
    #             rights_by_name[mname]['write'] |= bool(access.perm_write)
    #             rights_by_name[mname]['create'] |= bool(access.perm_create)
    #             rights_by_name[mname]['unlink'] |= bool(access.perm_unlink)
    #
    #         model_cache = {}
    #
    #         def get_model_record(model_name):
    #             if not model_name:
    #                 return None
    #             if model_name not in model_cache:
    #                 model_cache[model_name] = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
    #             return model_cache[model_name]
    #
    # def action_to_model_name(action):
    #     if not action:
    #         return None
    #     if action._name == 'ir.actions.act_window' and action.res_model:
    #         return action.res_model
    #     if action._name == 'ir.actions.report' and getattr(action, 'model', False):
    #         return action.model
    #     if action._name == 'ir.actions.server' and getattr(action, 'model_id', False):
    #         return action.model_id.model
    #     return None
    #
    #         def write_menu_tree(menu, row, written_models, level=1):
    #             any_written_here = False
    #             for submenu in menu.child_id:
    #                 if submenu.groups_id and not (submenu.groups_id & user.groups_id):
    #                     row, wrote_child = write_menu_tree(submenu, row, written_models, level + 1)
    #                     any_written_here = any_written_here or wrote_child
    #                     continue
    #
    #                 model_name = action_to_model_name(submenu.action)
    #
    #                 wrote_this_row = False
    #                 if model_name and model_name not in written_models:
    #                     perms = rights_by_name.get(model_name,
    #                                                {'read': False, 'write': False, 'create': False, 'unlink': False})
    #                     sheet.write(row, 1, ("   " * level) + submenu.name, left_no_color)
    #                     sheet.write(row, 2, model_name, left_no_color)
    #                     sheet.write(row, 3, "✅" if perms['read'] else "❌", center_no_color)
    #                     sheet.write(row, 4, "✅" if perms['write'] else "❌", center_no_color)
    #                     sheet.write(row, 5, "✅" if perms['create'] else "❌", center_no_color)
    #                     sheet.write(row, 6, "✅" if perms['unlink'] else "❌", center_no_color)
    #                     row += 1
    #                     wrote_this_row = True
    #                     any_written_here = True
    #                     written_models.add(model_name)
    #
    #                 row, wrote_child = write_menu_tree(submenu, row, written_models, level + 1)
    #                 any_written_here = any_written_here or wrote_child or wrote_this_row
    #
    #             return row, any_written_here
    #
    #         main_menus = self.env['ir.ui.menu'].search([('parent_id', '=', False)])
    #         for main_menu in main_menus:
    #             written_models = set()
    #             sheet.merge_range(row, 1, row, 6, main_menu.name, menu_color)
    #             row += 1
    #             row, wrote_any = write_menu_tree(main_menu, row, written_models, level=1)
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #             # If nothing written under this main menu, you can remove the header by overwriting,
    #             # or just leave it as a blank section header. Most people prefer keeping it visible.
    #
    # def generate_model_xlsx_report(self, workbook, data=None, objs=None):
    #     if self.user_ids:
    #         users = self.user_ids
    #     else:
    #         users = self.env['res.users'].search([])
    #
    #     center_orange_color = workbook.add_format(
    #         {'bold': True, 'align': 'center', 'bg_color': '#ffb84d', 'border': 1})
    #     left_blue_color = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#4db8ff', 'border': 1})
    #     left_no_color = workbook.add_format({'align': 'left', 'border': 1})
    #     center_no_color = workbook.add_format({'align': 'center', 'border': 1})
    #
    #     used_names = set()
    #
    #     if users:
    #         for user in users:
    #             base_name = user.name if user.name else f"User-{user.id}"
    #             base_name = base_name[:28]
    #
    #             sheet_name = base_name
    #             counter = 1
    #             while sheet_name.lower() in used_names:
    #                 sheet_name = f"{base_name}_{counter}"
    #                 sheet_name = sheet_name[:31]
    #                 counter += 1
    #
    #             used_names.add(sheet_name.lower())
    #
    #             sheet = workbook.add_worksheet(sheet_name)
    #
    #             sheet.set_column(0, 0, 40)
    #             sheet.set_column(1, 1, 30)
    #             sheet.set_column(2, 2, 70)
    #             sheet.set_column(3, 6, 10)
    #
    #             sheet.write(0, 0, 'User', center_orange_color)
    #             sheet.write(0, 1, 'Module', center_orange_color)
    #             sheet.write(0, 2, 'Model', center_orange_color)
    #             sheet.write(0, 3, 'Read', center_orange_color)
    #             sheet.write(0, 4, 'Write', center_orange_color)
    #             sheet.write(0, 5, 'Create', center_orange_color)
    #             sheet.write(0, 6, 'Delete', center_orange_color)
    #
    #             sheet.freeze_panes(1, 0)
    #             sheet.freeze_panes(2, 0)
    #
    #             row = 1
    #             sheet.merge_range(row, 0, row, 6, user.name, left_blue_color)
    #             row += 1
    #
    #             def action_to_model_name(action):
    #                 if not action:
    #                     return None
    #                 if action._name == 'ir.actions.act_window' and action.res_model:
    #                     return action.res_model
    #                 if action._name == 'ir.actions.report' and getattr(action, 'model', False):
    #                     return action.model
    #                 if action._name == 'ir.actions.server' and getattr(action, 'model_id', False):
    #                     return action.model_id.model
    #                 return None
    #
    #             def write_menu(menu, row, indent=0):
    #                 # Get Model Name from Menu's action
    #                 model_name = None
    #                 model_id = None
    #                 if menu.action:
    #                     model_name = action_to_model_name(menu.action)
    #
    #                 # Default (blank if no model)
    #                 can_read = can_write = can_create = can_unlink = ''
    #
    #                 if model_name:
    #                     model_id = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
    #
    #                     # Default rights when model exists → ✘
    #                     can_read = can_write = can_create = can_unlink = "❌"
    #
    #                     if model_id:
    #                         # Find all access rules for this model
    #                         access_rules = self.env['ir.model.access'].sudo().search([
    #                             ('model_id', '=', model_id.id)
    #                         ])
    #
    #                         # Collect user's group IDs
    #                         user_group_ids = set(self.env['res.groups'].sudo().search([
    #                             ('users', 'in', user.id)
    #                         ]).ids)
    #
    #                         # Check rights based on group access
    #                         for rule in access_rules:
    #                             if rule.group_id and rule.group_id.id not in user_group_ids:
    #                                 continue  # skip rules not assigned to this user
    #                             if rule.perm_read:
    #                                 can_read = "✅"
    #                             if rule.perm_write:
    #                                 can_write = "✅"
    #                             if rule.perm_create:
    #                                 can_create = "✅"
    #                             if rule.perm_unlink:
    #                                 can_unlink = "✅"
    #
    #                 # Write values to sheet
    #                 sheet.write(row, 1, menu.name if not menu.parent_id else '', left_no_color)
    #                 sheet.write(row, 2, model_id.name if model_id else '', left_no_color)
    #                 sheet.write(row, 3, can_read, center_no_color)
    #                 sheet.write(row, 4, can_write, center_no_color)
    #                 sheet.write(row, 5, can_create, center_no_color)
    #                 sheet.write(row, 6, can_unlink, center_no_color)
    #
    #                 row += 1
    #
    #                 # Recurse through children
    #                 children = self.env['ir.ui.menu'].search([('parent_id', '=', menu.id)])
    #                 for child in children:
    #                     row = write_menu(child, row, indent + 1)
    #
    #                 return row
    #
    #             main_menu_ids = self.env['ir.ui.menu'].search([('parent_id', '=', False)])
    #             for main_menu in main_menu_ids:
    #                 row = write_menu(main_menu, row, indent=0)
    #
    #

    def generate_model_xlsx_report(self, workbook, data=None, objs=None):
        if self.user_ids:
            users = self.user_ids
        else:
            users = self.env['res.users'].search([])

        center_orange_color = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#ffb84d', 'border': 1})
        left_blue_color = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#4db8ff', 'border': 1})
        left_brown_color = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#a3a3c2', 'border': 1})
        left_no_color = workbook.add_format({'align': 'left', 'border': 1})
        center_no_color = workbook.add_format({'align': 'center', 'border': 1})

        used_names = set()

        for user in users:
            base_name = user.name if user.name else f"User-{user.id}"
            base_name = base_name[:28]

            sheet_name = base_name
            counter = 1
            while sheet_name.lower() in used_names:
                sheet_name = f"{base_name}_{counter}"
                sheet_name = sheet_name[:31]
                counter += 1
            used_names.add(sheet_name.lower())

            sheet = workbook.add_worksheet(sheet_name)

            sheet.set_column(0, 0, 50)
            sheet.set_column(1, 1, 40)
            sheet.set_column(2, 5, 10)

            sheet.write(0, 0, 'Module', center_orange_color)
            sheet.write(0, 1, 'Model', center_orange_color)
            sheet.write(0, 2, 'Read', center_orange_color)
            sheet.write(0, 3, 'Write', center_orange_color)
            sheet.write(0, 4, 'Create', center_orange_color)
            sheet.write(0, 5, 'Delete', center_orange_color)

            sheet.freeze_panes(2, 0)

            row = 1
            sheet.merge_range(row, 0, row, 5, user.name, left_blue_color)
            row += 1

            printed_models = set()

            def action_to_model_name(action):
                if not action:
                    return None
                if action._name == 'ir.actions.act_window' and action.res_model:
                    return action.res_model
                if action._name == 'ir.actions.report' and getattr(action, 'model', False):
                    return action.model
                if action._name == 'ir.actions.server' and getattr(action, 'model_id', False):
                    return action.model_id.model
                return None

            def process_menu(menu, row):
                """Process a menu and return (row, printed_any)"""
                printed_any = False
                model_name = None
                model_id = None
                if menu.action:
                    model_name = action_to_model_name(menu.action)

                if model_name:
                    model_id = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
                    if model_id and model_id.model not in printed_models:
                        printed_models.add(model_id.model)

                        can_read = can_write = can_create = can_unlink = "❌"

                        if user._is_admin():
                            can_read = can_write = can_create = can_unlink = "✅"
                        else:
                            user_group_ids = set(user.groups_id.ids)
                            access_rules = self.env['ir.model.access'].sudo().search([
                                ('model_id', '=', model_id.id)
                            ])
                            for rule in access_rules:
                                if rule.group_id and rule.group_id.id not in user_group_ids:
                                    continue
                                if rule.perm_read:
                                    can_read = "✅"
                                if rule.perm_write:
                                    can_write = "✅"
                                if rule.perm_create:
                                    can_create = "✅"
                                if rule.perm_unlink:
                                    can_unlink = "✅"

                        if any([can_read == "✅", can_write == "✅", can_create == "✅", can_unlink == "✅"]):
                            sheet.write(row, 1, model_id.name, left_no_color)
                            sheet.write(row, 2, can_read, center_no_color)
                            sheet.write(row, 3, can_write, center_no_color)
                            sheet.write(row, 4, can_create, center_no_color)
                            sheet.write(row, 5, can_unlink, center_no_color)
                            row += 1
                            printed_any = True

                children = self.env['ir.ui.menu'].with_user(user).sudo().search([('parent_id', '=', menu.id)])
                for child in children:
                    row, child_printed = process_menu(child, row)
                    if child_printed:
                        printed_any = True

                return row, printed_any

            main_menus = self.env['ir.ui.menu'].with_user(user).sudo().search([('parent_id', '=', False)])
            for main_menu in main_menus:
                start_row = row
                row, printed = process_menu(main_menu, row)
                if printed:
                    sheet.write(start_row, 0, main_menu.name, left_brown_color)
                    row += 1



