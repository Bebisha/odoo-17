/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.MyFormWidget = publicWidget.Widget.extend({
    selector: '.gshock-form-section',
    events: {
        'change #region_id': '_onRegionChange',
        'change #country_id': '_onCountryChange',
        'change #privacy_check': '_onPrivacyCheckChange',
        'change #privacy_check2': '_onPrivacyCheckChange2',
        'change #privacy_check3': '_onPrivacyCheckChange3',
        'change #gshockLangSelector': '_onLanguageSwitch',
        'click #submitFormCasio': '_onSubmitClick',
        'click #submitFormCasioArb': '_onSubmitClick',
        'click #submitFormCasioFrench': '_onSubmitClick',
    },

     start: function () {
        this._super.apply(this, arguments);
        const currentPath = window.location.pathname;
        var selectedRegion = $('#region_id').val();
        var selectedAgent = $('#agent_name').val();
        if (selectedAgent && !['Events', 'Online'].includes(selectedAgent)) {
            this._populateCountries(selectedRegion);
            var selectedCountry = $('#country_id').val();
            if (currentPath.includes('/join_gmusic_club/'))  {

                this._populateCitesgm(selectedCountry);
                }
            else {
                this._populateCites(selectedCountry);
            }
        }
       if (currentPath.includes('/join_gmusic_club/'))  {
            this._populateCountriesmgmusiceis(selectedRegion);


        } else {
            this._populateCountries(selectedRegion);
        }
        if (currentPath.includes('/join_gmusic_club'))  {
            this._populateCountriesmgmusiceis(selectedRegion);
        } else {
            this._populateCountries(selectedRegion);
        }
    },

    _populateCountries(region) {
        const $targetSelect = $('#country_id');
        $targetSelect.empty();
        let placeholder = 'Country of Residence';
        $targetSelect.append($('<option>', {
            value: 'False',
            text: placeholder
        }));

        const middleEastCountries = [ "Bahrain", "Cyprus", "Egypt", "Iran", "Iraq", "Israel", "Jordan", "Kuwait", "Lebanon", "Oman", "Palestine", "Qatar", "Saudi Arabia", "Syria", "Turkey", "United Arab Emirates", "Yemen"];
        const africaCountries = [ "Algeria", "Angola", "Benin", "Botswana", "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros", "Democratic Republic of the Congo", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Republic of the Congo", "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe"];

        const countries = region === 'middle' ? middleEastCountries : africaCountries;

        countries.forEach(country => {
            $targetSelect.append($('<option>', {
                value: country,
                text: country
            }));
        });

       if (region === 'middle') {
         $targetSelect.val("United Arab Emirates");
       }
    },
     _populateCountriesmgmusiceis(region) {
        const $targetSelect = $('#country_id');
        $targetSelect.empty();
        let placeholder = 'Country of Residence';
        $targetSelect.append($('<option>', {
            value: 'False',
            text: placeholder
        }));

        const middleEastCountries = ["Oman", "Saudi Arabia",];
        const africaCountries = [ "Algeria", "Angola", "Benin", "Botswana", "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros", "Democratic Republic of the Congo", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Republic of the Congo", "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe"];

        const countries = region === 'middle' ? middleEastCountries : africaCountries;

        countries.forEach(country => {
            $targetSelect.append($('<option>', {
                value: country,
                text: country
            }));
        });
    },
    _populateCitesgm(country_id) {
    const lang = $('#gshockLangSelector').val();
    let cityLabel = 'City';
    if (lang === 'arabic') {
        cityLabel = 'مدينة';
    } else if (lang === 'french') {
        cityLabel = 'Ville';
    }

    $.ajax({
        url: '/get_cities',
        method: 'POST',
        contentType: "application/json",
        data: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {
                country_id: country_id  // Pass country_id, not country name
            },
            id: null
        }),
    }).then((data) => {
        const $targetSelect = $('#city_id');
        $targetSelect.empty();
        $targetSelect.append($('<option>', {
            value: '',
            text: cityLabel
        }));

        data.result.forEach(city => {
            $targetSelect.append($('<option>', {
                value: city,
                text: city
            }));
        });
    }).catch((error) => {
        error.source = "authenticate";
        return Promise.reject(error);
    });
},


    _populateCites(country){
        const lang = $('#gshockLangSelector').val();
        let cityLabel = 'City';
        if (lang === 'arabic') {
            cityLabel = 'مدينة';
        } else if (lang === 'french') {
            cityLabel = 'Ville';
        }
        $.ajax({
            url: '/get_cities',
            method: 'POST',
            contentType: "application/json",
            data: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    country: country
                },
                id: null
            }),
        }).then((data) => {
            const $targetSelect = $('#city_id');
            $targetSelect.empty();
            $targetSelect.append($('<option>', {
                value: '',
                text: cityLabel
            }));

            data.result.forEach(city => {
                $targetSelect.append($('<option>', {
                    value: city,
                    text: city
                }));
            });
        }).catch((error) => {
            error.source = "authenticate";
            return Promise.reject(error);
        });
    },


    _onSubmitClick(ev) {
        var birthYear = $('select[name="birth_year"]').val();
        var birthMonth = document.querySelector('select[name="birth_month"]').value;
        var birthDay = document.querySelector('select[name="birth_day"]').value;
        if (birthYear && birthMonth && birthDay) {
            var birthDate = new Date(birthYear, birthMonth - 1, birthDay);
            var today = new Date();

            var age = today.getFullYear() - birthDate.getFullYear();
            var m = today.getMonth() - birthDate.getMonth();

            if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
                age--;
            }
            if (age < 13) {
                ev.preventDefault();
                alert("You must be at least 13 years old to submit this form in accordance with our age policy !!");
                return false;
            }

        } else {
            alert("Please select Date of Birth !!");
            return false;
        }
    },


    _onRegionChange(ev) {
        const selectedRegion = ev.currentTarget.value;

        const $targetSelect = $('#country_id');
        $targetSelect.empty();

        const lang = $('#gshockLangSelector').val();
        let cityLabel = 'Country of Residence';
        if (lang === 'arabic') {
            cityLabel = 'بلد الإقامة ';
        } else if (lang === 'french') {
            cityLabel = 'Pays de résidence ';
        }

        $targetSelect.append($('<option>', {
            value: 'False',
            text: cityLabel
        }));

        // Middle East countries list
        if (selectedRegion === 'middle') {
            const middleEastCountries = [
                "Bahrain",
                "Cyprus",
                "Egypt",
                "Iran",
                "Iraq",
                "Israel",
                "Jordan",
                "Kuwait",
                "Lebanon",
                "Oman",
                "Palestine",
                "Qatar",
                "Saudi Arabia",
                "Syria",
                "Turkey",
                "United Arab Emirates",
                "Yemen"
            ];
            middleEastCountries.forEach(country => {
                $targetSelect.append($('<option>', {
                    value: country,
                    text: country
                }));
            });
        }
        // Africa countries list
        else {
            const africaCountries = [
                "Algeria",
                "Angola",
                "Benin",
                "Botswana",
                "Cabo Verde",
                "Cameroon",
                "Central African Republic",
                "Chad",
                "Comoros",
                "Democratic Republic of the Congo",
                "Djibouti",
                "Egypt",
                "Equatorial Guinea",
                "Eritrea",
                "Eswatini",
                "Ethiopia",
                "Gabon",
                "Gambia",
                "Ghana",
                "Guinea",
                "Guinea-Bissau",
                "Ivory Coast",
                "Kenya",
                "Lesotho",
                "Liberia",
                "Libya",
                "Madagascar",
                "Malawi",
                "Mali",
                "Mauritania",
                "Mauritius",
                "Morocco",
                "Mozambique",
                "Namibia",
                "Niger",
                "Nigeria",
                "Republic of the Congo",
                "Rwanda",
                "Sao Tome and Principe",
                "Senegal",
                "Seychelles",
                "Sierra Leone",
                "Somalia",
                "South Africa",
                "South Sudan",
                "Sudan",
                "Tanzania",
                "Togo",
                "Tunisia",
                "Uganda",
                "Zambia",
                "Zimbabwe"
            ];
            africaCountries.forEach(country => {
                $targetSelect.append($('<option>', {
                    value: country,
                    text: country
                }));
            });
        }
    },

    _onCountryChange(ev) {
        const _selectedCountry = ev.currentTarget.value;
        console.log(_selectedCountry,'_selectedCountry')
        if (_selectedCountry == "Bahrain") {
    $('#phonecode_id').val('+973').change();
}
else if (_selectedCountry == "Cyprus") {
    $('#phonecode_id').val('+357').change();
}
else if (_selectedCountry == "Egypt") {
    $('#phonecode_id').val('+20').change();
}
else if (_selectedCountry == "Iran") {
    $('#phonecode_id').val('+98').change();
}
else if (_selectedCountry == "Iraq") {
    $('#phonecode_id').val('+964').change();
}
else if (_selectedCountry == "Israel") {
    $('#phonecode_id').val('+972').change();
}
else if (_selectedCountry == "Jordan") {
    $('#phonecode_id').val('+962').change();
}
else if (_selectedCountry == "Kuwait") {
    $('#phonecode_id').val('+965').change();
}
else if (_selectedCountry == "Lebanon") {
    $('#phonecode_id').val('+961').change();
}
else if (_selectedCountry == "Oman") {
    $('#phonecode_id').val('+968').change();
}
else if (_selectedCountry == "Palestine") {
    $('#phonecode_id').val('+970').change();
}
else if (_selectedCountry == "Qatar") {
    $('#phonecode_id').val('+974').change();
}
else if (_selectedCountry == "Saudi Arabia") {
    $('#phonecode_id').val('+966').change();
}
else if (_selectedCountry == "Syria") {
    $('#phonecode_id').val('+963').change();
}
else if (_selectedCountry == "Turkey") {
    $('#phonecode_id').val('+90').change();
}
else if (_selectedCountry == "United Arab Emirates") {
    $('#phonecode_id').val('+971').change();
}
else if (_selectedCountry == "Yemen") {
    $('#phonecode_id').val('+967').change();
}

/* --- Africa --- */
else if (_selectedCountry == "Algeria") {
    $('#phonecode_id').val('+213').change();
}
else if (_selectedCountry == "Angola") {
    $('#phonecode_id').val('+244').change();
}
else if (_selectedCountry == "Benin") {
    $('#phonecode_id').val('+229').change();
}
else if (_selectedCountry == "Botswana") {
    $('#phonecode_id').val('+267').change();
}
else if (_selectedCountry == "Cabo Verde") {
    $('#phonecode_id').val('+238').change();
}
else if (_selectedCountry == "Cameroon") {
    $('#phonecode_id').val('+237').change();
}
else if (_selectedCountry == "Central African Republic") {
    $('#phonecode_id').val('+236').change();
}
else if (_selectedCountry == "Chad") {
    $('#phonecode_id').val('+235').change();
}
else if (_selectedCountry == "Comoros") {
    $('#phonecode_id').val('+269').change();
}
else if (_selectedCountry == "Democratic Republic of the Congo") {
    $('#phonecode_id').val('+243').change();
}
else if (_selectedCountry == "Djibouti") {
    $('#phonecode_id').val('+253').change();
}
else if (_selectedCountry == "Equatorial Guinea") {
    $('#phonecode_id').val('+240').change();
}
else if (_selectedCountry == "Eritrea") {
    $('#phonecode_id').val('+291').change();
}
else if (_selectedCountry == "Eswatini") {
    $('#phonecode_id').val('+268').change();
}
else if (_selectedCountry == "Ethiopia") {
    $('#phonecode_id').val('+251').change();
}
else if (_selectedCountry == "Gabon") {
    $('#phonecode_id').val('+241').change();
}
else if (_selectedCountry == "Gambia") {
    $('#phonecode_id').val('+220').change();
}
else if (_selectedCountry == "Ghana") {
    $('#phonecode_id').val('+233').change();
}
else if (_selectedCountry == "Guinea") {
    $('#phonecode_id').val('+224').change();
}
else if (_selectedCountry == "Guinea-Bissau") {
    $('#phonecode_id').val('+245').change();
}
else if (_selectedCountry == "Ivory Coast") {
    $('#phonecode_id').val('+225').change();
}
else if (_selectedCountry == "Kenya") {
    $('#phonecode_id').val('+254').change();
}
else if (_selectedCountry == "Lesotho") {
    $('#phonecode_id').val('+266').change();
}
else if (_selectedCountry == "Liberia") {
    $('#phonecode_id').val('+231').change();
}
else if (_selectedCountry == "Libya") {
    $('#phonecode_id').val('+218').change();
}
else if (_selectedCountry == "Madagascar") {
    $('#phonecode_id').val('+261').change();
}
else if (_selectedCountry == "Malawi") {
    $('#phonecode_id').val('+265').change();
}
else if (_selectedCountry == "Mali") {
    $('#phonecode_id').val('+223').change();
}
else if (_selectedCountry == "Mauritania") {
    $('#phonecode_id').val('+222').change();
}
else if (_selectedCountry == "Mauritius") {
    $('#phonecode_id').val('+230').change();
}
else if (_selectedCountry == "Morocco") {
    $('#phonecode_id').val('+212').change();
}
else if (_selectedCountry == "Mozambique") {
    $('#phonecode_id').val('+258').change();
}
else if (_selectedCountry == "Namibia") {
    $('#phonecode_id').val('+264').change();
}
else if (_selectedCountry == "Niger") {
    $('#phonecode_id').val('+227').change();
}
else if (_selectedCountry == "Nigeria") {
    $('#phonecode_id').val('+234').change();
}
else if (_selectedCountry == "Republic of the Congo") {
    $('#phonecode_id').val('+242').change();
}
else if (_selectedCountry == "Rwanda") {
    $('#phonecode_id').val('+250').change();
}
else if (_selectedCountry == "Sao Tome and Principe") {
    $('#phonecode_id').val('+239').change();
}
else if (_selectedCountry == "Senegal") {
    $('#phonecode_id').val('+221').change();
}
else if (_selectedCountry == "Seychelles") {
    $('#phonecode_id').val('+248').change();
}
else if (_selectedCountry == "Sierra Leone") {
    $('#phonecode_id').val('+232').change();
}
else if (_selectedCountry == "Somalia") {
    $('#phonecode_id').val('+252').change();
}
else if (_selectedCountry == "South Africa") {
    $('#phonecode_id').val('+27').change();
}
else if (_selectedCountry == "South Sudan") {
    $('#phonecode_id').val('+211').change();
}
else if (_selectedCountry == "Sudan") {
    $('#phonecode_id').val('+249').change();
}
else if (_selectedCountry == "Tanzania") {
    $('#phonecode_id').val('+255').change();
}
else if (_selectedCountry == "Togo") {
    $('#phonecode_id').val('+228').change();
}
else if (_selectedCountry == "Tunisia") {
    $('#phonecode_id').val('+216').change();
}
else if (_selectedCountry == "Uganda") {
    $('#phonecode_id').val('+256').change();
}
else if (_selectedCountry == "Zambia") {
    $('#phonecode_id').val('+260').change();
}
else if (_selectedCountry == "Zimbabwe") {
    $('#phonecode_id').val('+263').change();
}
else {
    $('#phonecode_id').val('empty').change();
}

        const lang = $('#gshockLangSelector').val();
        let cityLabel = 'City';
        if (lang === 'arabic') {
            cityLabel = 'مدينة';
        } else if (lang === 'french') {
            cityLabel = 'Ville';
        }

        $.ajax({
                url: '/get_cities',
                method: 'POST',
                contentType: "application/json",
                data: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        country: _selectedCountry
                    },
                    id: null
                }),
            })
            .then((data) => {
                const $targetSelect = $('#city_id');
                $targetSelect.empty();
                $targetSelect.append($('<option>', {
                    value: 'False',
                    text: cityLabel
                }));

                data.result.forEach(city => {
                    $targetSelect.append($('<option>', {
                        value: city,
                        text: city
                    }));
                });
            })
            .catch((error) => {
                error.source = "authenticate";
                return Promise.reject(error);
            });
    },

    _onPrivacyCheckChange(){
        if($('#privacy_check').is(':checked')){
            $('#submitFormCasio').prop("disabled",false);
        }
        else{
            $('#submitFormCasio').prop("disabled",true);
        }
    },

    _onPrivacyCheckChange2(){
        if($('#privacy_check2').is(':checked')){
            $('#submitFormCasioArb').prop("disabled",false);
        }
        else{
            $('#submitFormCasioArb').prop("disabled",true);
        }
    },

    _onPrivacyCheckChange3(){
        if($('#privacy_check3').is(':checked')){
            $('#submitFormCasioFrench').prop("disabled",false);
        }
        else{
            $('#submitFormCasioFrench').prop("disabled",true);
        }
    },

    _onLanguageSwitch(){
        var lang = $('#gshockLangSelector').val();
        var heading = $('#joinGshockHead');
        var langSelectorSpan = $('#gshockLangSelectorSpan');
        var full_name = $('#full_name');
        var region_id = $('#region_id');
        var agreeCheckBox = $('#agreeCheckBox');
        var country_id = $('#country_id');
        var city_id = $('#city_id');
        var nationality = $('#nationality');
        var email = $('#email');
        var phone = $('#phone');
        var male = $('.gender-option #male');
        var female = $('.gender-option #female');
        var not_spec = $('.gender-option #not_spec');
        var dob_label = $('.dob-label');
        var pref_lang = $('#preferred_language');
        var skill_level = $('#skill_level');
        var pref_lang_eng = $('#preLangEng');
        var pref_lang_arb = $('#preLangArb');
        var skillBeginner = $('#skillBeginner');
        var skillProf = $('#skillProf');
        var comments = $('#comments');
        var submitFormCasio = $('#submitFormCasio');

        var privacyWrapperArb = $('.privacy-wrapper-arb');
        var privacyWrapperEng = $('.privacy-wrapper-eng');
        var privacyWrapperFrench = $('.privacy-wrapper-french');

        var phoneFieldWrapperEng = $('.phone-field-wrapper-eng');
        var phoneFieldWrapperArb = $('.phone-field-wrapper-arb');
        let currentPath = window.location.pathname;
        if(currentPath.includes('/join_gshock_club/')){

            if (lang == 'arabic') {
                    heading.html('انضم إلى نادي G-SHOCK');
                    langSelectorSpan.html('اختار اللغة:');
                    agreeCheckBox.html('من خلال تحديد هذا المربع فإنك توافق على
                                            <a href="/g-shock/privacy-policy" target="_blank">سياسة الخصوصية  </a>');
                    full_name.attr('placeholder','الاسم الكامل');
                    email.attr('placeholder','عنوان البريد الإلكتروني');
                    phone.attr('placeholder','هاتف');
                    comments.attr('placeholder','تعليقات');
                    region_id.html('<option value="">اختر المنطقة </option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    city_id.html('<option value="">مدينة </option>')
                    male.html('ذكر')
                    female.html('أنثى')
                    not_spec.html('يفضل عدم ذكرها')
                    dob_label.html('اختر تاريخ الميلاد')
                    pref_lang.html('اللغة المفضلة للتواصل')
                    pref_lang_eng.html('إنجليزي')
                    pref_lang_arb.html(' عربي')
                    if (skill_level){
                        skill_level.html('مستوى المهارة')
                        skillBeginner.html('مبتدئ')
                        skillProf.html('احترافي')
                    }
                    $('select[name=nationality] > option:first-child').text('بلد الإقامة  ');
                    $('select[name=city_id] > option:first-child').text('مدينة');
                    $('select[name=country_id] > option:first-child').text('جنسية ');
                    $('select[name=birth_year] > option:first-child').text('سنة');
                    $('select[name=birth_month] > option:first-child').text('شهر');
                    $('select[name=birth_day] > option:first-child').text('يوم');


                    heading.css({'direction':'rtl'});
                    langSelectorSpan.css({'direction':'rtl'});
                    full_name.css({'direction':'rtl'});
                    agreeCheckBox.css({'direction':'rtl'});
                    email.css({'direction':'rtl'});
                    phone.css({'direction':'rtl'});
                    male.css({'direction':'rtl'});
                    female.css({'direction':'rtl'});
                    not_spec.css({'direction':'rtl'});
                    dob_label.css({'direction':'rtl'});
                    pref_lang.css({'direction':'rtl'});
                    pref_lang_eng.css({'direction':'rtl'});
                    pref_lang_arb.css({'direction':'rtl'});
                    if (skill_level){
                        skill_level.css({'direction':'rtl'});
                        skillBeginner.css({'direction':'rtl'});
                        skillProf.css({'direction':'rtl'});
                    }
                    comments.css({'direction':'rtl'});
                    region_id.css({'direction':'rtl'});
                    country_id.css({'direction':'rtl'});
                    city_id.css({'direction':'rtl'});
                    nationality.css({'direction':'rtl'});

                    privacyWrapperEng.addClass('d-none');
                    privacyWrapperArb.removeClass('d-none');
                    privacyWrapperFrench.addClass('d-none');

                    phoneFieldWrapperEng.addClass('d-none');
                    phoneFieldWrapperArb.removeClass('d-none');

                    phone.css({'border-left': 'unset'})
                    phone.css({'border-right': '2px solid black !important'})
            } else if (lang == 'french'){
                    heading.html('Rejoignez le club G-SHOCK');
                    langSelectorSpan.html('Select Language:');
                    agreeCheckBox.html('En cochant cette case, vous acceptez notre
                                            <a href="/g-shock/privacy-policy" target="_blank"> Politique de confidentialité.</a>');
                    full_name.attr('placeholder','Nom et prénom');
                    email.attr('placeholder','Adresse e-mail');
                    phone.attr('placeholder','téléphone');
                    comments.attr('placeholder','commentaires');
                    region_id.html('<option value="">Choisissez une région </option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    $('select[name=nationality] > option:first-child').text('Nationalité');
                    $('select[name=city_id] > option:first-child').text('Ville');
                    $('select[name=country_id] > option:first-child').text('Pays de résidence');
                    male.html('Mâle')
                    female.html('Femelle')
                    not_spec.html('Je préfère ne pas mentionner')
                    dob_label.html('Sélectionnez la date de naissance')
                    pref_lang.html('Langue préférée pour la communication')
                    pref_lang_eng.html('Anglais')
                    pref_lang_arb.html('arabe')
                    if (skill_level){
                        skill_level.html('Niveau de compétence')
                        skillBeginner.html('Débutant')
                        skillProf.html('Professionnel')
                    }
                    $('select[name=birth_year] > option:first-child').text('Année');
                    $('select[name=birth_month] > option:first-child').text('Mois');
                    $('select[name=birth_day] > option:first-child').text('Jour');

                    heading.css({'direction':'ltr'});
                    langSelectorSpan.css({'direction':'ltr'});
                    full_name.css({'direction':'ltr'});
                    agreeCheckBox.css({'direction':'ltr'});
                    email.css({'direction':'ltr'});
                    phone.css({'direction':'ltr'});
                    male.css({'direction':'ltr'});
                    female.css({'direction':'ltr'});
                    not_spec.css({'direction':'ltr'});
                    dob_label.css({'direction':'ltr'});
                    pref_lang.css({'direction':'ltr'});
                    pref_lang_eng.css({'direction':'ltr'});
                    pref_lang_arb.css({'direction':'ltr'});
                    if (skill_level){
                        skill_level.css({'direction':'ltr'});
                        skillBeginner.css({'direction':'ltr'});
                        skillProf.css({'direction':'ltr'});
                    }
                    comments.css({'direction':'ltr'});
                    region_id.css({'direction':'ltr'});
                    country_id.css({'direction':'ltr'});
                    city_id.css({'direction':'ltr'});
                    nationality.css({'direction':'ltr'});

                    privacyWrapperArb.addClass('d-none');
                    privacyWrapperEng.addClass('d-none');
                    privacyWrapperFrench.removeClass('d-none');

                    phoneFieldWrapperArb.addClass('d-none');
                    phoneFieldWrapperEng.removeClass('d-none');

                    phone.css({'border-right': 'unset'})
                    phone.css({'border-left': '2px solid black !important'})
            } else {
                    heading.html('Join the G-SHOCK Club');
                    langSelectorSpan.html('Select Language: ');
                    agreeCheckBox.html('By checking this box you agree to our
                                            <a href="/g-shock/privacy-policy" target="_blank"> Privacy Policy</a>');
                    full_name.attr('placeholder','Full Name');
                    email.attr('placeholder','Email Address');
                    phone.attr('placeholder','Phone');
                    comments.attr('placeholder','Comments');
                    region_id.html('<option value="">Select Region</option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    $('select[name=nationality] > option:first-child').text('Nationality');
                    $('select[name=city_id] > option:first-child').text('City');
                    $('select[name=country_id] > option:first-child').text('Country of Residence');
                    male.html('Male')
                    female.html('Female')
                    not_spec.html('Prefer not to mention')
                    dob_label.html('Select Date of Birth')
                    pref_lang.html('Preferred language for communication')
                    pref_lang_eng.html('English')
                    pref_lang_arb.html('Arabic')
                    if (skill_level){
                        skill_level.html('Skill Level')
                        skillBeginner.html('Beginner')
                        skillProf.html('Professional')
                    }
                    $('select[name=birth_year] > option:first-child').text('Year');
                    $('select[name=birth_month] > option:first-child').text('Month');
                    $('select[name=birth_day] > option:first-child').text('Day');

                    heading.css({'direction':'ltr'});
                    langSelectorSpan.css({'direction':'ltr'});
                    full_name.css({'direction':'ltr'});
                    agreeCheckBox.css({'direction':'ltr'});
                    email.css({'direction':'ltr'});
                    phone.css({'direction':'ltr'});
                    male.css({'direction':'ltr'});
                    female.css({'direction':'ltr'});
                    not_spec.css({'direction':'ltr'});
                    dob_label.css({'direction':'ltr'});
                    pref_lang.css({'direction':'ltr'});
                    pref_lang_eng.css({'direction':'ltr'});
                    pref_lang_arb.css({'direction':'ltr'});
                    if (skill_level){
                        skill_level.css({'direction':'ltr'});
                        skillBeginner.css({'direction':'ltr'});
                        skillProf.css({'direction':'ltr'});
                    }
                    comments.css({'direction':'ltr'});
                    region_id.css({'direction':'ltr'});
                    country_id.css({'direction':'ltr'});
                    city_id.css({'direction':'ltr'});
                    nationality.css({'direction':'ltr'});

                    privacyWrapperArb.addClass('d-none');
                    privacyWrapperEng.removeClass('d-none');
                    privacyWrapperFrench.addClass('d-none');

                    phoneFieldWrapperArb.addClass('d-none');
                    phoneFieldWrapperEng.removeClass('d-none');

                    phone.css({'border-right': 'unset'})
                    phone.css({'border-left': '2px solid black !important'})
            }
           }
        else if(currentPath.includes('/join_gshock_club')){
            if (lang == 'arabic') {
                    heading.html('انضم إلى نادي G-SHOCK');
                    langSelectorSpan.html('اختار اللغة:');
                    agreeCheckBox.html('من خلال تحديد هذا المربع فإنك توافق على
                                            <a href="/g-shock/privacy-policy" target="_blank">سياسة الخصوصية  </a>');
                    full_name.attr('placeholder','الاسم الكامل');
                    email.attr('placeholder','عنوان البريد الإلكتروني');
                    phone.attr('placeholder','هاتف');
                    comments.attr('placeholder','تعليقات');
                    region_id.html('<option value="">اختر المنطقة </option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    city_id.html('<option value="">مدينة </option>')
                    male.html('ذكر')
                    female.html('أنثى')
                    not_spec.html('يفضل عدم ذكرها')
                    dob_label.html('اختر تاريخ الميلاد')
                    pref_lang.html('اللغة المفضلة للتواصل')
                    pref_lang_eng.html('إنجليزي')
                    pref_lang_arb.html(' عربي')
                    if (skill_level){
                        skill_level.html('مستوى المهارة')
                        skillBeginner.html('مبتدئ')
                        skillProf.html('احترافي')
                    }
                    $('select[name=nationality] > option:first-child').text('بلد الإقامة  ');
                    $('select[name=city_id] > option:first-child').text('مدينة');
                    $('select[name=country_id] > option:first-child').text('جنسية ');
                    $('select[name=birth_year] > option:first-child').text('سنة');
                    $('select[name=birth_month] > option:first-child').text('شهر');
                    $('select[name=birth_day] > option:first-child').text('يوم');


                    heading.css({'direction':'rtl'});
                    langSelectorSpan.css({'direction':'rtl'});
                    full_name.css({'direction':'rtl'});
                    agreeCheckBox.css({'direction':'rtl'});
                    email.css({'direction':'rtl'});
                    phone.css({'direction':'rtl'});
                    male.css({'direction':'rtl'});
                    female.css({'direction':'rtl'});
                    not_spec.css({'direction':'rtl'});
                    dob_label.css({'direction':'rtl'});
                    pref_lang.css({'direction':'rtl'});
                    pref_lang_eng.css({'direction':'rtl'});
                    pref_lang_arb.css({'direction':'rtl'});
                    if (skill_level){
                        skill_level.css({'direction':'rtl'});
                        skillBeginner.css({'direction':'rtl'});
                        skillProf.css({'direction':'rtl'});
                    }
                    comments.css({'direction':'rtl'});
                    region_id.css({'direction':'rtl'});
                    country_id.css({'direction':'rtl'});
                    city_id.css({'direction':'rtl'});
                    nationality.css({'direction':'rtl'});

                    privacyWrapperEng.addClass('d-none');
                    privacyWrapperArb.removeClass('d-none');
                    privacyWrapperFrench.addClass('d-none');

                    phoneFieldWrapperEng.addClass('d-none');
                    phoneFieldWrapperArb.removeClass('d-none');

                    phone.css({'border-left': 'unset'})
                    phone.css({'border-right': '2px solid black !important'})
            } else if (lang == 'french'){
                    heading.html('Rejoignez le club G-SHOCK');
                    langSelectorSpan.html('Select Language:');
                    agreeCheckBox.html('En cochant cette case, vous acceptez notre
                                            <a href="/g-shock/privacy-policy" target="_blank"> Politique de confidentialité.</a>');
                    full_name.attr('placeholder','Nom et prénom');
                    email.attr('placeholder','Adresse e-mail');
                    phone.attr('placeholder','téléphone');
                    comments.attr('placeholder','commentaires');
                    region_id.html('<option value="">Choisissez une région </option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    $('select[name=nationality] > option:first-child').text('Nationalité');
                    $('select[name=city_id] > option:first-child').text('Ville');
                    $('select[name=country_id] > option:first-child').text('Pays de résidence');
                    male.html('Mâle')
                    female.html('Femelle')
                    not_spec.html('Je préfère ne pas mentionner')
                    dob_label.html('Sélectionnez la date de naissance')
                    pref_lang.html('Langue préférée pour la communication')
                    pref_lang_eng.html('Anglais')
                    pref_lang_arb.html('arabe')
                    if (skill_level){
                        skill_level.html('Niveau de compétence')
                        skillBeginner.html('Débutant')
                        skillProf.html('Professionnel')
                    }
                    $('select[name=birth_year] > option:first-child').text('Année');
                    $('select[name=birth_month] > option:first-child').text('Mois');
                    $('select[name=birth_day] > option:first-child').text('Jour');

                    heading.css({'direction':'ltr'});
                    langSelectorSpan.css({'direction':'ltr'});
                    full_name.css({'direction':'ltr'});
                    agreeCheckBox.css({'direction':'ltr'});
                    email.css({'direction':'ltr'});
                    phone.css({'direction':'ltr'});
                    male.css({'direction':'ltr'});
                    female.css({'direction':'ltr'});
                    not_spec.css({'direction':'ltr'});
                    dob_label.css({'direction':'ltr'});
                    pref_lang.css({'direction':'ltr'});
                    pref_lang_eng.css({'direction':'ltr'});
                    pref_lang_arb.css({'direction':'ltr'});
                    if (skill_level){
                        skill_level.css({'direction':'ltr'});
                        skillBeginner.css({'direction':'ltr'});
                        skillProf.css({'direction':'ltr'});
                    }
                    comments.css({'direction':'ltr'});
                    region_id.css({'direction':'ltr'});
                    country_id.css({'direction':'ltr'});
                    city_id.css({'direction':'ltr'});
                    nationality.css({'direction':'ltr'});

                    privacyWrapperArb.addClass('d-none');
                    privacyWrapperEng.addClass('d-none');
                    privacyWrapperFrench.removeClass('d-none');

                    phoneFieldWrapperArb.addClass('d-none');
                    phoneFieldWrapperEng.removeClass('d-none');

                    phone.css({'border-right': 'unset'})
                    phone.css({'border-left': '2px solid black !important'})
            } else {
                    heading.html('Join the G-SHOCK Club');
                    langSelectorSpan.html('Select Language: ');
                    agreeCheckBox.html('By checking this box you agree to our
                                            <a href="/g-shock/privacy-policy" target="_blank"> Privacy Policy</a>');
                    full_name.attr('placeholder','Full Name');
                    email.attr('placeholder','Email Address');
                    phone.attr('placeholder','Phone');
                    comments.attr('placeholder','Comments');
                    region_id.html('<option value="">Select Region</option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    $('select[name=nationality] > option:first-child').text('Nationality');
                    $('select[name=city_id] > option:first-child').text('City');
                    $('select[name=country_id] > option:first-child').text('Country of Residence');
                    male.html('Male')
                    female.html('Female')
                    not_spec.html('Prefer not to mention')
                    dob_label.html('Select Date of Birth')
                    pref_lang.html('Preferred language for communication')
                    pref_lang_eng.html('English')
                    pref_lang_arb.html('Arabic')
                    $('select[name=birth_year] > option:first-child').text('Year');
                    $('select[name=birth_month] > option:first-child').text('Month');
                    $('select[name=birth_day] > option:first-child').text('Day');

                    heading.css({'direction':'ltr'});
                    langSelectorSpan.css({'direction':'ltr'});
                    full_name.css({'direction':'ltr'});
                    agreeCheckBox.css({'direction':'ltr'});
                    email.css({'direction':'ltr'});
                    phone.css({'direction':'ltr'});
                    male.css({'direction':'ltr'});
                    female.css({'direction':'ltr'});
                    not_spec.css({'direction':'ltr'});
                    dob_label.css({'direction':'ltr'});
                    pref_lang.css({'direction':'ltr'});
                    pref_lang_eng.css({'direction':'ltr'});
                    pref_lang_arb.css({'direction':'ltr'});
                    if (skill_level){
                        skill_level.css({'direction':'ltr'});
                        skillBeginner.css({'direction':'ltr'});
                        skillProf.css({'direction':'ltr'});
                    }
                    comments.css({'direction':'ltr'});
                    region_id.css({'direction':'ltr'});
                    country_id.css({'direction':'ltr'});
                    city_id.css({'direction':'ltr'});
                    nationality.css({'direction':'ltr'});

                    privacyWrapperArb.addClass('d-none');
                    privacyWrapperEng.removeClass('d-none');
                    privacyWrapperFrench.addClass('d-none');

                    phoneFieldWrapperArb.addClass('d-none');
                    phoneFieldWrapperEng.removeClass('d-none');

                    phone.css({'border-right': 'unset'})
                    phone.css({'border-left': '2px solid black !important'})
            }
        }
        else if(currentPath.includes('/join_gmusic_club')){
         if (lang == 'arabic') {
                    heading.html('انضم إلى نادي G-MUSIC');
                    langSelectorSpan.html('اختار اللغة:');
                    agreeCheckBox.html('من خلال تحديد هذا المربع فإنك توافق على
                                            <a href="/g-music/privacy-policy" target="_blank">سياسة الخصوصية  </a>');
                    full_name.attr('placeholder','الاسم الكامل');
                    email.attr('placeholder','عنوان البريد الإلكتروني');
                    phone.attr('placeholder','هاتف');
                    comments.attr('placeholder','تعليقات');
                    region_id.html('<option value="">اختر المنطقة </option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    city_id.html('<option value="">مدينة </option>')
                    male.html('ذكر')
                    female.html('أنثى')
                    not_spec.html('يفضل عدم ذكرها')
                    dob_label.html('اختر تاريخ الميلاد')
                    pref_lang.html('اللغة المفضلة للتواصل')
                    pref_lang_eng.html('إنجليزي')
                    pref_lang_arb.html(' عربي')
                    if (skill_level){
                        skill_level.html('مستوى المهارة')
                        skillBeginner.html('مبتدئ')
                        skillProf.html('احترافي')
                    }
                    $('select[name=nationality] > option:first-child').text('بلد الإقامة  ');
                    $('select[name=city_id] > option:first-child').text('مدينة');
                    $('select[name=country_id] > option:first-child').text('جنسية ');
                    $('select[name=birth_year] > option:first-child').text('سنة');
                    $('select[name=birth_month] > option:first-child').text('شهر');
                    $('select[name=birth_day] > option:first-child').text('يوم');


                    heading.css({'direction':'rtl'});
                    langSelectorSpan.css({'direction':'rtl'});
                    full_name.css({'direction':'rtl'});
                    agreeCheckBox.css({'direction':'rtl'});
                    email.css({'direction':'rtl'});
                    phone.css({'direction':'rtl'});
                    male.css({'direction':'rtl'});
                    female.css({'direction':'rtl'});
                    not_spec.css({'direction':'rtl'});
                    dob_label.css({'direction':'rtl'});
                    pref_lang.css({'direction':'rtl'});
                    pref_lang_eng.css({'direction':'rtl'});
                    pref_lang_arb.css({'direction':'rtl'});
                    if (skill_level){
                        skill_level.css({'direction':'rtl'});
                        skillBeginner.css({'direction':'rtl'});
                        skillProf.css({'direction':'rtl'});
                    }
                    comments.css({'direction':'rtl'});
                    region_id.css({'direction':'rtl'});
                    country_id.css({'direction':'rtl'});
                    city_id.css({'direction':'rtl'});
                    nationality.css({'direction':'rtl'});

                    privacyWrapperEng.addClass('d-none');
                    privacyWrapperArb.removeClass('d-none');
                    privacyWrapperFrench.addClass('d-none');

                    phoneFieldWrapperEng.addClass('d-none');
                    phoneFieldWrapperArb.removeClass('d-none');

                    phone.css({'border-left': 'unset'})
                    phone.css({'border-right': '2px solid black !important'})
            } else if (lang == 'french'){
                    heading.html('Rejoignez le club G-MUSIC');
                    langSelectorSpan.html('Select Language:');
                    agreeCheckBox.html('En cochant cette case, vous acceptez notre
                                            <a href="/g-music/privacy-policy" target="_blank"> Politique de confidentialité.</a>');
                    full_name.attr('placeholder','Nom et prénom');
                    email.attr('placeholder','Adresse e-mail');
                    phone.attr('placeholder','téléphone');
                    comments.attr('placeholder','commentaires');
                    region_id.html('<option value="">Choisissez une région </option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    $('select[name=nationality] > option:first-child').text('Nationalité');
                    $('select[name=city_id] > option:first-child').text('Ville');
                    $('select[name=country_id] > option:first-child').text('Pays de résidence');
                    male.html('Mâle')
                    female.html('Femelle')
                    not_spec.html('Je préfère ne pas mentionner')
                    dob_label.html('Sélectionnez la date de naissance')
                    pref_lang.html('Langue préférée pour la communication')
                    pref_lang_eng.html('Anglais')
                    pref_lang_arb.html('arabe')
                    if (skill_level){
                        skill_level.html('Niveau de compétence')
                        skillBeginner.html('Débutant')
                        skillProf.html('Professionnel')
                    }
                    $('select[name=birth_year] > option:first-child').text('Année');
                    $('select[name=birth_month] > option:first-child').text('Mois');
                    $('select[name=birth_day] > option:first-child').text('Jour');

                    heading.css({'direction':'ltr'});
                    langSelectorSpan.css({'direction':'ltr'});
                    full_name.css({'direction':'ltr'});
                    agreeCheckBox.css({'direction':'ltr'});
                    email.css({'direction':'ltr'});
                    phone.css({'direction':'ltr'});
                    male.css({'direction':'ltr'});
                    female.css({'direction':'ltr'});
                    not_spec.css({'direction':'ltr'});
                    dob_label.css({'direction':'ltr'});
                    pref_lang.css({'direction':'ltr'});
                    pref_lang_eng.css({'direction':'ltr'});
                    pref_lang_arb.css({'direction':'ltr'});
                    if (skill_level){
                        skill_level.css({'direction':'ltr'});
                        skillBeginner.css({'direction':'ltr'});
                        skillProf.css({'direction':'ltr'});
                    }
                    comments.css({'direction':'ltr'});
                    region_id.css({'direction':'ltr'});
                    country_id.css({'direction':'ltr'});
                    city_id.css({'direction':'ltr'});
                    nationality.css({'direction':'ltr'});

                    privacyWrapperArb.addClass('d-none');
                    privacyWrapperEng.addClass('d-none');
                    privacyWrapperFrench.removeClass('d-none');

                    phoneFieldWrapperArb.addClass('d-none');
                    phoneFieldWrapperEng.removeClass('d-none');

                    phone.css({'border-right': 'unset'})
                    phone.css({'border-left': '2px solid black !important'})
            } else {
                    heading.html('Join the G-MUSIC Club');
                    langSelectorSpan.html('Select Language: ');
                    agreeCheckBox.html('By checking this box you agree to our
                                            <a href="/g-music/privacy-policy" target="_blank"> Privacy Policy</a>');
                    full_name.attr('placeholder','Full Name');
                    email.attr('placeholder','Email Address');
                    phone.attr('placeholder','Phone');
                    comments.attr('placeholder','Comments');
                    region_id.html('<option value="">Select Region</option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    $('select[name=nationality] > option:first-child').text('Nationality');
                    $('select[name=city_id] > option:first-child').text('City');
                    $('select[name=country_id] > option:first-child').text('Country of Residence');
                    male.html('Male')
                    female.html('Female')
                    not_spec.html('Prefer not to mention')
                    dob_label.html('Select Date of Birth')
                    pref_lang.html('Preferred language for communication')
                    pref_lang_eng.html('English')
                    pref_lang_arb.html('Arabic')
                    $('select[name=birth_year] > option:first-child').text('Year');
                    $('select[name=birth_month] > option:first-child').text('Month');
                    $('select[name=birth_day] > option:first-child').text('Day');

                    heading.css({'direction':'ltr'});
                    langSelectorSpan.css({'direction':'ltr'});
                    full_name.css({'direction':'ltr'});
                    agreeCheckBox.css({'direction':'ltr'});
                    email.css({'direction':'ltr'});
                    phone.css({'direction':'ltr'});
                    male.css({'direction':'ltr'});
                    female.css({'direction':'ltr'});
                    not_spec.css({'direction':'ltr'});
                    dob_label.css({'direction':'ltr'});
                    pref_lang.css({'direction':'ltr'});
                    pref_lang_eng.css({'direction':'ltr'});
                    pref_lang_arb.css({'direction':'ltr'});
                    if (skill_level){
                        skill_level.css({'direction':'ltr'});
                        skillBeginner.css({'direction':'ltr'});
                        skillProf.css({'direction':'ltr'});
                    }
                    comments.css({'direction':'ltr'});
                    region_id.css({'direction':'ltr'});
                    country_id.css({'direction':'ltr'});
                    city_id.css({'direction':'ltr'});
                    nationality.css({'direction':'ltr'});

                    privacyWrapperArb.addClass('d-none');
                    privacyWrapperEng.removeClass('d-none');
                    privacyWrapperFrench.addClass('d-none');

                    phoneFieldWrapperArb.addClass('d-none');
                    phoneFieldWrapperEng.removeClass('d-none');

                    phone.css({'border-right': 'unset'})
                    phone.css({'border-left': '2px solid black !important'})
            }
            }

        else if(currentPath.includes('/join_gmusic_club')){
         if (lang == 'arabic') {
                    heading.html('انضم إلى نادي G-MUSIC');
                    langSelectorSpan.html('اختار اللغة:');
                    agreeCheckBox.html('من خلال تحديد هذا المربع فإنك توافق على
                                            <a href="/g-music/privacy-policy" target="_blank">سياسة الخصوصية  </a>');
                    full_name.attr('placeholder','الاسم الكامل');
                    email.attr('placeholder','عنوان البريد الإلكتروني');
                    phone.attr('placeholder','هاتف');
                    comments.attr('placeholder','تعليقات');
                    region_id.html('<option value="">اختر المنطقة </option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    city_id.html('<option value="">مدينة </option>')
                    male.html('ذكر')
                    female.html('أنثى')
                    not_spec.html('يفضل عدم ذكرها')
                    dob_label.html('اختر تاريخ الميلاد')
                    pref_lang.html('اللغة المفضلة للتواصل')
                    pref_lang_eng.html('إنجليزي')
                    pref_lang_arb.html(' عربي')
                    if (skill_level){
                        skill_level.html('مستوى المهارة')
                        skillBeginner.html('مبتدئ')
                        skillProf.html('احترافي')
                    }
                    $('select[name=nationality] > option:first-child').text('بلد الإقامة  ');
                    $('select[name=city_id] > option:first-child').text('مدينة');
                    $('select[name=country_id] > option:first-child').text('جنسية ');
                    $('select[name=birth_year] > option:first-child').text('سنة');
                    $('select[name=birth_month] > option:first-child').text('شهر');
                    $('select[name=birth_day] > option:first-child').text('يوم');


                    heading.css({'direction':'rtl'});
                    langSelectorSpan.css({'direction':'rtl'});
                    full_name.css({'direction':'rtl'});
                    agreeCheckBox.css({'direction':'rtl'});
                    email.css({'direction':'rtl'});
                    phone.css({'direction':'rtl'});
                    male.css({'direction':'rtl'});
                    female.css({'direction':'rtl'});
                    not_spec.css({'direction':'rtl'});
                    dob_label.css({'direction':'rtl'});
                    pref_lang.css({'direction':'rtl'});
                    pref_lang_eng.css({'direction':'rtl'});
                    pref_lang_arb.css({'direction':'rtl'});
                    if (skill_level){
                        skill_level.css({'direction':'rtl'});
                        skillBeginner.css({'direction':'rtl'});
                        skillProf.css({'direction':'rtl'});
                    }
                    comments.css({'direction':'rtl'});
                    region_id.css({'direction':'rtl'});
                    country_id.css({'direction':'rtl'});
                    city_id.css({'direction':'rtl'});
                    nationality.css({'direction':'rtl'});

                    privacyWrapperEng.addClass('d-none');
                    privacyWrapperArb.removeClass('d-none');
                    privacyWrapperFrench.addClass('d-none');

                    phoneFieldWrapperEng.addClass('d-none');
                    phoneFieldWrapperArb.removeClass('d-none');

                    phone.css({'border-left': 'unset'})
                    phone.css({'border-right': '2px solid black !important'})
            } else if (lang == 'french'){
                    heading.html('Rejoignez le club G-MUSIC');
                    langSelectorSpan.html('Select Language:');
                    agreeCheckBox.html('En cochant cette case, vous acceptez notre
                                            <a href="/g-music/privacy-policy" target="_blank"> Politique de confidentialité.</a>');
                    full_name.attr('placeholder','Nom et prénom');
                    email.attr('placeholder','Adresse e-mail');
                    phone.attr('placeholder','téléphone');
                    comments.attr('placeholder','commentaires');
                    region_id.html('<option value="">Choisissez une région </option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    $('select[name=nationality] > option:first-child').text('Nationalité');
                    $('select[name=city_id] > option:first-child').text('Ville');
                    $('select[name=country_id] > option:first-child').text('Pays de résidence');
                    male.html('Mâle')
                    female.html('Femelle')
                    not_spec.html('Je préfère ne pas mentionner')
                    dob_label.html('Sélectionnez la date de naissance')
                    pref_lang.html('Langue préférée pour la communication')
                    pref_lang_eng.html('Anglais')
                    pref_lang_arb.html('arabe')
                    if (skill_level){
                        skill_level.html('Niveau de compétence')
                        skillBeginner.html('Débutant')
                        skillProf.html('Professionnel')
                    }
                    $('select[name=birth_year] > option:first-child').text('Année');
                    $('select[name=birth_month] > option:first-child').text('Mois');
                    $('select[name=birth_day] > option:first-child').text('Jour');

                    heading.css({'direction':'ltr'});
                    langSelectorSpan.css({'direction':'ltr'});
                    full_name.css({'direction':'ltr'});
                    agreeCheckBox.css({'direction':'ltr'});
                    email.css({'direction':'ltr'});
                    phone.css({'direction':'ltr'});
                    male.css({'direction':'ltr'});
                    female.css({'direction':'ltr'});
                    not_spec.css({'direction':'ltr'});
                    dob_label.css({'direction':'ltr'});
                    pref_lang.css({'direction':'ltr'});
                    pref_lang_eng.css({'direction':'ltr'});
                    pref_lang_arb.css({'direction':'ltr'});
                    if (skill_level){
                        skill_level.css({'direction':'ltr'});
                        skillBeginner.css({'direction':'ltr'});
                        skillProf.css({'direction':'ltr'});
                    }
                    comments.css({'direction':'ltr'});
                    region_id.css({'direction':'ltr'});
                    country_id.css({'direction':'ltr'});
                    city_id.css({'direction':'ltr'});
                    nationality.css({'direction':'ltr'});

                    privacyWrapperArb.addClass('d-none');
                    privacyWrapperEng.addClass('d-none');
                    privacyWrapperFrench.removeClass('d-none');

                    phoneFieldWrapperArb.addClass('d-none');
                    phoneFieldWrapperEng.removeClass('d-none');

                    phone.css({'border-right': 'unset'})
                    phone.css({'border-left': '2px solid black !important'})
            } else {
                    heading.html('Join the G-MUSIC Club');
                    langSelectorSpan.html('Select Language: ');
                    agreeCheckBox.html('By checking this box you agree to our
                                            <a href="/g-music/privacy-policy" target="_blank"> Privacy Policy</a>');
                    full_name.attr('placeholder','Full Name');
                    email.attr('placeholder','Email Address');
                    phone.attr('placeholder','Phone');
                    comments.attr('placeholder','Comments');
                    region_id.html('<option value="">Select Region</option>
                                        <option value="middle">Middle East</option>
                                        <option value="africa">Africa</option>')
                    $('select[name=nationality] > option:first-child').text('Nationality');
                    $('select[name=city_id] > option:first-child').text('City');
                    $('select[name=country_id] > option:first-child').text('Country of Residence');
                    male.html('Male')
                    female.html('Female')
                    not_spec.html('Prefer not to mention')
                    dob_label.html('Select Date of Birth')
                    pref_lang.html('Preferred language for communication')
                    pref_lang_eng.html('English')
                    pref_lang_arb.html('Arabic')
                    $('select[name=birth_year] > option:first-child').text('Year');
                    $('select[name=birth_month] > option:first-child').text('Month');
                    $('select[name=birth_day] > option:first-child').text('Day');

                    heading.css({'direction':'ltr'});
                    langSelectorSpan.css({'direction':'ltr'});
                    full_name.css({'direction':'ltr'});
                    agreeCheckBox.css({'direction':'ltr'});
                    email.css({'direction':'ltr'});
                    male.css({'direction':'ltr'});
                    female.css({'direction':'ltr'});
                    not_spec.css({'direction':'ltr'});
                    dob_label.css({'direction':'ltr'});
                    pref_lang.css({'direction':'ltr'});
                    pref_lang_eng.css({'direction':'ltr'});
                    pref_lang_arb.css({'direction':'ltr'});
                    if (skill_level){
                        skill_level.css({'direction':'ltr'});
                        skillBeginner.css({'direction':'ltr'});
                        skillProf.css({'direction':'ltr'});
                    }
                    comments.css({'direction':'ltr'});
                    region_id.css({'direction':'ltr'});
                    country_id.css({'direction':'ltr'});
                    city_id.css({'direction':'ltr'});
                    nationality.css({'direction':'ltr'});

                    privacyWrapperArb.addClass('d-none');
                    privacyWrapperEng.removeClass('d-none');
                    privacyWrapperFrench.addClass('d-none');

                    phoneFieldWrapperArb.addClass('d-none');
                    phoneFieldWrapperEng.removeClass('d-none');

                    phone.css({'border-right': 'unset'})
                    phone.css({'border-left': '2px solid black !important'})
            }

        }

        else {}

        var selectedAgent = $('#agent_name').val();
        if (selectedAgent && !['Events', 'Online'].includes(selectedAgent)) {
             $('#region_id').val('middle');
             var selectedCountry = $('#country_id').val();
             this._populateCites(selectedCountry);
        }
    }

});