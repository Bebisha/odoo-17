# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import models, api, _
import warnings

from odoo.exceptions import UserError


class DailyAppointmentReport(models.AbstractModel):
    _name = 'report.bista_tdcc_operations.daily_appointment_report'
    _description = 'TDCC Daily Appointment Report'

    def _get_data_from_report(self, data):
        dt1 = data['start_date']
        dt2 = data['end_date']
        utz = self.env.user.tz or 'UTC'
        clinic_id = str(data['clinic_id'])
        physician_id = str(data['physician_id'])
        room_id = str(data['room_id'])
        where = """where
                        (aa.start_date AT TIME ZONE 'UTC'
                        AT TIME ZONE '%s') :: date >= '%s' and
                        (aa.start_date AT TIME ZONE 'UTC'
                        AT TIME ZONE '%s') :: date <= '%s'
                        """ % (utz, dt1, utz, dt2)
        if data['clinic_id']:
            where += " and aa.clinic_id = " + clinic_id
        if data['physician_id']:
            where += " and aa.physician_id = " + physician_id
        elif data['code_id']:
            physician_ids = self.env['res.partner'].search(
                [('physician_code_id', '=', data['code_id'])])
            if len(physician_ids) == 1:
                where += " and aa.physician_id = " + str(physician_ids.id)
            elif len(physician_ids) > 1:
                physicians = str(tuple(physician_ids.ids))
                where += " and aa.physician_id in " + physicians

        if data['room_id']:
            where += " and aa.room_id = " + room_id

        query = """select
                    aa.name ,
                    client.name as client,
                    company.name as clinic,
                    physician.name as physician,
                    room.name as room,
                    to_char((aa.start_date AT TIME ZONE 'UTC'
                    AT TIME ZONE '%s')::date, 'DD/MM/YYYY') as date,
                    to_char((aa.start_date AT TIME ZONE 'UTC'
                    AT TIME ZONE '%s')::time, 'HH24:MI') as time,
                    aa.duration as duration
            from appointment_appointment aa
                    left join res_company company on
                    aa.clinic_id = company.id
                    left join res_partner physician on
                    aa.physician_id = physician.id
                    left join res_partner client on
                    aa.client_id = client.id
                    left join room_room room on
                    aa.room_id = room.id  %s """ % (utz, utz, where)

        self._cr.execute(query)
        res = self._cr.dictfetchall()

        if not res:
            raise UserError(
                _("There is no appointments for selected date \
                        or selected record."))
        return res

    def _get_title(self, data):
        return "Appointments for the Period  %s to %s" % (
            data.get('start_date'),
            data.get('end_date'))

    @api.model
    def _get_report_values(self, docids, data=None):
        app_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_tdcc_operations.action_report_leave_settlement')
        return {
            'doc_ids': self.ids,
            'docs': self,
            'doc_model': app_report.model,
            'get_title': self._get_title(data['form_data']),
            'get_data_from_report': self._get_data_from_report(
                data['form_data']),

        }
