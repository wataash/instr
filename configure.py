from collections import  defaultdict
import json
import tkinter
import tkinter.filedialog
import os

conf = defaultdict(str)

try:
    with open(os.environ['appdata'] + r'\instr\Agilent4156C.json') as f:
        conf = defaultdict(str, json.load(f))
except FileNotFoundError:
    pass


class Application(tkinter.Frame):
    def __init__(self, master=None):
        tkinter.Frame.__init__(self, master)
        self._pad = 2  # 2px
        self._irow = 0  # row index

        self.title('Save data to')
        tkinter.Button(self, text='Browse', command=self.browse_write).\
            grid(row=self._irow, column=0, padx=self._pad, pady=self._pad, sticky=tkinter.E)
        self.e_datadir = tkinter.Entry(self)
        self.e_datadir.insert(0, conf['datadir'])
        self.e_datadir.grid(row=self._irow, column=1, padx=self._pad, pady=self._pad)
        self._irow += 1

        self.title('VISA configurations')
        self.e_agilent_visa_resource_name = self.label_and_entry('Agilent 4156C VISA resource name', conf['agilent_visa_resource_name'])
        self.e_agilent_visa_timeout_sec = self.label_and_entry('Agilent 4156C timeout [s]', conf['agilent_visa_timeout_sec'])
        self.e_suss_visa_resource_name = self.label_and_entry('SUSS PA300 VISA resource name', conf['suss_visa_resource_name'])
        self.e_suss_visa_timeout_sec = self.label_and_entry('SUSS PA300 timeout [s]', conf['suss_visa_timeout_sec'])

        self.title('Device information')
        self.e_sample = self.label_and_entry('Sample', conf['sample'])
        self.e_mesa = self.label_and_entry('Mesa type', conf['mesa'])
        self.e_distance_between_mesa = self.label_and_entry('Distance between mesa [um]', conf['distance_between_mesa'])
        self.e_max_X = self.label_and_entry('Last X', conf['max_X'])
        self.e_max_Y = self.label_and_entry('Last Y', conf['max_Y'])
        self.e_subs_width = self.label_and_entry('Substrate width [um] (approximately)', conf['subs_width'])
        self.e_subs_height = self.label_and_entry('Substrate height [um] (approximately)', conf['subs_height'])
        self.e_theta_diagonal = self.label_and_entry('Theta_diagonal (calculated by theta.py)', conf['theta_diagonal'])
        self.e_x00_subs = self.label_and_entry('x00_substrate (calculated by theta.py)', conf['x00_subs'])
        self.e_y00_subs = self.label_and_entry('y00_substrate (calculated by theta.py)', conf['y00_subs'])

        self.title('Measurement configurations')
        self.e_z_contact = self.label_and_entry('z_contact', conf['z_contact'])
        self.e_z_separate = self.label_and_entry('z_separate', conf['z_separate'])
        self.e_meas_XYs = self.label_and_entry('XYs to measure (X Y, X Y, ...)', 'Not implemented (input manually')  # meas_XYs
        self.e_meas_Vs = self.label_and_entry('Voltage list (space separated)', 'Not implemented (input manually)')  # meas_Vs

        self.title('template')
        self.e_template = self.label_and_entry('template label', 'template entry')

        self.OK_button = tkinter.Button(self, text='OK', command=self.command_OK)
        self.OK_button.grid(row=self._irow, columnspan=2, padx=self._pad, pady=self._pad, sticky=tkinter.W+tkinter.E)
        self._irow += 1

        self.OK_button.focus_set()

    def label_and_entry(self, label_text, entry_text=''):
        tkinter.Label(self, text=label_text).\
            grid(row=self._irow, column=0, padx=self._pad, pady=self._pad, sticky=tkinter.W)
        entry = tkinter.Entry(self)
        entry.insert(0, entry_text)
        entry.grid(row=self._irow, column=1, padx=self._pad, pady=self._pad)
        self._irow += 1
        return entry

    def title(self, label_text):
        tkinter.Label(self, text=label_text).\
            grid(row=self._irow, columnspan=2, padx=self._pad, pady=self._pad, sticky=tkinter.W+tkinter.E)
        self._irow += 1

    def command_OK(self):
        root.quit()  # root.destroy()

    def browse_write(self):
        selected_dir = tkinter.filedialog.askdirectory()
        if selected_dir != '':
            self.e_datadir.delete(0, 'end')
            self.e_datadir.insert(0, selected_dir)


root = tkinter.Tk()
app = Application(master=root)
app.pack()

def main():
    app.mainloop()
    # TODO: conf = values on GUI
    with open(os.environ['appdata'] + r'\instr\Agilent4156C.json', 'w') as f:
        json.dump(conf, f)
    # print(app.e_agilent_visa_timeout_sec.get())
    # app.mainloop()
    # print(app.e_agilent_visa_timeout_sec.get
    app.destroy()
    return conf

if __name__ == '__main__':
    main()
