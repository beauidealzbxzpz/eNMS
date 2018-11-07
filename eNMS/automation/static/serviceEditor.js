/*
global
addService: false
alertify: false
call: false
fCall: false
nodes: false
propertyTypes: false
servicesClasses: false
showModal: false
workflowBuilder: false;
*/

(function() {
  convertSelect('service-devices', 'service-pools');
  for (let i = 0; i < servicesClasses.length; i++) {
    const cls = servicesClasses[i];
    $('#services').append(`<option value='${cls}'>${cls}</option>`);
  }
})();

/**
 * Edit a service.
 * @param {id} id - Service Id.
 * @param {duplicate} duplicate - Duplicate.
 */
function editService(id, duplicate) {
  if (id) {
    $('#title').text(`${duplicate ? 'Duplicate' : 'Edit'} Service Instance`);
  }
  const url = `/automation/get_service/${id || $('#services').val()}`;
  call(url, function(result) {
    $('#html-form').html(result.form);
    if (result.service) {
      $('#services').hide();
      if (duplicate) {
        result.service.id = result.service.name = '';
      }
      for (const [property, value] of Object.entries(result.service)) {
        const propertyType = propertyTypes[property] || 'str';
        if (propertyType.includes('bool')) {
          $(`#${property}`).prop('checked', value);
        } else if (propertyType.includes('dict')) {
          $(`#${property}`).val(value ? JSON.stringify(value): '{}');
        } else {
          $(`#${property}`).val(value);
        }
      }

      showModal('edit-service');
    }
  });
}

/**
 * Save a service.
 */
function saveService() { // eslint-disable-line no-unused-vars
  const url = `/automation/save_service/${$('#services').val()}`;
  fCall(url, '#edit-service-form', function(result) {
    const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
    if (typeof workflowBuilder === 'undefined') {
      addService(mode, result);
    } else {
      nodes.update({id: result.id, label: result.name});
    }
    const message = `Service '${result.name}'
    ${mode == 'edit' ? 'edited' : 'created'} !`;
    alertify.notify(message, 'success', 5);
    $('#edit-service').modal('hide');
  });
}

$('#services').change(function() {
  editService();
});
