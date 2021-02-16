import tkinter
import requests
import pandas as pd
from tkinter import ttk
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

        nameLabel = tkinter.Label(self.top, text='Select Your Name')
        nameLabel.grid(row=1, column=1, columnspan=2)

        self.namesList = self.getNamesFromNexudus()
        self.selectedName = tkinter.StringVar(self.top)

        nameDropDown = AutocompleteCombobox(self.top, textvariable=self.selectedName)
        nameDropDown.set_completion_list(self.namesList)
        nameDropDown.grid(row=2, column=1, columnspan=2)

        selectButton = tkinter.Button(self.top, text='Start', command=self.startAssignment)
        selectButton.grid(row=3, column=1)

        refreshButton = tkinter.Button(self.top, text='Refresh', command = self.getNamesFromNexudus)
        refreshButton.grid(row=3, column=2)

    def getNamesFromNexudus(self):
        """Pull the list of users from nexudus and return a list of the names"""
        nexudus_auth = ('', b'')
        url = "https://spaces.nexudus.com/api/spaces/coworkers?size=500"
        all_users = requests.get(url, auth=nexudus_auth)
        all_users = pd.DataFrame(all_users.json()['Records'])
        names = all_users.FullName.to_list()
        all_users = None
        names = ['name1','name2','name3']
        self.users = all_users

        return names

    def startAssignment(self):
        """Wait for a signal from DoorFlow and assign the fob number to the appropriate user"""
        name = self.selectedName.get()
        self.statusWindow = tkinter.Toplevel(self.top)
        self.statusWindow.configure(bg='green')
        waitLabel = tkinter.Label(self.statusWindow, text='Hit Fob against the reader now')
        waitLabel.grid()

        self.doorflowStatus = False

        self.checkDoorFlow()

    def checkDoorFlow(self):

        if self.doorflowStatus == False:
            doorflow_auth = requests.auth.HTTPBasicAuth('3zxv-BQUSiSyER5UxrM4','x')
            time.sleep(2)
            print('Response Recieved')
            self.statusWindow.destroy()
            self.doorflowStatus = True
        elif self.doorflowStatus == True:
            print('Do Nothing')

        self.top.after(2000, self.checkDoorFlow)



if __name__ == '__main__':
    root = tkinter.Tk()
    app = SignUpAll(root)
    root.mainloop()
