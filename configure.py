from collections import defaultdict
import inspect
import json
import tkinter
import tkinter.filedialog
import os


conf = defaultdict(str)
os.makedirs(os.environ['appdata'] + r'\instr', exist_ok=True)

try:
    with open(os.environ['appdata'] + r'\instr\Agilent4156C.json') as f:
        conf = defaultdict(str, json.load(f))
except FileNotFoundError:
    print('File not found:' + os.environ['appdata'] + r'\instr\Agilent4156C.json')


class Application(tkinter.Frame):
    def __init__(self, master=None):
        tkinter.Frame.__init__(self, master)
        # self.entries = defaultdict(str)
        self.entries = {}
        self._pad = 2  # 2px
        self._irow = 0  # row index

        self.title('Save data to')
        tkinter.Button(self, text='Browse', command=self.browse_write).\
            grid(row=self._irow, column=0, padx=self._pad, pady=self._pad, sticky=tkinter.E)
        self.entries['data_dir'] = tkinter.Entry(self)
        self.entries['data_dir'].insert(0, conf['data_dir'])
        self.entries['data_dir'].grid(row=self._irow, column=1, padx=self._pad, pady=self._pad)
        self._irow += 1

        self.title('VISA configurations')
        self.entries['agi_visa_rsrc_name'] = self.label_and_entry('Agilent 4156C VISA resource name', conf['agi_visa_rsrc_name'])
        self.entries['agi_visa_timeout_sec'] = self.label_and_entry('Agilent 4156C timeout [s]', conf['agi_visa_timeout_sec'])
        self.entries['suss_visa_rsrc_name'] = self.label_and_entry('SUSS PA300 VISA resource name', conf['suss_visa_rsrc_name'])
        self.entries['suss_visa_timeout_sec'] = self.label_and_entry('SUSS PA300 timeout [s]', conf['suss_visa_timeout_sec'])

        self.title('Device information')
        self.entries['sample'] = self.label_and_entry('Sample', conf['sample'])
        self.entries['mesa'] = self.label_and_entry('Mesa type', conf['mesa'])
        self.entries['distance_between_mesa'] = self.label_and_entry('Distance between mesa [um]', conf['distance_between_mesa'])
        self.entries['max_X'] = self.label_and_entry('Max X', conf['max_X'])
        self.entries['max_Y'] = self.label_and_entry('Max Y', conf['max_Y'])
        self.entries['subs_width'] = self.label_and_entry('Substrate width [um] (approximately)', conf['subs_width'])
        self.entries['subs_height'] = self.label_and_entry('Substrate height [um] (approximately)', conf['subs_height'])
        self.entries['theta_diagonal'] = self.label_and_entry('theta_diagonal (calculated by theta.py)', conf['theta_diagonal'])
        self.entries['x00_subs'] = self.label_and_entry('x00_subs (calculated by theta.py)', conf['x00_subs'])
        self.entries['y00_subs'] = self.label_and_entry('y00_subs (calculated by theta.py)', conf['y00_subs'])

        self.title('Measurement configurations')
        self.entries['z_contact'] = self.label_and_entry('z_contact', conf['z_contact'])
        self.entries['z_separate'] = self.label_and_entry('z_separate', conf['z_separate'])
        self.entries['compliance'] = self.label_and_entry('Compliance current [A]', conf['compliance'])
        self.entries['meas_XYs'] = self.label_and_entry('XYs to measure (X0 Y0, X1 Y1, ...)', self.meas_XYs_to_input_form(conf['meas_XYs']))
        self.entries['meas_Vs'] = self.label_and_entry('Voltages [V] (V0 V1 ...)', self.meas_Vs_to_input_form(conf['meas_Vs']))

        self.title('template')
        self.entries['template'] = self.label_and_entry('template label', 'template entry')

        self.OK_button = tkinter.Button(self, text='OK', command=self.command_OK)
        self.OK_button.grid(row=self._irow, columnspan=2, padx=self._pad, pady=self._pad, sticky=tkinter.W+tkinter.E)
        self._irow += 1

        self.OK_button.focus_set()  # To enable quick closing window by hit the space bar

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
        # print(conf['asdf']) -> conf has key 'asdf'
        for key in self.entries.keys():
            conf[key] = self.entries[key].get()
        conf['agi_visa_timeout_sec'] = int(conf['agi_visa_timeout_sec'])
        conf['suss_visa_timeout_sec'] = int(conf['suss_visa_timeout_sec'])
        conf['distance_between_mesa'] = float(conf['distance_between_mesa'])
        conf['max_X'] = int(conf['max_X'])
        conf['max_Y'] = int(conf['max_Y'])
        conf['subs_width'] = float(conf['subs_width'])
        conf['subs_height'] = float(conf['subs_height'])
        conf['theta_diagonal'] = float(conf['theta_diagonal'])
        conf['x00_subs'] = float(conf['x00_subs'])
        conf['y00_subs'] = float(conf['y00_subs'])
        conf['z_contact'] = float(conf['z_contact'])
        conf['z_separate'] = float(conf['z_separate'])
        conf['compliance'] = float(conf['compliance'])
        conf['meas_XYs'] = self.meas_XYs_parse(conf['meas_XYs'])
        conf['meas_Vs'] = self.meas_Vs_parse(conf['meas_Vs'])
        root.destroy()
        # root.quit()

    def browse_write(self):
        selected_dir = tkinter.filedialog.askdirectory()
        if selected_dir != '':
            self.entries['data_dir'].delete(0, 'end')
            self.entries['data_dir'].insert(0, selected_dir)

    def meas_XYs_to_input_form(self, meas_XYs):
        """
        [(X0, Y0), (X1, Y1), ...] -> 'X0 Y0, X1 Y1, ...'

        :type meas_XYs: list[tuple[int]]
        :rtype: str
        """
        try:
            tmp = [str(XY[0]) + ' ' + str(XY[1]) for XY in meas_XYs]  # ['X0 Y0', 'X1 Y1', ...]
            tmp = ', '.join(tmp)
            return tmp
        except ValueError:
            print('ValueError on', inspect.stack()[0][3])
            return ''

    def meas_XYs_parse(self, meas_XYs_input):
        """
        'X0 Y0, X1 Y1, ...' -> [(X0, Y0), (X1, Y1), ...]

        :type meas_XYs_input: str
        :rtype: list[tuple[int]]
        """
        try:
            tmp = meas_XYs_input.split(',')  # ['X0 Y0', ' X1 Y1', ...]
            tmp = [tuple(map(int, XY.split())) for XY in tmp]
            return tmp
        except ValueError:
            print('ValueError on', inspect.stack()[0][3])
            return [ ]

    def meas_Vs_to_input_form(self, meas_Vs):
        """
        [V0, V1, ...] -> 'V0 V1 ...'

        :type meas_Vs: list of float
        :rtype: str
        """
        try:
            tmp = map(str, meas_Vs)
            tmp = ' '.join(tmp)
            return tmp
        except ValueError:
            print('ValueError on', inspect.stack()[0][3])
            return ''

    def meas_Vs_parse(self, meas_Vs_input):
        """
        'V0 V1 ...' -> [V0, V1, ...]

        :type meas_Vs_input: str
        :rtype: list of float
        """
        try:
            tmp = [float(V) for V in meas_Vs_input.split()]
            return tmp
        except ValueError:
            print('ValueError on', inspect.stack()[0][3])
            return []


root = tkinter.Tk()
app = Application(master=root)
app.pack()

def main():
    app.mainloop()
    # TODO: conf = values on GUI
    with open(os.environ['appdata'] + r'\instr\Agilent4156C.json', 'w') as f:
        json.dump(conf, f)
    # print(app.e_agi_visa_timeout_sec.get())
    # app.mainloop()
    # print(app.e_agi_visa_timeout_sec.get
    return conf

if __name__ == '__main__':
    main()
