import base64
import csv
import io
from datetime import datetime, date, timedelta

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class ImportLicenseDate(models.TransientModel):
    _name = "import.license.date.wizard"
    _description = 'Importing the License Date'

    data_file = fields.Binary(string="Template File", required=True)


    def update_file(self):
        try:
            csv_data = base64.b64decode(self.data_file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)

            # Read CSV data
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            file_reader.extend(csv_reader)
            keys = ['Emulator License Code', 'License Attributes-Start Date', 'License Attributes-End Date']
            for i in range(1, len(file_reader)):
                field = list(map(str, file_reader[i]))
                if len(field) != 3:
                    raise ValueError(f"Invalid data format on line {i + 1}: {field}")
                values = dict(zip(keys, field))
                license_code = field[0]
                start_date_str = field[1]
                end_date_str = field[2]
                try:
                    start_date = datetime.strptime(start_date_str, '%Y/%m/%d')
                    end_date = datetime.strptime(end_date_str, '%Y/%m/%d')
                except ValueError:
                    raise ValueError(f"Date format error on line {i + 1}: {field}")
                formatted_start_date = start_date.strftime('%Y-%m-%d')
                formatted_end_date = end_date.strftime('%Y-%m-%d')
                emulator_record = self.env['emulator.licence'].search([('name', '=', license_code)], limit=1)

                if emulator_record:
                    emulator_record.sudo().write({
                        'start_date': formatted_start_date,
                        'end_date': formatted_end_date
                    })
                    emulator_record.message_post(
                        body=f"The license dates have been updated. Activation Date: {formatted_start_date}, End Date: {formatted_end_date}",
                    )

                else:
                    ValidationError(f"Record with License Code {license_code} not found.")
            self.send_notifications()


        except Exception as e:
            raise ValidationError(f"File update failed due to: {str(e)}")

    def send_notifications(self):
        notification_date = date.today()
        expiring_licenses = self.env['emulator.licence'].search([
            ('act_date', '<=', notification_date),
            ('state', '=', 'allocated'),('is_new_allocated', '=', False),('is_first_register','=',True),
        ])
        if not expiring_licenses:
            return
        for license in expiring_licenses:
            teacher = license.allocated_teachers
            if teacher:
                # Check for active licenses of the same type
                active_licenses = self.env['emulator.licence'].search([
                    ('emulator_licence_type', '=', license.emulator_licence_type),
                    ('active', '=', True),
                    ('state', '=', 'new'),
                ], limit=1)
                license.state = 'expire'
                license.is_new_allocated = True

                if active_licenses:
                    # Select the first available license
                    first_active_license = active_licenses[0]
                    new_license_code = first_active_license.name
                    # Prepare email content
                    mail_content = (
                        "Dear Customer,<br><br>"
                        "We would like to inform you that your current Emulator License Code has expired. "
                        "Please find below your new License Code, which will be valid for one year from the date of activation:<br><br>"
                        f"Model Name: {license.emulator_licence_type}<br>"
                        f"New License Code: {new_license_code}<br><br>"
                        "Sincerely,<br>"
                        "CASIO Middle East and Africa Team"
                    )

                    subject = 'Emulator License Expiry Notification'

                    # Send email notification
                    email_values = {
                        'subject': subject,
                        'body_html': mail_content,
                        'email_to': teacher.email,
                    }
                    mail_mail = self.env['mail.mail'].sudo().create(email_values)
                    mail_mail.send()

                    license.message_post(body=f"License {license.name} is expiring. Notified teacher {teacher.name}.")

                    # Update teacher with new license
                    teacher.sudo().write({
                        'emulator_licence': new_license_code,
                        'emul_licence_id': first_active_license.id,
                    })
                    teacher.message_post(body=f"Emulator license {new_license_code} has been updated.")

                    # Allocate the license and mark it as allocated
                    first_active_license.sudo().write({
                        # 'is_new_allocated': True,
                        'is_first_register': True,
                        'allocated_teacher': teacher.name,
                        'allocated_teachers': teacher.id,
                        'state': 'allocated',
                        'act_date': date.today(),
                        'allocated_date': date.today(),
                    })
                    first_active_license.message_post(
                        body=f"License {first_active_license.name} allocated to {teacher.name}.")


