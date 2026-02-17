# -*- coding: utf-8 -*-
import ast
from datetime import datetime
from odoo import models


class KgEmiratesId(models.Model):
    _inherit = 'res.partner'

    def fetch_eid_details(self):
        user_id = self.env.user.id
        emirates_id = self.env['kg.emiratesid.scan'].sudo().search([('user_id', '=', user_id)], limit=1,
                                                                   order="id DESC")
        if emirates_id:
            datas = ast.literal_eval(emirates_id.data)
            if datas.get('FullNameEn') and datas.get('FullNameEn').find(','):
                first_name = datas.get('FullNameEn')[:datas.get('FullNameEn').find(',')]
                middle_name = datas.get('FullNameEn')[datas.get('FullNameEn').find(',') + 1:]
                middle_name = middle_name[:middle_name.find(',')]
            self.update({'name': first_name})
            self.update({'first_name': first_name})
            self.update({'middle_name': middle_name})
            self.update({'image_1920': datas.get('Image')})
            self.update({'nationality': datas.get('NationalityEn')})
            bdyparsed_date = datetime.strptime(str(datas.get('DateOfBirth')),
                                               '%d/%m/%Y')  # Correct format for '11/03/2000'
            bdyformatted_date = bdyparsed_date.strftime('%Y-%m-%d')
            self.update({'dob': bdyformatted_date})
            eidparsed_date = datetime.strptime(str(datas.get('ExpiryDate')),
                                               '%d/%m/%Y')  # Correct format for '11/03/2000'
            eidformatted_date = eidparsed_date.strftime('%Y-%m-%d')
            self.update({'emiratesid_expiry': eidformatted_date})
            if datas.get('Gender') == 'M':
                self.update({'gender': 'male'})
            elif datas.get('Gender') == 'F':
                self.update({'gender': 'female'})
            else:
                self.update({'gender': 'other'})
