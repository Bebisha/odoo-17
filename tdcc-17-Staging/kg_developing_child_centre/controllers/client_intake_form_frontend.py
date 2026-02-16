import base64
from odoo import http, tools, _
from odoo.http import request

from odoo.tools import image_data_uri


class client_intake_form(http.Controller):
    def _save_image_nswo(self, file, res_id):
        if not file:
            return False
        Attachment = request.env['ir.attachment'].sudo()
        attachment_id = Attachment.create({
            'name': request.env.user.name,
            'type': 'binary',
            'datas': file.encode(),
            'res_model': 'client.intake.form',
            'res_id': res_id,
        })
        return attachment_id.datas


    @http.route(['/ClientIntakeForm'], type='http', auth="public", website=True, csrf=True)
    def client_intake_form(self, request_id=None, access_token=None, **post):
        backend_ref = post.get('ref')
        backend_submit = post.get('is_submitted')
        backend_name = post.get('first_name')
        c = request.env['client.intake.form'].search([('ref', '=', backend_ref)])

        country_rec = request.env['res.country'].sudo().search([])
        edit_and_create=request.env['ir.config_parameter'].sudo().get_param('client_intake_form_config.edit_and_create')
        ctx = {
            'first_name': c.first_name,
            'last_name': c.last_name,
            'gender': c.gender,
            'date_of_birth': c.date_of_birth,
            'nationality': c.nationality.id,
            'primary_language': c.primary_language,
            'language_spoken': c.language_spoken,
            'school_grade': c.school_grade,
            'contact_person': c.contact_person,
            'mother_name': c.mother_name,
            'phone_number_1': c.phone_number_1,
            'occupation_1': c.occupation_1,
            'mother_mail': c.mother_mail,
            'father_name': c.father_name,
            'phone_number_2': c.phone_number_2,
            'occupation_2': c.occupation_2,
            'father_mail': c.father_mail,
            'parents_related_relative': c.parents_related_relative,
            'center': c.center,
            'describe': c.describe,
            'describe_new': c.describe,
            'child_health': c.child_health,
            'child_health_new': c.child_health,
            'first_name_1': c.first_name_1,
            'last_name_1': c.last_name_1,
            'first_name_2': c.first_name_2,
            'last_name_2': c.last_name_2,
            'terms_condition': c.terms_condition,
            'confirm': c.confirm,
            'country_rec': country_rec,
            'edit_and_create': edit_and_create,
            'signature': c.signature,
            'ref': c.ref,
            'is_submitted': c.is_submitted,
        }

        ctx.update(self._get_documents_front(c))
        ctx.update(self._get_documents_src(c))
        ctx.update(self._get_documents_sign(c))
        return request.render("kg_developing_child_centre.intake_form",ctx)


    def _get_documents_src(self, clientintake):
        res = {}
        for field in ['doc_back']:
            if clientintake[field]:
                if clientintake[field][:7] == b'JVBERi0':
                    img_src = "data:application/pdf;base64,%s" % (clientintake[field].decode())

                else:
                    img_src = image_data_uri(clientintake[field])
                    res[field] = img_src

            else:
                res[field] = False

        return res

    def _get_documents_front(self, clientintake):
        res = {}
        for field in ['doc_front']:
            if clientintake[field]:
                if clientintake[field][:7] == b'JVBERi0':
                    img_src = "data:application/pdf;base64,%s" % (clientintake[field].decode())

                else:
                    img_src = image_data_uri(clientintake[field])
                    res[field] = img_src

            else:
                res[field] = False

        return res

    def _get_documents_sign(self, clientintake):
        res = {}
        for field in ['signature']:
            if clientintake[field]:
                if clientintake[field][:7] == b'JVBERi0':
                    img_src = "data:application/pdf;base64,%s" % (clientintake[field].decode())
                else:
                    img_src = image_data_uri(clientintake[field])
                    res[field] = img_src
            else:
                res[field] = False
        return res

    @http.route(['/ClientIntakeForm/submit'], type='http', csrf=False, auth="public", website=True,
                method=['POST', 'GET'])
    def client_intake_submit_form(self, **post):
        file = post.get('files_1')
        values = {
            'first_name': post.get('first_name'),
            'last_name': post.get('last_name'),
            'gender': post.get('gender'),
            'date_of_birth': post.get('date_of_birth'),
            'nationality': post.get('nationality'),
            'primary_language': post.get('primary_language'),
            'language_spoken': post.get('language_spoken'),
            'school_grade': post.get('school_grade'),
            'contact_person': post.get('contact_person'),
            'mother_name': post.get('mother_name'),
            'phone_number_1': post.get('phone_number_1'),
            'occupation_1': post.get('occupation_1'),
            'mother_mail': post.get('mother_mail'),
            'father_name': post.get('father_name'),
            'phone_number_2': post.get('phone_number_2'),
            'occupation_2': post.get('occupation_2'),
            'father_mail': post.get('father_mail'),
            'parents_related_relative': post.get('parents_related_relative'),
            'center': post.get('center'),
            'describe': post.get('describe'),
            # 'upload_file': post.get('upload_file'),
            'child_health': post.get('child_health'),
            'edit_and_create': post.get('edit_and_create'),
            'terms_condition': post.get('terms_condition'),
            'first_name_1': post.get('first_name_1'),
            'last_name_1': post.get('last_name_1'),
            'first_name_2': post.get('first_name_2'),
            'last_name_2': post.get('last_name_2'),
            'confirm': post.get('confirm'),
            'is_submitted': True,

        }

        partner = request.env['client.intake.form'].sudo().create(values)
        attachment_sign = post.get('signature')
        attachment_sign_1 = self._save_image_nswo(attachment_sign, partner.id)
        # attachment_img = post.get('upload_file')
        # attachment_sign_2 = self._save_upload_file(attachment_img, partner.id)
        #
        partner.sudo().write({
            'signature': attachment_sign_1,
            # 'upload_file': attachment_sign_2,

        }),

        if post.get('doc_front', False):
            Attachments = request.env['ir.attachment']
            name = request.env.user.name
            file = post.get('doc_front')
            attachment_id = Attachments.sudo().create({
                'name': name,
                'type': 'binary',
                'res_model': 'client.intake.form',
                'res_id': partner.id,
                'datas': base64.encodebytes(file.read()),
            })
            partner.write({
                'doc_front': attachment_id.datas
            }),

            if post.get('doc_back', False):
                Attachments = request.env['ir.attachment']
                name = request.env.user.name
                file = post.get('doc_back')
                attachment_id = Attachments.sudo().create({
                    'name': name,
                    'type': 'binary',
                    'res_model': 'client.intake.form',
                    'res_id': partner.id,
                    'datas': base64.encodebytes(file.read()),
                })
                partner.write({
                    'doc_back': attachment_id.datas
                }),



        return request.render("kg_developing_child_centre.client_intake_submit_form", {'ref_id': partner.name})
