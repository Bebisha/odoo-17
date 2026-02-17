import time
import json
import datetime
import io
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:

    from odoo.tools.misc import xlsxwriter

except ImportError:

    import xlsxwriter


class ExcelWizard(models.TransientModel):
    _name = "survey.xlsx.report.wizard"

    name = fields.Many2one(comodel_name='survey.survey', string="Survey Name",store=True)


    def print_xlsx(self):

        survey_inputs = self.env['survey.user_input_line'].search([('survey_id', '=', self.name.id)])
        quess = self.env['survey.question'].search([('survey_id', '=', self.name.id)])
        col_count = 3
        matrix_qst = len(self.name.question_and_page_ids.filtered(lambda m: m.question_type == 'matrix').labels_ids_2)
        choice_qst = len(self.name.question_and_page_ids.filtered(
            lambda m: m.question_type in ['simple_choice', 'multiple_choice']).labels_ids)
        normal_qst = len(self.name.question_and_page_ids.filtered(
            lambda m: m.question_type not in ['matrix', 'simple_choice', 'multiple_choice']))
        col_count = matrix_qst + choice_qst + normal_qst
        questions = {}
        for ques in quess:
            if not ques.is_page:
                questions[ques.id] = ques.title
        # print(questions)
        results = []
        for email_id in list(set(survey_inputs.mapped('email'))):
            inputs = self.env['survey.user_input_line'].search([('survey_id', '=', self.name.id),('email','=',email_id)])
            vals = {}
            vals['email'] = email_id
            vals['question'] = {}
            for index, survey in enumerate(inputs):
                if index == 0:
                    email = survey.email
                    mobile_no = survey.mobile_no
                    date = survey.create_date
                    vals['mobile_no'] = mobile_no
                    vals['date'] = date
                if survey.answer_type == 'free_text':
                    vals['question'][survey.question_id.id] = survey.value_free_text
                elif survey.answer_type == 'text':
                    vals['question'][survey.question_id.id] = survey.value_text
                elif survey.answer_type == 'number':
                    vals['question'][survey.question_id.id] = survey.value_number
                elif survey.answer_type == 'date':
                    vals['question'][survey.question_id.id] = survey.value_date
                elif survey.answer_type == 'datetime':
                    vals['question'][survey.question_id.id] = survey.value_datetime
                else:
                    vals['question'][survey.question_id.id] = survey.value_suggested.value
            results.append(vals)
        data = {
            'name' : self.name.title,
            'email' : email,
            'date' : date,
            'answers' : results,
            'questions' : questions,
            'col_count' : col_count,
        }

        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'survey.xlsx.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Survey Excell Report',
                     }
        }

    def get_xlsx_report(self, data, response):
        # def write()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        col_count = data['col_count']
        # print("col_count -->2",col_count)
        loop = (col_count / 26) + 1
        column1 = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        column = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        for i in range(0,round(loop)):
            ltr = column1[i]
            for l in column1:
                column.append(str(ltr)+str(l))
        # print("column--->",column)

        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        head1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px'})
        txt = workbook.add_format({'font_size': '10px'})
        rw_count = 3
        column_count = 3
        sheet.merge_range('A1:H1', data['name'], head)
        sheet.write('A2', 'Time and date answered', head1)
        sheet.set_column('A2:A2',30)
        sheet.write('B2', 'Email', head1)
        sheet.set_column('B2:B2',30)
        sheet.write('C2', 'Mobile', head1)
        question_index = {}
        for index, key in enumerate(data['questions']):
            quess = self.env['survey.question'].search([('id','=',key)])
            if quess.question_type in ['matrix']:
                cell = str(column[column_count]) + str("2")
                sheet.write(cell, data['questions'][key], head1)
                question_index[index] = key
                row = 3
                for line in quess.labels_ids_2:
                    cell = str(column[column_count])+str(row)
                    sheet.write(cell,line.value, head1)
                    column_count +=1
                    question_index[index] = key
                # column_count += 1
            elif quess.question_type in ['simple_choice','multiple_choice']:
                cell = str(column[column_count]) + str("2")
                sheet.write(cell, data['questions'][key], head1)
                question_index[index] = key
                row = 3
                # print("data['questions'][key]--->",data['questions'][key])
                for line in quess.labels_ids:
                    # print("line.value--->", line.value)
                    # print("column count--->",column_count)
                    cell = str(column[column_count])+str(row)
                    sheet.write(cell,line.value, head1)
                    column_count +=1
                    question_index[index] = key
                # column_count += 1
            else:
                cell = str(column[column_count]) + str("2")
                sheet.write(cell, data['questions'][key], head1)
                column_count += 1
                question_index[index] = key

        rw_count += 1
        for answer in data['answers']:
            column_count = 0
            cell = str(column[column_count])+str(rw_count)
            sheet.write(cell,answer['date'])
            column_count = column_count + 1
            cell = str(column[column_count])+str(rw_count)
            sheet.write(cell,answer['email'])
            column_count = column_count + 1
            cell = str(column[column_count])+str(rw_count)
            sheet.write(cell,answer['mobile_no'])
            for i in range(0,len(data['questions']),1):
                quess = self.env['survey.question'].search([('id', '=', question_index[i])])
                if quess.question_type == 'matrix':
                    input = self.env['survey.user_input_line'].search(
                        [('question_id', '=', int(question_index[i])), ('email', '=', answer['email'])])
                    for qs in quess.labels_ids_2:
                        inp = input.filtered(lambda l : l.value_suggested_row.id == qs.id)
                        if len(inp) == 1:
                            column_count = column_count + 1
                            cell = str(column[column_count]) + str(rw_count)
                            sheet.write(cell, inp.value_suggested.value)
                        else:
                            column_count = column_count + 1
                            cell = str(column[column_count]) + str(rw_count)
                            sheet.write(cell,'')
                    column_count + 1
                elif quess.question_type in ['simple_choice','multiple_choice']:
                    input = self.env['survey.user_input_line'].search(
                        [('question_id', '=', int(question_index[i])), ('email', '=', answer['email'])])
                    for qs in quess.labels_ids:
                        inp = input.filtered(lambda l : l.value_suggested.id == qs.id)
                        if len(inp) == 1:
                            column_count = column_count + 1
                            cell = str(column[column_count]) + str(rw_count)
                            sheet.write(cell, inp.value_suggested.value)
                        else:
                            column_count = column_count + 1
                            cell = str(column[column_count]) + str(rw_count)
                            sheet.write(cell,'')
                    column_count + 1
                else:
                    column_count = column_count + 1
                    cell = str(column[column_count])+str(rw_count)
                    sheet.write(cell,answer['question'][question_index[i]])
            rw_count = rw_count + 1
            column_count = column_count + 1

            # print("answer['mobile_no']",answer['question'])

        # sheet.write('D2', 'To:', head1)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
