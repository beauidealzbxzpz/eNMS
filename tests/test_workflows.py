from time import sleep

from eNMS import db
from eNMS.base.helpers import retrieve
from eNMS.tasks.models import Task

from tests.test_base import check_blueprints


@check_blueprints('/tasks', '/workflows')
def test_netmiko_workflow(user_client):
    task = retrieve(Task, name='task_netmiko_VRF_workflow')
    task.schedule(run_now=True)
    sleep(75)
    db.session.commit()
    print(task.logs)
    assert True
