from odoo import http
from odoo.http import request


class WebsiteForm(http.Controller):

    @http.route(['/Dev_History'], type='http', auth="user", website=True, sitemap=True)
    def dev_history_page_1(self, **post):
        nationality = request.env['res.country'].sudo().search([])
        values = {}
        values.update({'country_rec': nationality})
        return request.render("kg_hms.online_dev_history_form_page_1", values)

    @http.route(['/dev-history-pg1-values'], type='json', csrf=False, auth="user", website=True, sitemap=True)
    def dev_history_page_1_values(self, **post):
        print(post, "POSTTTT")
        today_date = post.get('today_date')
        print(today_date)
        first_name = post.get('first_name')
        dev_last_name = post.get('dev_last_name')
        dev_dob = post.get('dev_dob')
        age = post.get('age')
        nationality = request.env['res.country'].sudo().browse(int(post.get('nationality')))
        gender = post.get('gender')
        dev_language = post.get('dev_language')
        dev_dominant_language = post.get('dev_dominant_language')
        dev_current_school = post.get('dev_current_school')
        dev_school_year_grade = post.get('dev_school_year_grade')
        dev_classroom_teacher = post.get('dev_classroom_teacher')
        dev_mother_first_name = post.get('dev_mother_first_name')
        mother_phone = post.get('mother_phone')
        mother_nationality = request.env['res.country'].sudo().browse(int(post.get('mother_nationality')))
        dev_mother_email = post.get('dev_mother_email')
        dev_father_name = post.get('dev_father_name')
        father_phone = post.get('father_phone')
        father_nationality = request.env['res.country'].sudo().browse(int(post.get('father_nationality')))
        dev_father_email = post.get('dev_father_email')
        dev_home_address = post.get('dev_home_address')
        dev_previous_place = post.get('dev_previous_place')
        dev_siblings = post.get('dev_siblings')
        dev_grand_parents = post.get('dev_grand_parents')
        dev_others = post.get('dev_others')

        list_vals = []
        values = {}
        values.update({'today_date': today_date,
                       'first_name': first_name,
                       'dev_last_name': dev_last_name,
                       'dev_dob': dev_dob,
                       'age': age,
                       'nationality': nationality.id,
                       'gender': gender,
                       'dev_language': dev_language,
                       'dev_dominant_language': dev_dominant_language,
                       'dev_current_school': dev_current_school,
                       'dev_school_year_grade': dev_school_year_grade,
                       'dev_classroom_teacher': dev_classroom_teacher,
                       'dev_mother_first_name': dev_mother_first_name,
                       'mother_phone': mother_phone,
                       'mother_nationality': mother_nationality.id,
                       'dev_mother_email': dev_mother_email,
                       'dev_father_name': dev_father_name,
                       'father_phone': father_phone,
                       'father_nationality': father_nationality.id,
                       'dev_father_email': dev_father_email,
                       'dev_home_address': dev_home_address,
                       'dev_previous_place': dev_previous_place,
                       'dev_siblings': dev_siblings,
                       'dev_grand_parents': dev_grand_parents,
                       'dev_others': dev_others,
                       })
        list_vals.append(values)
        final_val = {}
        final_val.update({'list_val': list_vals})
        # return request.render("kg_hms.online_dev_history_form_2", final_val)
        return final_val
        # return request.render("kg_hms.online_dev_history_form_2", {})

    @http.route(['/Dev_History/page-2'], type='http', csrf=False, auth="user", website=True, sitemap=True)
    def dev_history_page_2(self, **post):
        return request.render("kg_hms.online_dev_history_form_2", {})
