odoo.define ('kg_developing_child_centre.condition', function (require) {
   'use strict';
    require('web.dom_ready');



   const fileUploader = document.getElementById('doc_front');
    fileUploader.addEventListener('change', (event) => {
      const file = event.target.files[0];
      const size = file.size;
      if (size > 5e+6) {
      alert('The allowed file size is maximum 5MB')
      $('#doc_front').val('')
      }
    });



    const fileUploader_back = document.getElementById('doc_back');
    fileUploader_back.addEventListener('change', (event) => {
      const file = event.target.files[0];
      const size = file.size;
      if (size > 5e+6) {
      alert('The allowed file size is maximum 5MB')
      $('#doc_back').val('')
      }
    });

   $('#date_of_birth').on('change',function(ev) {
      var select_date = new Date($('#date_of_birth').val())
      console.log(select_date)
      var today = new Date();
      if(today < select_date){
          alert("Date cannot should be future date")
          $('#date_of_birth').val('')
      }
    });


    $('#signature_srr').bind('change', function(e) {
      var data = $('#signature_srr').jSignature('getData');
      console.log(e)
      console.log('#signature_srr')

      if (data) {
        data=data.replace('data:image/png;base64,', '')
        }
      if (data) {
        $("#signature_capture").val(data);
            }
    });


    $('#clear').click(function (ev) {
        $('#signature_srr').jSignature("reset");
        $("#signature_capture").val('');
        ev.preventDefault();
    });

     $('#submit_button').click(function() {
        if (!$("input[name='gender']:checked").val()) {
           alert('Fill the gender field!');
            return false;
        }
        if (!$("textarea[name='signature']").val()) {
           alert('Fill the signature field!');
            return false;
        }
        if (!$("input[name='parents_related_relative']:checked").val()) {
           alert('Fill the Are parents related / relatives?');
            return false;
        }
     });

//      const form = document.getElementById('form_id');
//        alert('RESSSSSSSSSSSSSS')
//        form.target.reset();


     $('#first_name').on('change',function(ev) {
    if ($('#first_name').val() && $('#sign').val()!= 'done') {
        $('#signature_srr').jSignature();
        $("#signature_capture").val('');
     $('#sign').val('done')
        ev.preventDefault();
        }
   });

   });

   odoo.define ('kg_developing_child_centre.condition_dev', function (require) {
   'use strict';
    require('web.dom_ready');



    const fileUploader_file = document.getElementById('upload_report');
    fileUploader_file.addEventListener('change', (event) => {
      const file = event.target.files[0];
      const size = file.size;
      if (size > 5e+6) {
      alert('The allowed file size is maximum 5MB')
      $('#upload_report').val('')
      }
    });

   $('#date_of_birth').on('change',function(ev) {
      var select_date = new Date($('#date_of_birth').val())
      console.log(select_date)
      var today = new Date();
      if(today < select_date){
          alert("Date cannot should be future date")
          $('#date_of_birth').val('')
      }
    });

   $('#age').on('change',function(ev) {
     var select_age = $('#age').val()
     if(select_age > 15){
        alert("Age cannot be above 15")
        $('#age').val('')
        }
   });

    $("#dev_form_id")[0].reset();

    $('#signature_srr').bind('change', function(e) {
      var data = $('#signature_srr').jSignature('getData');
      console.log(e)
      console.log('#signature_srr')

      if (data) {
        data=data.replace('data:image/png;base64,', '')
        }
      if (data) {
        $("#signature_capture").val(data);
            }
    });


    $('#clear_dev').click(function (ev) {
        $('#signature_srr').jSignature("reset");
        $("#signature_capture").val('');
        ev.preventDefault();
    });

     $('#submit_button').click(function() {
        if (!$("input[name='gender']:checked").val()) {
           alert('Fill the gender field!');
            return false;
        }
        if (!$("textarea[name='signature']").val()) {
           alert('Fill the signature field!');
            return false;
        }
  });

//        if ($('#main_concern').val()==null || $('#main_concern').val()==''){
//        alert('CHECCCCCCCCCC')
//        return false;
//        }

//       alert($('#res').val())




    $('#first_name').on('change',function(ev) {
    if ($('#first_name').val() && $('#sign').val()!= 'done') {
        $('#signature_srr').jSignature();
        $("#signature_capture").val('');
        $('#sign').val('done')
        ev.preventDefault();
        }
});

    $(document).ready(function() {
    //set initial state.


    $('#other_check').change(function() {
        if(this.checked) {
            $('#collapsediv1').show()
        }
//        $('#other_check').val(this.checked);
    });
});



});

