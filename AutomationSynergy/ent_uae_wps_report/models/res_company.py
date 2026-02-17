# -*- coding: utf-8 -*-
######################################################################################
#
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anjhana A K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
from odoo import api, fields, models


class ResCompany(models.Model):
    """inherited to add fields in model"""
    _inherit = 'res.company'

    employer_id = fields.Char(string="Employer ID", help="Company Employer ID")

    def write(self, vals):
        """to add company registry and employee value while editing"""
        if 'company_registry' in vals:
            vals['company_registry'] = vals['company_registry'].zfill(
                13) if vals['company_registry'] else False
        if 'employer_id' in vals:
            vals['employer_id'] = vals['employer_id'].zfill(
                13) if vals['employer_id'] else False
        return super().write(vals)

    @api.model
    def create(self, vals):
        """to add company registry and employee value while creating"""
        vals['company_registry'] = vals['company_registry'].zfill(
            13) if vals['company_registry'] else False
        if 'employer_id' in vals:
            vals['employer_id'] = vals['employer_id'].zfill(
                13) if vals['employer_id'] else False
        return super().create(vals)
