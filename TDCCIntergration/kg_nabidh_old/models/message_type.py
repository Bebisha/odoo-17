from odoo import fields, models, api, _
import json
import warnings
import requests

from odoo.exceptions import ValidationError


class KgMessageType(models.Model):
    _name = 'message.type'

    _sql_constraints = [
        ('uniq_message_type', 'unique(message_type)', 'Message Type must be unique.'),
    ]

    message_type = fields.Selection([
        ('A28', 'ADT^A28'),
        ('A03', 'ADT^A03'),
        ('A04', 'ADT^A04'),
        ('A08', 'ADT^A08'),
        ('A11', 'ADT^A11'),
        ('A31', 'ADT^A31'),
        ('A39', 'ADT^A39'),
        ('R01', 'ORU^R01'),
        ('T02', 'MDM^T02'),
        ('T08', 'MDM^T08'),
        ('PC1', 'PPR^PC1'),
        ('O01', 'ORM^O01'),
        ('V04', 'VXU^V04')
    ], string=" Message Type")

    name = fields.Char(string="Type")
    student = fields.Many2many('res.partner', string="Student", compute="_student_id")
    date_message = fields.Datetime("Message time", default=lambda self: fields.Datetime.now())

    link = fields.Char(compute='get_url', string='Nabidhu Url ')
    nabidh_status = fields.Char(string='Nabidh Status')

    @api.depends('message_type')
    def get_url(self):
        for rec in self:
            rec.link = False
            if rec.message_type:
                nabidh_login_url = 'http://103.118.168.194:3002/api/%s' % rec.message_type
                rec.link = nabidh_login_url
            else:
                warnings.warn("Warning: message_type is not set for record with ID: %s" % rec.id)

    def _student_id(self):
        for rec in self:
            rec.student = False
            log = self.env['nabidh.log'].search([('kg_message_type', '=', rec.id)])
            rec.student = log.mapped('student')

    @api.onchange('message_type')
    def onchange_message_type(self):
        if self.message_type:
            self.name = self.message_type

    def action_view_log(self):
        return {
            'name': 'Nabidh Log',
            'res_model': 'nabidh.log',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {},
            'domain': [('kg_message_type', '=', self.id)],
            'target': 'current',

        }

    def action_send(self,message,values,hl7message,student,status):
        if not self.message_type == 'T08':
            log = self.env['nabidh.log'].search([('student','=',student),('kg_message_type','=',self.id)])
            if not log:
                data = {
                    'kg_message_type': self.id,
                    'student': student,
                    'message': values ,
                    'response': message,
                    'hl7message':hl7message,
                    'status':status


                }
                self.env['nabidh.log'].create(data)

            else:
                log.write({'message': values,'response': message,'date_message': fields.Datetime.now(),'hl7message':hl7message,'status':status})
        else:
            log = self.env['nabidh.log'].search([('student', '=', student), ('kg_message_type', '=', self.id)])
            print(hl7message,"hl7message1")
            print(message,"message1")
            print(values,"values1")
            print(status,"status1")
            if not log:
                data = {
                    'kg_message_type': self.id,
                    'student': student,
                    'message': hl7message,
                    'response': message,
                    'hl7message': values,
                    'status': status

                }
                self.env['nabidh.log'].create(data)

            else:
                log.write({'message': values, 'response': message, 'date_message': fields.Datetime.now(),
                           'hl7message': hl7message, 'status': status})


    def _clean_hl7(self, message):
        if isinstance(message, str):
            lines = [line.strip() for line in message.strip().splitlines() if line.strip()]
            return "\n".join(lines)
        else:
            return message

    def action_hl7_url(self, hl7message):
        print(hl7message, "hl7message")
        if isinstance(hl7message, str):
            hl7message_value = self._clean_hl7(hl7message)
        else:
            hl7message_value = hl7message

        headers = {
            "Content-Type": "text/plain",
        }

        login_url = 'https://developerstg.dha.gov.ae/api/nabidhtesting/hl7testutility?app_id=a830a5be&app_key=10ea058592008b19969f3116832962b8'

        response = requests.post(login_url, data=hl7message_value, headers=headers)
        print(response, "response")

        if response.status_code == 200:
            print("Status Code:", response.status_code)
            response_text = response.text.strip()
            print(response_text,"response_text")
            print("Response Text from NABIDH:", repr(response_text))

            if ':' in response_text:
                status_value = response_text.split(':', 1)[1].strip()
                print("Status Only:", status_value)
                self.nabidh_status = status_value
            else:
                print("Unexpected format:", response_text)



