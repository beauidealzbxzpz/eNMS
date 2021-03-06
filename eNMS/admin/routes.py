from datetime import datetime
from flask import (
    abort,
    current_app as app,
    redirect,
    render_template,
    request,
    url_for
)
from flask_login import current_user, login_user, logout_user
from git import Repo
from ipaddress import IPv4Network
from json import loads
from ldap3 import Connection, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPBindError
from os import listdir
from requests import get as rest_get
from requests.exceptions import ConnectionError

from eNMS.main import db, ldap_client, tacacs_client, USE_LDAP, USE_TACACS
from eNMS.admin import bp
from eNMS.admin.forms import (
    AddInstance,
    AddUser,
    AdministrationForm,
    LogsForm,
    LoginForm,
    MigrationsForm
)
from eNMS.admin.helpers import migrate_export, migrate_import
from eNMS.base.helpers import (
    fetch_all,
    get,
    get_one,
    post,
    factory,
    fetch,
    serialize
)
from eNMS.base.properties import (
    instance_public_properties,
    user_public_properties
)
from eNMS.inventory.helpers import database_filtering


@get(bp, '/user_management', 'View')
def user_management():
    return dict(
        fields=user_public_properties,
        users=serialize('User'),
        form=AddUser(request.form)
    )


@get(bp, '/administration', 'View')
def administration():
    return dict(
        form=AdministrationForm(request.form),
        parameters=get_one('Parameters').serialized
    )


@get(bp, '/database', 'View')
def database():
    return dict(
        logs_form=LogsForm(request.form),
        migrations_form=MigrationsForm(request.form),
        folders=listdir(app.path / 'migrations')
    )


@get(bp, '/instance_management', 'View')
def instance_management():
    return dict(
        fields=instance_public_properties,
        instances=serialize('Instance'),
        form=AddInstance(request.form)
    )


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name, password = request.form['name'], request.form['password']
        if request.form['authentication_method'] == 'Database':
            user = fetch('User', name=name)
            if password == user.password:
                login_user(user)
                return redirect(url_for('base_blueprint.dashboard'))
            else:
                abort(403)
        elif request.form['authentication_method'] == 'LDAP':
            try:
                with Connection(
                    ldap_client,
                    user=f'{app.config["LDAP_USERDN"]}\\{name}',
                    password=password,
                    auto_bind=True,
                    authentication=NTLM
                ) as connection:
                    connection.search(
                        app.config['LDAP_BASEDN'],
                        f'(&(objectClass=person)(samaccountname={name}))',
                        search_scope=SUBTREE,
                        get_operational_attributes=True,
                        attributes=['cn', 'memberOf', 'mail']
                    )
                    json_response = loads(
                        connection.response_to_json()
                    )['entries'][0]
                    if not json_response:
                        abort(403)
                    user = {
                        'name': name,
                        'password': password,
                        'email': json_response['attributes'].get('mail', '')
                    }
                    if any(
                        app.config['LDAP_ADMIN_GROUP'] in s
                        for s in json_response['attributes']['memberOf']
                    ):
                        user['permissions'] = ['Admin']
                    new_user = factory('User', **user)
                    login_user(new_user)
                    return redirect(url_for('base_blueprint.dashboard'))
            except LDAPBindError:
                abort(403)
        elif request.form['authentication_method'] == 'TACACS':
            if tacacs_client.authenticate(name, password).valid:
                user = factory('User', **{'name': name, 'password': password})
                login_user(user)
                return redirect(url_for('base_blueprint.dashboard'))
            else:
                abort(403)
        else:
            abort(403)
    if not current_user.is_authenticated:
        login_form = LoginForm(request.form)
        authentication_methods = [('Database',) * 2]
        if USE_LDAP:
            authentication_methods.append(('LDAP',) * 2)
        if USE_TACACS:
            authentication_methods.append(('TACACS',) * 2)
        login_form.authentication_method.choices = authentication_methods
        return render_template('login.html', login_form=login_form)
    return redirect(url_for('base_blueprint.dashboard'))


@get(bp, '/logout')
def logout():
    logout_user()
    return redirect(url_for('admin_blueprint.login'))


@post(bp, '/save_parameters', 'Admin')
def save_parameters():
    parameters = get_one('Parameters')
    remote_git = request.form['git_repository_automation']
    if parameters.git_repository_automation != remote_git:
        Repo.clone_from(remote_git, app.path / 'git' / 'automation')
    parameters.update(**request.form)
    database_filtering(fetch('Pool', id=request.form['pool']))
    db.session.commit()
    return True


@post(bp, '/scan_cluster', 'Admin')
def scan_cluster():
    parameters = get_one('Parameters')
    protocol = parameters.cluster_scan_protocol
    for ip_address in IPv4Network(parameters.cluster_scan_subnet):
        try:
            instance = rest_get(
                f'{protocol}://{ip_address}/rest/is_alive',
                timeout=parameters.cluster_scan_timeout
            ).json()
            if app.config['CLUSTER_ID'] != instance.pop('cluster_id'):
                continue
            factory('Instance', **{
                **instance,
                **{'ip_address': str(ip_address)}
            })
        except ConnectionError:
            continue
    db.session.commit()
    return True


@post(bp, '/get_cluster_status', 'View')
def get_cluster_status():
    instances = fetch_all('Instance')
    return {
        attr: [getattr(instance, attr) for instance in instances]
        for attr in ('status', 'cpu_load')
    }


@post(bp, '/clear_logs', 'Admin')
def clear_logs():
    clear_date = datetime.strptime(
        request.form['clear_logs_date'],
        '%d/%m/%Y %H:%M:%S'
    )
    for job in fetch_all('Job'):
        job.logs = {
            date: log for date, log in job.logs.items()
            if datetime.strptime(date, '%Y-%m-%d-%H:%M:%S.%f') > clear_date
        }
    db.session.commit()
    return True


@post(bp, '/reset_status', 'Admin')
def reset_status():
    for job in fetch_all('Job'):
        job.status = 'Idle'
    db.session.commit()
    return True


@post(bp, '/migration_<direction>', 'Admin')
def migration(direction):
    return {
        'import': migrate_import,
        'export': migrate_export
    }[direction](app.path, request.form)
