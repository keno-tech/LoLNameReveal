import sys
import requests
from urllib3 import disable_warnings
import json
from time import sleep
import platform
import psutil
import base64
from lcu_driver import Connector
import PySimpleGUI as sg

disable_warnings()

# global variables

api_key = 'RGAPI-592fc2b3-7180-48e3-af7d-ac97d10107d6'

app_port = None
riotclient_app_port = None
auth_token = None
riotclient_auth_token = None
region = None
lcu_name = None   # LeagueClientUx executable name
inChampSelect = False

# functions


def getLCUName():
    '''
    Get LeagueClient executable name depending on platform.
    '''
    global lcu_name
    if platform.system() == 'Windows':
        lcu_name = 'LeagueClientUx.exe'
    elif platform.system() == 'Darwin':
        lcu_name = 'LeagueClientUx'
    elif platform.system() == 'Linux':
        lcu_name = 'LeagueClientUx'


def LCUAvailable():
    '''
    Check whether a client is available.
    '''
    return lcu_name in (p.name() for p in psutil.process_iter())


def getLCUArguments():
    global auth_token, app_port, region, riotclient_auth_token, riotclient_app_port
    '''
    Get region, remoting-auth-token and app-port for LeagueClientUx.
    '''
    if not LCUAvailable():
        sys.exit('No ' + lcu_name + ' found. Login to an account and try again.')

    for p in psutil.process_iter():
        if p.name() == lcu_name:
            args = p.cmdline()

            for a in args:
                if '--region=' in a:
                    region = a.split('--region=', 1)[1].lower()
                if '--remoting-auth-token=' in a:
                    auth_token = a.split('--remoting-auth-token=', 1)[1]
                if '--app-port' in a:
                    app_port = a.split('--app-port=', 1)[1]
                if '--riotclient-auth-token=' in a:
                    riotclient_auth_token = a.split('--riotclient-auth-token=', 1)[1]
                if '--riotclient-app-port=' in a:
                    riotclient_app_port = a.split('--riotclient-app-port=', 1)[1]

connector = Connector()
@connector.ready


async def connect(connection):
    
    global inChampSelect

    getLCUName()

    getLCUArguments()
    
    lcu_api = 'https://127.0.0.1:' + app_port
    riotclient_api = 'https://127.0.0.1:' + riotclient_app_port

    lcu_session_token = base64.b64encode(
        ('riot:' + auth_token).encode('ascii')).decode('ascii')


    riotclient_session_token = base64.b64encode(
        ('riot:' + riotclient_auth_token).encode('ascii')).decode('ascii')
        

    lcu_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + lcu_session_token
    }

    riotclient_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'LeagueOfLegendsClient',
        'Authorization': 'Basic ' + riotclient_session_token
    }

    get_current_summoner = lcu_api + '/lol-summoner/v1/current-summoner'
    r = requests.get(get_current_summoner, headers=lcu_headers, verify=False)
    r = json.loads(r.text)

    # GUI     
    sg.theme('DarkBlue')   

    layout = [[sg.Text(f'Connected: {r["displayName"]}... Welcome to NameReveal')],
                [sg.Button('Reveal Names')],
                [[sg.Multiline(size=(60,15), font='Courier 8', expand_x=True, expand_y=True, write_only=True,
                                    reroute_stdout=True, reroute_stderr=True, echo_stdout_stderr=True, autoscroll=True, auto_refresh=True)]]
                                    ]
    
    window = sg.Window('LolNameReveal', layout, finalize=True)
    
    while True:
        participants = []    
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        elif event == 'Reveal Names':
            try:
                get_champ_select = lcu_api + '/lol-champ-select/v1/session'
                r = requests.get(get_champ_select, headers=lcu_headers, verify=False)
                r = json.loads(r.text)
                if 'errorCode' in r:
                        print('Not in champ select. Press the button again when you are ready.')

                else:
                    print("* Getting Participants *")
                    sleep(1)
                    try:
                        get_lobby = riotclient_api + '/chat/v5/participants/champ-select'
                        r = requests.get(get_lobby, headers=riotclient_headers, verify=False)
                        r = json.loads(r.text)
                        for i in r['participants']:
                            participants.append(i['name'])
                        print("Your team: ")
                        print("-----------------------")
                        
                        for i in participants:
                            print(i)                            
                        
                    except:
                        sys.exit(0)
                        
            except:
                print('*Error Exiting... *')
                sys.exit(0)

   

connector.start()