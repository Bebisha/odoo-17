import base64
from odoo import http, tools
from odoo.http import request
from odoo.tools import image_data_uri



class HistoryForm(http.Controller):
    def _save_image_signature(self, file, res_id):
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

    @http.route(['/DevelopmentalHistoryForm'], type='http', auth="public", website=True)
    def patient_form(self, **post):
        backend_ref = post.get('ref')
        c = request.env['developmental.history.form'].search([('ref_dev', '=', backend_ref)])

        country_rec = request.env['res.country'].sudo().search([])
        ctx = {
            'first_name': c.first_name,
            'last_name': c.last_name,
            'date_of_birth': c.date_of_birth,
            'age': c.age,
            'nationality': c.nationality.id,
            'gender': c.gender,
            'language_spoken': c.language_spoken,
            'dominant_language': c.dominant_language,
            'current_school': c.current_school,
            'school_year_grade': c.school_year_grade,
            'classroom_teacher': c.classroom_teacher,
            'mother_name': c.mother_name,
            'phone_number_1': c.phone_number_1,
            'nationality_1': c.nationality_1.id,
            'mother_mail': c.mother_mail,
            'father_name': c.father_name,
            'phone_number_2': c.phone_number_2,
            'nationality_2': c.nationality_2.id,
            'father_mail': c.father_mail,
            'home_address': c.home_address,
            'previous_place': c.previous_place,
            'hearing_test': c.hearing_test,
            'siblings': c.siblings,
            'grandparents': c.grandparents,
            'others': c.others,

            'main_concern': c.main_concern,
            'main_concern_new': c.main_concern,
            'first_notice': c.first_notice,
            'speech_language_therapist': c.speech_language_therapist,
            'occupational_therapist': c.occupational_therapist,
            'physiotherapist': c.physiotherapist,
            'educational_psychologist': c.educational_psychologist,
            'any_other_1': c.any_other_1,
            'other_medical': c.other_medical,
            'parents_related_relative': c.parents_related_relative,
            'child_general_health': c.child_general_health,
            'child_general_health_new': c.child_general_health,
            'physical_difficulties': c.physical_difficulties,
            'ear_infections': c.ear_infections,
            'screened_tested': c.screened_tested,
            'wear_glasses': c.wear_glasses,
            'past_present_medications': c.past_present_medications,
            'past_present_medications_new': c.past_present_medications,
            'allergies': c.allergies,
            'allergies_new': c.allergies,

            'full_term_delivery': c.full_term_delivery,
            'full_term_cesarean': c.full_term_cesarean,

            'pre_term': c.pre_term,
            'during_pregnancy': c.during_pregnancy,
            'problems': c.problems,
            'crawling': c.crawling,
            'sitting': c.sitting,
            'walking': c.walking,
            'babbling': c.babbling,
            'first_words': c.first_words,
            'short_sentences': c.short_sentences,
            'child_like': c.child_like,

            'child_understanding': c.child_understanding,
            'child_understanding_instruction_school': c.child_understanding_instruction_school,
            'child_interact': c.child_interact,
            'child_easy_understand': c.child_easy_understand,
            'speaking_fluently': c.speaking_fluently,
            'family_speech': c.family_speech,

            'carrying_fine_motor': c.carrying_fine_motor,
            'child_dressing': c.child_dressing,
            'bump': c.bump,
            'figuring_activities': c.figuring_activities,

            'school_experience': c.school_experience,
            'enjoy_school': c.enjoy_school,
            'dislike_activities': c.dislike_activities,
            'perspective': c.perspective,
            'raised_concerns': c.raised_concerns,
            'help': c.help,
            'help_support_feel': c.help_support_feel,
            'different_behaviour': c.different_behaviour,
            'child_communicate': c.child_communicate,

            'speech_language_delay': c.speech_language_delay,
            'motor_delay': c.motor_delay,
            'sensory_processing_disorder': c.sensory_processing_disorder,
            'add': c.add,
            'global_development': c.global_development,
            'asd': c.asd,
            'drs_stutter_stammer': c.drs_stutter_stammer,
            'any_other_2': c.any_other_2,
            'assessment_consultation': c.assessment_consultation,
            'assessment_consultation_new': c.assessment_consultation,
            'other_like_information': c.other_like_information,
            # 'check_box_other': c.check_box_other,
            'country_rec': country_rec,
            'ref_dev': c.ref_dev,
            'is_submitted_dev': c.is_submitted_dev,

        }
        ctx.update(self._get_documents_sign(c))

        return request.render("kg_developing_child_centre.history_form", ctx)
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


    @http.route(['/DevelopmentalHistoryForm/submit'], type='http', csrf=False, auth="public", website=True,
                method=['POST', 'GET'])
    def patient_submit_form(self, **post):
        values = {
            'today_date': post.get('today_date'),
            'first_name': post.get('first_name'),
            'last_name': post.get('last_name'),
            'date_of_birth': post.get('date_of_birth'),
            'age': post.get('age'),
            'nationality': post.get('nationality'),
            'nationality_1': post.get('nationality_1'),
            'nationality_2': post.get('nationality_2'),
            # 'male': post.get('male'),
            'gender': post.get('gender'),
            'language_spoken': post.get('language_spoken'),
            'dominant_language': post.get('dominant_language'),
            'current_school': post.get('current_school'),
            'school_year_grade': post.get('school_year_grade'),
            'classroom_teacher': post.get('classroom_teacher'),

            'mother_name': post.get('mother_name'),
            'phone_number_1': post.get('phone_number_1'),
            'phone_number_2': post.get('phone_number_2'),
            'father_name': post.get('father_name'),
            'mother_mail': post.get('mother_mail'),
            'father_mail': post.get('father_mail'),
            'home_address': post.get('home_address'),
            'previous_place': post.get('previous_place'),
            'siblings': post.get('siblings'),
            'grandparents': post.get('grandparents'),
            'others': post.get('others'),

            'main_concern': post.get('main_concern'),
            'first_notice': post.get('first_notice'),
            'speech_language_therapist': post.get('speech_language_therapist'),
            'occupational_therapist': post.get('occupational_therapist'),
            'physiotherapist': post.get('physiotherapist'),
            'educational_psychologist': post.get('educational_psychologist'),
            'any_other_1': post.get('any_other_1'),
            'other_medical': post.get('other_medical'),
            'parents_related_relative': post.get('parents_related_relative'),
            'child_general_health': post.get('child_general_health'),
            'physical_difficulties': post.get('physical_difficulties'),
            'ear_infections': post.get('ear_infections'),
            'screened_tested': post.get('screened_tested'),
            'hearing_test': post.get('hearing_test'),
            'child_communicate': post.get('child_communicate'),
            'wear_glasses': post.get('wear_glasses'),
            'past_present_medications': post.get('past_present_medications'),
            'allergies': post.get('allergies'),

            'full_term_delivery': post.get('full_term_delivery'),
            'full_term_cesarean': post.get('full_term_cesarean'),
            'pre_term': post.get('pre_term'),
            'during_pregnancy': post.get('during_pregnancy'),
            'problems': post.get('problems'),
            'crawling': post.get('crawling'),
            'sitting': post.get('sitting'),
            'walking': post.get('walking'),
            'babbling': post.get('babbling'),
            'first_words': post.get('first_words'),
            'short_sentences': post.get('short_sentences'),
            'child_like': post.get('child_like'),

            'child_understanding': post.get('child_understanding'),
            'child_understanding_instruction_school': post.get('child_understanding_instruction_school'),
            'child_interact': post.get('child_interact'),
            'child_easy_understand': post.get('child_easy_understand'),
            'speaking_fluently': post.get('speaking_fluently'),
            'family_speech': post.get('family_speech'),

            'carrying_fine_motor': post.get('carrying_fine_motor'),
            'child_dressing': post.get('child_dressing'),
            'bump': post.get('bump'),
            'figuring_activities': post.get('figuring_activities'),

            'school_experience': post.get('school_experience'),
            'enjoy_school': post.get('enjoy_school'),
            'dislike_activities': post.get('dislike_activities'),
            'perspective': post.get('perspective'),
            'raised_concerns': post.get('raised_concerns'),
            'help': post.get('help'),
            'help_support_feel': post.get('help_support_feel'),
            'different_behaviour': post.get('different_behaviour'),

            'speech_language_delay': post.get('speech_language_delay'),
            'motor_delay': post.get('motor_delay'),
            'sensory_processing_disorder': post.get('sensory_processing_disorder'),
            'add': post.get('add'),
            'global_development': post.get('global_development'),
            'asd': post.get('asd'),
            'drs_stutter_stammer': post.get('drs_stutter_stammer'),
            'any_other_2': post.get('any_other_2'),
            'assessment_consultation': post.get('assessment_consultation'),
            # 'check_box_other': post.get('check_box_other'),
            'other_like_information': post.get('other_like_information'),
            'is_submitted_dev': True,

        }

        partner = request.env['developmental.history.form'].sudo().create(values)
        attachment_sign = post.get('signature')
        attachment_sign_1 = self._save_image_signature(attachment_sign, partner.id)

        partner.sudo().write({
            'signature': attachment_sign_1,
        }),

        if post.get('upload_report', False):
            Attachments = request.env['ir.attachment']
            name = request.env.user.name
            file = post.get('upload_report')
            attachment_id = Attachments.sudo().create({
                'name': name,
                'type': 'binary',
                'res_model': 'developmental.history.form',
                'res_id': partner.id,

                'datas': base64.encodebytes(file.read()),
            })
            partner.write({
                'upload_report': attachment_id.datas
            }),

        return request.render("kg_developing_child_centre.developmental_submit_form", {'ref_id':partner.name})
