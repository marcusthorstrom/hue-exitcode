
import requests, json, time, pickle, argparse
from  os import path

# Authentication function
def authenticate(bridge_ip):
    auth_req = requests.post("http://"+bridge_ip + "/api", json={"devicetype":"hue_exit_code#linux"})
    auth_res = auth_req.json()
    if len(auth_res) == 1:
        auth_res = auth_res[0]
        if 'error' in auth_res:
            if ((auth_res['error'])['type'] == 101):
                print("Press the button")
                input("Press enter after pressing the button. ")
                return authenticate(bridge_ip)
        if 'success' in auth_res:
            return (auth_res['success'])['username']


# Returns the lights to use
def getLights(bridge_ip, userid):
    # Step 3. Get the lights
    lights_req = requests.get("http://"+ bridge_ip + "/api/" + userid + "/lights")
    lights_res = lights_req.json()

    # Step 3.1. Find the Color-lights (for red/green)
    lights_found = {}
    for light_id, light in lights_res.items():
        if('colorgamut' in light['capabilities']['control']):
            lights_found[light_id] = light

    if lights_found == []:
        for light_id, light in lights_res.items():
            # No color lights were found, select another one
            if(light['capabilities']['control'] != {}):
                lights_found[light_id] = light

    # Step 3.2. Select the color lamp(s) to use
    for light_id, light in lights_found.items():
        print(light_id + " : "+ light['name'])

    lights_selected = input("Select ligt(s) to use, enter id or id's followed by ',' ")
    lights_selected = lights_selected.replace(" ", "") # Remove spaces
    lights_selected = lights_selected.split(",")
    return lights_selected

def getBridge():
    bridge_req = requests.get("https://discovery.meethue.com/")
    bridge_res = bridge_req.json()

    if len(bridge_res) > 1:
        print("More than 1 hue bridge found.")
        for num, bridge in enumerate(bridge_res):
            print("%d : %s" % ( num+1, bridge['internalipaddress']) )
        num = input("Which to choose? ")

        return bridge_res[int(num)-1]['internalipaddress']
    elif len(bridge_res) == 1:
        return bridge_res[0]['internalipaddress']
    else:
        print("No bridge found on the network, exiting.")
        return ""

def main():

    parser = argparse.ArgumentParser(description="Flash HUE lights")
    parser.add_argument('--exit_code', metavar="?", type=int, help="The exitcode to display [0/1]")
    parser.add_argument('--setup', dest="setup", help="Used to setup the script", action="store_true")



    args = parser.parse_args()

    if args.exit_code == None and not args.setup:
        print("Unknonw arguments.")
        print("Use either --setup to setup or --exit_code [0/1] to display green/red colors.")
        exit(1)
    
    exit_code = True if args.exit_code == 0 else False

    settings = {}
    settings_changed = False
    if path.exists("settings.pkl"):
        settings = pickle.load(open("settings.pkl", "rb"))
    elif not args.setup:
        print("No settingsfile located, setup need. Run with --setup")
        exit

    if not "ip" in settings:
        # Step 1. Find the IP of the HUE bridge
        bridge_ip = getBridge()
        print("Bridge used: %s" % bridge_ip)
        settings['ip'] = bridge_ip
        settings_changed = True
    bridge_ip = settings['ip']


    if not "userid" in settings:
        # Step 2. See if the user is authenticated
        userid = authenticate(settings['ip'])
        print("UserId: " + userid)
        settings['userid'] = userid
        settings_changed = True
    userid = settings['userid']


    if not "lights" in settings:
        # Step 3. Get the lights
        lights = getLights(settings['ip'], settings['userid'])
        settings['lights'] = lights
        settings_changed = True
    lights = settings['lights']

    if settings_changed:
        # Save settings
        with open("settings.pkl", "wb") as f:
            pickle.dump(settings, f)    

    # Do noting more if we are setting up
    if args.setup:
        exit(0) 


    # Step 4. Flash the lights
    current_state = {}
    for light in lights:
        lights_req = requests.get("http://" + bridge_ip + "/api/" + userid + "/lights/" + light)
        lights_res = lights_req.json()
        # Save the current state:
        state = str(lights_res['state']).replace("True", "true").replace("'", "\"")
        current_state[light] = state

    for light in lights: 
        green = '{ "on": true, "bri": 100, "alert": "none", "hue": 21845, "sat": 255 }'
        red =  '{ "on": true, "bri": 100, "alert": "none", "hue": 65535, "sat": 255 }'
        lights_req = requests.put("http://" + bridge_ip + "/api/" + userid + "/lights/" + light + "/state", data=(green if exit_code else red))
        lights_res = lights_req.json()

    time.sleep(0.3)

    for light, state in current_state.items():
        lights_req = requests.put("http://" + bridge_ip + "/api/" + userid + "/lights/" + light + "/state", data=state)



if __name__== "__main__":
    main()

