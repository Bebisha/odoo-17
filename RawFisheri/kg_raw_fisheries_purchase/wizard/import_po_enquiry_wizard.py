from tempfile import TemporaryFile

import openpyxl

from odoo import models, fields, _
import base64
from odoo.exceptions import UserError


class ImportPOEnquiryWizard(models.TransientModel):
    _name = "import.po.enquiry.wizard"
    _description = "Import PO Enquiry Wizard"

    name = fields.Char(string="Reference")
    upload_file = fields.Binary(string="Upload Excel File", required=True)
    filename = fields.Char(string="File Name")

    def action_import_file(self):
        return True
        # if self.upload_file:
        #     file_data = base64.b64decode(self.upload_file)
        #     fileobj = TemporaryFile('wb+')
        #     fileobj.write(file_data)
        #     fileobj.seek(0)
        #     workbook = openpyxl.load_workbook(fileobj, data_only=True)
        #
        #     grouped_data = {}
        #
        #     last_date = last_vendor = last_vessel = None
        #     last_ship_to = last_bill_to = last_account_no = None
        #     last_prepared_by = last_page_pic = last_type = None
        #     last_serial_no = last_note = None
        #
        #     for sheet in workbook.worksheets:
        #         for row_cells in sheet.iter_rows(min_row=2):
        #             if all(cell.value is None for cell in row_cells):
        #                 continue
        #
        #             row_num = row_cells[0].row
        #
        #             date = row_cells[1].value or last_date
        #             vendor_name = row_cells[2].value or last_vendor
        #             vessel_name = row_cells[3].value or last_vessel
        #             ship_to_name = row_cells[4].value or last_ship_to
        #             bill_to_name = row_cells[5].value or last_bill_to
        #             account_no = row_cells[6].value or last_account_no
        #             prepared_by_name = row_cells[7].value or last_prepared_by
        #             page_pic = row_cells[8].value or last_page_pic
        #             type_name = row_cells[9].value or last_type
        #             serial_no = row_cells[10].value or last_serial_no
        #             note = row_cells[11].value or last_note
        #
        #             product_code = row_cells[12].value
        #             description = row_cells[13].value
        #             qty = row_cells[14].value
        #             uom_name = row_cells[15].value
        #
        #             if row_cells[1].value: last_date = date
        #             if row_cells[2].value: last_vendor = vendor_name
        #             if row_cells[3].value: last_vessel = vessel_name
        #             if row_cells[4].value: last_ship_to = ship_to_name
        #             if row_cells[5].value: last_bill_to = bill_to_name
        #             if row_cells[6].value: last_account_no = account_no
        #             if row_cells[7].value: last_prepared_by = prepared_by_name
        #             if row_cells[8].value: last_page_pic = page_pic
        #             if row_cells[9].value: last_type = type_name
        #             if row_cells[10].value: last_serial_no = serial_no
        #             if row_cells[11].value: last_note = note
        #
        #             if not vendor_name:
        #                 raise UserError(_("Row %s: Vendor is missing.") % row_num)
        #             vendor = self.env['res.partner'].search([('name', '=', vendor_name)], limit=1)
        #             if not vendor:
        #                 raise UserError(_("Row %s: Vendor '%s' not found.") % (row_num, vendor_name))
        #
        #             if not vessel_name:
        #                 raise UserError(_("Row %s: Vessel is missing.") % row_num)
        #             vessel = self.env['sponsor.sponsor'].search([('name', '=', vessel_name)], limit=1)
        #             if not vessel:
        #                 raise UserError(_("Row %s: Vessel '%s' not found.") % (row_num, vessel_name))
        #
        #             ship_partner = None
        #             if ship_to_name:
        #                 ship_partner = self.env['res.partner'].search([('name', '=', ship_to_name)], limit=1)
        #                 if not ship_partner:
        #                     raise UserError(_("Row %s: Ship To partner '%s' not found.") % (row_num, ship_to_name))
        #
        #             bill_partner = None
        #             if bill_to_name:
        #                 bill_partner = self.env['res.partner'].search([('name', '=', bill_to_name)], limit=1)
        #                 if not bill_partner:
        #                     raise UserError(_("Row %s: Bill To partner '%s' not found.") % (row_num, bill_to_name))
        #
        #             prepared_user = None
        #             # if prepared_by_name:
        #             #     prepared_user = self.env['res.users'].search([('name', '=', prepared_by_name)], limit=1)
        #             #     if not prepared_user:
        #             #         raise UserError(_("Row %s: Prepared By user '%s' not found.") % (row_num, prepared_by_name))
        #
        #             enquiry_type = None
        #             if type_name:
        #                 enquiry_type = self.env['purchase.enquiry.type'].search([('name', '=', type_name)], limit=1)
        #                 if not enquiry_type:
        #                     raise UserError(_("Row %s: Enquiry Type '%s' not found.") % (row_num, type_name))
        #
        #             # if not product_code:
        #             #     raise UserError(_("Row %s: Part No is missing.") % row_num)
        #             # product = self.env['product.product'].search([('default_code', '=', str(product_code))], limit=1)
        #             # if not product:
        #             #     raise UserError(_("Row %s: Product with code '%s' not found.") % (row_num, product_code))
        #
        #             if not uom_name:
        #                 raise UserError(_("Row %s: UOM is missing.") % row_num)
        #             uom = self.env['uom.uom'].search([('name', '=', str(uom_name))], limit=1)
        #             if not uom:
        #                 raise UserError(_("Row %s: UOM '%s' not found.") % (row_num, uom_name))
        #
        #             key = (
        #                 date, vessel.id, vendor.id,
        #                 ship_partner.id if ship_partner else None,
        #                 bill_partner.id if bill_partner else None,
        #                 account_no, prepared_user.id if prepared_user else None,
        #                 page_pic, enquiry_type.id if enquiry_type else None,
        #                 serial_no, note
        #             )
        #             if key not in grouped_data:
        #                 grouped_data[key] = []
        #
        #             grouped_data[key].append({
        #                 'description': description,
        #                 # 'product_id': product.id,
        #                 # 'part_no': product.default_code,
        #                 'qty': qty,
        #                 'uom_id': uom.id,
        #             })
        #
        #     for (date, vessel_id, vendor_id, ship_to_id, bill_to_id, account_no, prepared_by_id, page_pic, type_id,
        #          serial_no, note), lines in grouped_data.items():
        #         po_enq_vals = {
        #             'order_date': date,
        #             'vessel_id': vessel_id,
        #             'vendor_id': vendor_id,
        #             'ship_partner_id': ship_to_id,
        #             'bill_partner_id': bill_to_id,
        #             'acc_no': account_no,
        #             'prepared_user_id': prepared_by_id or self.env.user.id,
        #             'page_pic': page_pic,
        #             'enquiry_type_id': type_id,
        #             'serial_no': serial_no,
        #             'note': note,
        #             'po_enquiry_ids': [],
        #         }
        #
        #         po_enq_line_vals = []
        #         for index, line in enumerate(lines, start=1):
        #             po_enq_line_vals.append((0, 0, {
        #                 'sl_no': index,
        #                 'description': line['description'],
        #                 # 'product_id': line['product_id'],
        #                 'qty': line['qty'],
        #                 # 'part_no': line['part_no'],
        #                 'uom_id': line['uom_id'],
        #             }))
        #
        #         po_enq_vals['po_enquiry_ids'] = po_enq_line_vals
        #         self.env['purchase.enquiry'].create(po_enq_vals)
