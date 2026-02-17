from odoo import http
from odoo.http import request
from datetime import date


class GShockClubController(http.Controller):

    @http.route('/get_cities', type='json', auth='public', methods=['POST'], csrf=False)
    def get_cities(self, **post):
        country = post.get('country')
        if not country:
            return {'error': 'Missing country parameter'}
        if country == "United Arab Emirates":
            return ['Ajman', 'Abu Dhabi', 'Dubai', 'Fujairah', 'Ras al-Khaimah', 'Sharjah', 'Umm al-Quwain']
        if country == "OMAN":
            return ['Barka', 'RUWI', 'Ruwi', 'SAHAM', 'Salalah', 'Bahla', 'Khasab', 'Muscat', 'Nizwa', 'Seeb', 'Sohar',
                    'Sur']
        if country == "Saudi Arabia":
            return [
                "Abqaiq", "Al Baha", "Al Hada", "Abha", "Jouf", "Al Kharj", "Al Hasa", "Al Khobar",
                "Al Muajjiz", "Qaisumah", "Al Khobar", "Ar Rass", "Asfan", "Al Shuqaiq", "Al 'Uthmaniyah",
                "Waisumah", "Al Bahah", "Badanah", "Bisha", "Buraydah", "Ad Dawadami", "Dhahran", "Dhuba",
                "Ad Dammam", "Nejran", "Wedjh", "Gassim", "Jizan", "Al Hadithah", "Hail", "Hafar al Batin",
                "Hofuf", "Hazm Al Jalamid", "Al Jubayl Industrial City", "Jazan Economic City", "Jeddah",
                "Jeddah Industrial City 2 & 3", "Jubail", "Juaymah Terminal", "Jeddah Yachts Club Port",
                "King Abdullah City", "King Fhad", "Al Khuraibah", "King Khalid", "Khamis Mushayt", "Lith",
                "Al Jawf", "Makkah", "Manailih", "Madinah", "Muhayil", "Majma", "Manfouha", "Najran", "Al Qahmah",
                "Qalsn", "Al Qurainah", "Qatif", "Al Qunfudah", "Qurayyah", "Rabigh", "Harad", "Arar", "Rafha",
                "Ras al Mishab", "Ras al Khafji", "Ras Al-Khair", "Ras Tanura", "Riyadh", "Riyadh Dry Port",
                "Safaniya", "Salwá", "Sayhat", "Shadqam", "Shuaibah", "Sharurah", "Sulayel", "Salboukh"]
        if country == "empty":
            return []
        cities = http.request.env['res.partner'].sudo().get_cities(country)
        return list(cities)

    @http.route(['/join_gshock_club', '/join_gshock_club/<int:agent_id>'], type='http', auth='public', website=True)
    def join_gshock_club(self, agent_id=None):
        agent_name = False
        default_region = False
        set_readonly = False

        if agent_id:
            agent_order_id = http.request.env["agent.order"].sudo().search([('id', '=', agent_id)], limit=1)
            agent_name = agent_order_id.agent_name
        if agent_name not in ['Events', 'Online']:
            default_region = 'middle'
            set_readonly = True

        return request.render('kg_gshock_page.join_gshock_club_template', {
            'agent_id': agent_id,
            'region_id': default_region,
            'set_readonly': set_readonly,
            'agent_name': agent_name,
        })

    @http.route(['/scan_gshock_club', '/scan_gshock_club/<int:agent_id>'], type='http', auth='public', website=True)
    def scan_gshock_club(self, agent_id=None):
        agent_name = ''
        if agent_id:
            agent_order_id = http.request.env["agent.order"].sudo().search([('id', '=', agent_id)], limit=1)
            agent_name = agent_order_id.agent_name
        return request.render('kg_gshock_page.scan_gshock_club_template',
                              {'agent_id': agent_id, 'agent_name': agent_name})

    @http.route('/g-shock/privacy-policy', type='http', auth='public', website=True)
    def gshock_privacy(self, **kw):
        return request.render('kg_gshock_page.privacy_policy_page', {})

    @http.route("/submit_form", type="http", auth="public", website=True, csrf=False)
    def submit_form(self, **kw):
        partner_exist = http.request.env["res.partner"].sudo().search([('email', '=', kw.get("email"))],limit=1)
        state_id = http.request.env["res.country.state"].sudo().search([('name', '=', kw.get("city_id"))],limit=1)
        if state_id:
            country_id = state_id.country_id
        b_year = kw.get("birth_year")
        b_month = kw.get("birth_month")
        b_day = kw.get("birth_day")
        if b_year and b_month and b_day:
            my_date = date(int(b_year), int(b_month), int(b_day))
        else:
            my_date = False
        if kw.get('agent_id'):
            agent_order_id = http.request.env["agent.order"].sudo().search([('id', '=', kw.get('agent_id'))], limit=1)
            agent_order = agent_order_id.agent_name
        else:
            agent_order = False
        vals = {
            "name": kw.get("full_name"),
            "email": kw.get("email"),
            "mobile": "+971"+str(kw.get("phone")),
            "kg_gender": kw.get("gender"),
            "kg_pre_lang": kw.get("preferred_language"),
            "kg_cmnt": kw.get("comments"),
            "kg_area_res": state_id.id,
            "country_id": country_id.id,
            "kg_age_id": my_date,
            "kg_country_res": int(kw.get("nationality")),
            "kg_agent": agent_order,
            "kg_join_club": "gshock"
        }
        if partner_exist:
            partner_exist.sudo().write(vals)
        else:
            http.request.env["res.partner"].sudo().create(vals)
        return request.render('kg_gshock_page.thank_you_page', {'agent_id':kw.get('agent_id')})
