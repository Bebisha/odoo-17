# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class LinkTrackerClick(models.Model):
    _inherit = 'link.tracker.click'

    kg_email = fields.Char('Email',related='mailing_trace_id.email',store=True)