import tkinter
import requests
import pandas as pd
from tkinter import ttk
from tkinter import messagebox
import time

class AutocompleteCombobox(ttk.Combobox):

    def set_completion_list(self, completion_list):
        """Use our completion list as our drop down selection menu, arrows move through menu."""
        self._completion_list = sorted(completion_list, key=str.lower) # Work with a sorted list
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = self._completion_list  # Setup our popup menu

    def autocomplete(self, delta=0):
        """autocomplete the Combobox, delta may be 0/1/-1 to cycle through possible hits"""
        if delta: # need to delete selection otherwise we would fix the current position
            self.delete(self.position, tkinter.END)
        else: # set position to end so selection starts where textentry ended
            self.position = len(self.get())
        # collect hits
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()): # Match case insensitively
                _hits.append(element)
        # if we have a new hit list, keep this in mind
        if _hits != self._hits:
            self._hit_index = 0
            self._hits=_hits
        # only allow cycling if we are in a known hit list
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        # now finally perform the auto completion
        if self._hits:
            self.delete(0,tkinter.END)
            self.insert(0,self._hits[self._hit_index])
            self.select_range(self.position,tkinter.END)

    def handle_keyrelease(self, event):
        """event handler for the keyrelease event on this widget"""
        if event.keysym == "BackSpace":
            self.delete(self.index(tkinter.INSERT), tkinter.END)
            self.position = self.index(tkinter.END)
        if event.keysym == "Left":
            if self.position < self.index(tkinter.END): # delete the selection
                self.delete(self.position, tkinter.END)
            else:
                self.position = self.position-1 # delete one character
                self.delete(self.position, tkinter.END)
        if event.keysym == "Right":
            self.position = self.index(tkinter.END) # go to end (no selection)
        if len(event.keysym) == 1:
            self.autocomplete()
        # No need for up/down, we'll jump to the popup
        # list at the position of the autocompletion

class SignUpAll():
    """KeyFob Assignment utility"""
    def __init__(self, master):

        self.doorflowStatus = False

        self.top = master
        self.users = None
        self.doorflow_auth = requests.auth.HTTPBasicAuth('3zxv-BQUSiSyER5UxrM4','x')
        self.nexudus_auth = ()

        self.createStartScreen()
        
    def createStartScreen(self):

        self.startScreen = tkinter.Toplevel(self.top)

        titleLabel = tkinter.Label(self.startScreen, text='Create A New Fob')
        titleLabel.grid(row=1, column=1)

        startButton = tkinter.Button(self.startScreen, text='Start', command=self.createInitilizeScreen)
        startButton.grid(row=2, column=1)

    def createInitilizeScreen(self):

        self.startScreen.destroy()
        self.initScreen = tkinter.Toplevel(self.top)

        nameLabel = tkinter.Label(self.initScreen, text='Select Your Name')
        nameLabel.grid(row=1, column=1, columnspan=2)

        self.namesList = self.getNamesFromNexudus()
        self.selectedName = tkinter.StringVar(self.top)
        
        nameDropDown = AutocompleteCombobox(self.initScreen, textvariable=self.selectedName)
        nameDropDown.set_completion_list(self.namesList)
        nameDropDown.grid(row=2, column=1, columnspan=2)

        selectButton = tkinter.Button(self.initScreen, text='Start', command=self.startAssignment)
        selectButton.grid(row=3, column=1)

        refreshButton = tkinter.Button(self.initScreen, text='Refresh', command = self.getNamesFromNexudus)
        refreshButton.grid(row=3, column=2)

    def getNamesFromNexudus(self):
        """Pull the list of users from nexudus and return a list of the names"""
        
        url = "https://spaces.nexudus.com/api/spaces/coworkers?size=500"
        all_users = requests.get(url, auth=self.nexudus_auth)
        all_users = pd.DataFrame(all_users.json()['Records'])
        names = all_users.FullName.to_list()

        self.users = all_users

        return names

    def startAssignment(self):
        """Wait for a signal from DoorFlow and assign the fob number to the appropriate user"""
        name = self.selectedName.get()

        tkinter.messagebox.showinfo(self.initScreen, message='Hit Card Now, you will hear a beep after your badge is read')

        lastevent = self.getDoorFlowEvents()

        if lastevent == False:
            print('You didnt scan a card, try again')
            self.initScreen.destroy()
            self.createInitilizeScreen()
            return

        status = self.searchNexudusCards(lastevent)

        # Check if card is already in use by someone else
        if status == False:
            print('That card is already in use, try again')
            self.initScreen.destroy()
            self.createInitilizeScreen()
            return

        # TODO: Check time stamp and make sure it makes sense

        # TODO: If everything is ok, take the user name and the number and push to Nexudus
        status = self.pushUpdate(lastevent,name)
        if status == False:
            self.initScreen.destroy()
            self.createInitilizeScreen()
            return
        else:
            self.initScreen.destroy()
            self.createStartScreen()

    def getDoorFlowEvents(self):
        url = "https://admin.doorflow.com/api/2/events?n=20"
        all_events = requests.get(url, auth=self.doorflow_auth)
        
        return all_events.json()[0]

        for event in all_events.json():
            if event['door_controller_name'] == 'Design Point':
                return event
            else:
                return False

    def searchNexudusCards(self,lastevent):

        cardNumber = int(lastevent['credentials_number'])

        if cardNumber in self.cleanCredentialList(self.users.AccessCardId):
            return False

        if cardNumber in self.cleanCredentialList(self.users.KeyFobNumber):
            return False

        return True

    def cleanCredentialList(self,series):

        list_of_creds = []
        for value in series.to_list():

            if value == None:
                continue
            elif '\t' in value:
                n = int(value.split('\t')[-1])
                list_of_creds.append(n)
            elif ',' in value:
                for n in value.split(','):
                    list_of_creds.append(int(n))
            else:
                try:
                    list_of_creds.append(int(value))
                except:
                    pass

        return(list_of_creds)

    def pushUpdate(self,lastevent,name):

        update = self.users[self.users.FullName==name].iloc[0].to_dict()
        update['KeyFobNumber'] = update['KeyFobNumber']+','+lastevent['credentials_number']

        url = "https://spaces.nexudus.com/api/spaces/coworkers"
        r = requests.put(url, auth=self.nexudus_auth, json=update)
        if r.status_code == 201:
            print('Success')
            return True
        else:
            print('Something went wrong with the upload')
            return False

if __name__ == '__main__':
    root = tkinter.Tk()
    root.withdraw()
    app = SignUpAll(root)
    root.mainloop()
