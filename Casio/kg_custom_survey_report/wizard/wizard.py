import re
import string
from base64 import encodebytes
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from odoo import models, fields, api

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ExcelWizard(models.TransientModel):
    _name = "survey.xlsx.report.wizard"

    name = fields.Many2one(comodel_name='survey.survey', string="Survey Name", store=True)
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def get_report_values(self):
        page_ids = self.name.question_and_page_ids
        matrix_qst = len(page_ids.filtered(lambda m: m.question_type == 'matrix').matrix_row_ids)
        choice_qst = len(page_ids.filtered(lambda m: m.question_type in ['simple_choice', 'multiple_choice']).suggested_answer_ids)
        col_count = matrix_qst + choice_qst
        questions = {ques.id: ques.title for ques in self.name.question_ids if not ques.is_page}
        query = """
            SELECT
                uil.email AS email,
                uil.mobile_no AS mobile_no,
                uil.create_date AS create_date,
                uil.answer_type AS answer_type,
                uil.question_id AS question_id,
                uil.value_text_box AS value_text_box,
                uil.value_char_box AS value_char_box,
                uil.value_numerical_box AS value_numerical_box,
                uil.value_date AS value_date,
                uil.value_datetime AS value_datetime,
                uil.suggested_answer_id AS suggested_answer_id,
                jsonb_build_object(
                    'matrix_row_id', uil.matrix_row_id::text,
                    'matrix_col_id', sa.value
                ) AS survey_question_answer,
                uil.id AS survey_question_answer_id
            FROM
                survey_user_input_line uil
            LEFT JOIN
                survey_question_answer sa ON uil.suggested_answer_id = sa.id
            LEFT JOIN
                survey_user_input ui ON uil.user_input_id = ui.id
            WHERE
                uil.survey_id = %s AND ui.state = 'done';
        """

        self.env.cr.execute(query, (self.name.id,))
        results = self.env.cr.dictfetchall()

        ans_vals = []
        for result in results:
            val = {
                'email': result['email'],
                'question': {},
                'mobile_no': result['mobile_no'],
                'date': result['create_date']
            }

            if result['answer_type'] == 'text_box':
                val['question'][result['question_id']] = result['value_text_box']
            elif result['answer_type'] == 'char_box':
                val['question'][result['question_id']] = result['value_char_box']
            elif result['answer_type'] == 'numerical_box':
                val['question'][result['question_id']] = result['value_numerical_box']
            elif result['answer_type'] == 'date':
                val['question'][result['question_id']] = result['value_date']
            elif result['answer_type'] == 'datetime':
                val['question'][result['question_id']] = result['value_datetime']
            else:
                if result['survey_question_answer']:
                    mat_val = {}
                    if result['survey_question_answer']['matrix_row_id']:
                        matrix_val = self.env['survey.question.answer'].browse(int(result['survey_question_answer']['matrix_row_id']))
                        mat_val[matrix_val.value] = result['survey_question_answer']['matrix_col_id']
                        val['question'][result['question_id']] = mat_val
                    else:
                        value = result['survey_question_answer']['matrix_col_id']
                        val['question'][result['question_id']] = value
            ans_vals.append(val)
        single_letter_columns = [chr(i) for i in range(ord('D'), ord('Z') + 1)]
        double_letter_columns = [a + b for a in string.ascii_uppercase for b in string.ascii_uppercase]
        columns = single_letter_columns + double_letter_columns
        combined_data = {}
        for entry in ans_vals:
            email = entry['email']
            question_id, answer = list(entry['question'].items())[0]
            if email not in combined_data:
                combined_data[email] = {
                    'email': email,
                    'question': defaultdict(list),
                    'mobile_no': entry['mobile_no'],
                    'date': entry['date'],
                }
            combined_data[email]['question'][question_id].append(answer)
        for email in combined_data:
            combined_data[email]['question'] = dict(combined_data[email]['question'])

        combined_answers = combined_data


        row = 3
        for line in combined_answers.values():
            new_ans_vals = {}
            row += 1
            col = 0
            for k in questions.keys():
                question = self.env['survey.question'].browse(k)
                if k in line['question'].keys():
                    if question.question_type in ['matrix']:
                        for ln in question.matrix_row_ids:
                            if line['question'][k] != [None]:
                                for item in line['question'][k]:
                                    if item != None:
                                        if ln.value in item:
                                            if not isinstance(item, str):
                                                val = item[ln.value]
                                                first_key = next(iter(item[ln.value].keys()))
                                                value = val[first_key]
                                                new_ans_vals[columns[col] + str(row)] = value

                            col += 1
                    elif question.question_type in ['simple_choice', 'multiple_choice']:
                        for ln in question.suggested_answer_ids:
                            if line['question'][k] != [None]:
                                if line['question'][k][0] != None:
                                    if not isinstance(line['question'][k][0], str):
                                        first_key = next(iter(line['question'][k][0].keys()))
                                        value = line['question'][k][0][first_key]
                                        if ln.value == value:
                                            new_ans_vals[columns[col] + str(row)] = ln.value
                            col += 1
                    else:
                        new_ans_vals[columns[col] + str(row)] = line['question'][k][0]
                        col += 1
                else:
                    if question.question_type in ['matrix']:
                        col += len(question.matrix_row_ids)
                    elif question.question_type in ['simple_choice', 'multiple_choice']:
                        col += len(question.suggested_answer_ids)
                    else:
                        col += 1
            line['question'] = new_ans_vals

        final_answers = list(combined_answers.values())

        data = {
            'name': self.name.title,
            'answers': final_answers,
            'questions': questions,
            'col_count': col_count,
        }
        return data

    def print_xlsx(self):
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xlsx_report(workbook, data=self.get_report_values())
        workbook.close()
        fout = encodebytes(file_io.getvalue())
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Survey Report'
        filename = '%s_%s' % (report_name, datetime_string)
        self.write({'fileout': fout, 'fileout_filename': filename})
        file_io.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        sheet = workbook.add_worksheet('Survey Report')
        col_count = data['col_count']
        loop = (col_count // 26) + 1
        column1 = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
        column = column1[:]
        for i in range(loop):
            prefix = column1[i]
            column.extend([prefix + letter for letter in column1])
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        head1 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '12px'})
        rw_count = 3
        column_count = 3
        sheet.merge_range('A1:H1', data['name'], head)
        sheet.write('A2', 'Time and date answered', head1)
        sheet.set_column('A2:A2', 30)
        sheet.write('B2', 'Email', head1)
        sheet.set_column('B2:B2', 30)
        sheet.write('C2', 'Mobile', head1)
        question_index = {}
        survey_question = self.env['survey.question']
        qus_po = {}

        for index, key in enumerate(data['questions']):
            quess = survey_question.browse(key)
            if quess.question_type in ['matrix']:
                col_span = len(quess.matrix_row_ids)
            elif quess.question_type in ['simple_choice', 'multiple_choice']:
                col_span = len(quess.suggested_answer_ids)
            else:
                col_span = 1
            cell = f"{column[column_count]}2"
            end_column = column_count + col_span - 1
            if column_count == end_column:
                sheet.write(cell, data['questions'][key], head1)
            else:
                sheet.merge_range(1, column_count, 1, end_column, data['questions'][key], head1)
            question_index[index] = key
            row = 3

            if quess.question_type in ['matrix']:
                for line in quess.matrix_row_ids:
                    cell = f"{column[column_count]}{row}"
                    sheet.write(cell, line.value, head1)
                    column_count += 1
            elif quess.question_type in ['simple_choice', 'multiple_choice']:
                for line in quess.suggested_answer_ids:
                    cell = f"{column[column_count]}{row}"
                    qus_po[line.value] = cell
                    sheet.write(cell, line.value, head1)
                    column_count += 1
            else:
                column_count += 1

        rw_count += 1
        date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy'})
        for answer in data['answers']:
            column_count = 0
            cell = f"{column[column_count]}{rw_count}"
            sheet.write(cell, answer['date'], date_style)

            column_count += 1
            cell = f"{column[column_count]}{rw_count}"
            sheet.write(cell, answer['email'])

            column_count += 1
            cell = f"{column[column_count]}{rw_count}"
            sheet.write(cell, answer['mobile_no'])

            for k in answer['question'].keys():
                sheet.write(k, str(answer['question'][k]) if answer['question'][k] else '', '')
            rw_count += 1

