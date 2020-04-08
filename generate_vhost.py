
import json
import os
import sys


class MissingRequiredField(Exception):
    pass
class FileNotFound(IOError): 
    pass
class InvalidExtension(Exception): 
    pass
class IncorrectNumberOfArguments(Exception): 
    pass

def validate(service): 
    if 'init_script' not in service: 
        raise MissingRequiredField('Missing field init_script')
    
    if not os.path.isfile(service['init_script']):
        raise FileNotFound('File not found '+ service['init_script'])
        
    _, base_ext = get_file_base_name_and_extension(service['init_script'])

    if base_ext != '.py':
        raise InvalidExtension('Only python scripts are allowed')
        
    return True

def get_file_base_name_and_extension(filename):
    base = os.path.basename(filename)
    base_parts = os.path.splitext(base)
    base_name = base_parts[0]
    base_ext = base_parts[1]
    return base_name, base_ext
    
def service_text(service):
    init_script = service['init_script']
    directory = os.path.dirname(init_script)
    base_name, _ = get_file_base_name_and_extension(init_script)
    process_name = 'wsgi_{}'.format(base_name) if 'process_name' not in service else service['process_name']
    api_name = base_name if 'api_name' not in service else service['api_name']
    user = 'apache' if 'user' not in service else service['user']
    group = 'root' if 'group' not in service else service['group']
    threads = '30' if 'threads' not in service else str(service['threads'])
    processes = '3' if 'processes' not in service else str(service['processes'])
    
    
    
    service_text = '''
    WSGIDaemonProcess $PROCESS_NAME$ user=$USER$ group=$GROUP$ threads=$TCOUNT$ processes=$PCOUNT$ inactivity-timeout=0

    WSGIScriptAlias $API_NAME$ $INIT_SCRIPT$

    <Directory $DIRECTORY$>
      WSGIProcessGroup $PROCESS_NAME$
      WSGIApplicationGroup %{GLOBAL}
      Order Deny,Allow
      Allow from all
      Require all granted
    </Directory>
    
    
    '''
    service_text = service_text.replace('$PROCESS_NAME$', process_name)
    service_text = service_text.replace('$API_NAME$', api_name)
    service_text = service_text.replace('$DIRECTORY$', directory)
    service_text = service_text.replace('$USER$', user)
    service_text = service_text.replace('$GROUP$', group)
    service_text = service_text.replace('$TCOUNT$', threads)
    service_text = service_text.replace('$PCOUNT$', processes)
    service_text = service_text.replace('$INIT_SCRIPT$', init_script)
    service_text = service_text.replace('$PROCESS_NAME$', process_name)
    service_text = service_text.replace('$PROCESS_NAME$', process_name)

    return service_text
    

def write_vhost_file(parameters_file_name, vhost_conf_file_name):
    x = '''
<VirtualHost *:80>
  ServerName  huawei1.dolcera.net
  ServerAlias www.huawei1.dolcera.net
  Redirect permanent / https://huawei1.dolcera.net
</VirtualHost>

<VirtualHost *:443>
    ServerName  huawei1.dolcera.net
    ServerAlias www.huawei1.dolcera.net

    $INSERT_HERE$


    ErrorLog  /var/log/httpd/error_log
    CustomLog /var/log/httpd/access_log hauwei

    <Directory /var/www/html>
        AllowOverride All
        Require all granted
    </Directory>

</VirtualHost>
    '''

    with open(parameters_file_name) as f: 
        data = json.load(f)
        insert_text = ''
        for service in data: 
            if validate(service): 
                insert_text += service_text(service)
        x = x.replace('$INSERT_HERE$', insert_text)

    with open(vhost_conf_file_name, 'w') as f: 
        f.write(x)

    return True
        

    
if __name__ == '__main__':
    if len(sys.argv) < 3: 
        raise IncorrectNumberOfArguments('Received '+str(len(sys.argv))+' arguments. Expected 3')
    vhost_conf_file = sys.argv[2]
    parameters_conf_file = sys.argv[1]
    if not os.path.isfile(parameters_conf_file):
        raise FileNotFound('File not found'+ parameters_conf_file)
    write_vhost_file(parameters_conf_file, vhost_conf_file)