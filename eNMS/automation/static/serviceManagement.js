/*
global
call: false
doc: false
fields: false
services: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Table Actions.
 * @param {values} values - values array.
 * @param {service} service - service.
 */
function tableActions(values, service) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showLogs('${properties.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="compareLogs('${properties.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runJob('${properties.id}')">Run</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="editService('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="editService('${properties.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('service', '${properties.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/services/index.html');
  for (let i = 0; i < services.length; i++) {
    addService('create', services[i]);
  }
  getStates('service');
})();

