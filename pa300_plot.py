# Std libs
import os.path
import sqlite3
# Non-std libs
import matplotlib.pyplot as plt
# MyLibs
import constants as c


class Pa300Plot():
    """description of class"""
    def __init__(self, sample, sql_params_path):
        # Database
        self.conn_params = sqlite3.connect(sql_params_path)
        self.cur_params = self.conn_params.cursor()
        # Device infomation
        self.sample = sample
        self.mask, self.X_min, self.X_max, self.Y_min, self.Y_max = \
            self.cur_params.execute('SELECT mask, X_min, X_max, Y_min, Y_max \
            FROM samples WHERE sample=?',
            (self.sample,)).fetchone()
        mesas = self.cur_params.execute('SELECT mesa FROM mesas WHERE mask=?',
                                   (self.mask,)).fetchall()
        self.mesas = [x[0] for x in mesas]
        # Plot config
        self.var = 'R'
        self.var_unit = {'J': 'Am2', 'R': 'ohm', 'RA': 'ohmm2'}[self.var]
        self.auto_scale = True
        self.var_min = {'J': 0, 'R': 1e3, 'RA': 1e-8}[self.var]
        self.var_max = {'J': 1, 'R': 1e5, 'RA': 1e-3}[self.var]
        # Miscellaneous
        self.save_dir = os.path.expanduser('~/Desktop/')

    def plot_R_X(self):
        Xs = {}
        Ys = {}
        Rs = {}
        fig = plt.figure()
        ax = plt.gca()
        ax.set_yscale('log')
        for mesa in self.mesas:
            XYRs = self.cur_params.execute(
                'SELECT X,Y,zzz FROM resistance \
                 WHERE sample=? AND mesa=? AND Y>=1'.
                replace('zzz', self.var),
                (self.sample, mesa)).fetchall()
            if XYRs == []:
                continue
            Xs[mesa], Ys[mesa], Rs[mesa] = zip(*XYRs)
            ax.scatter(Xs[mesa], Rs[mesa], c=Ys[mesa], marker='x', label=mesa)
            for i in range(len(Xs[mesa])):
                ax.annotate(Ys[mesa][i], (Xs[mesa][i], Rs[mesa][i]))
            #ax.legend(loc=2)
            #plt.ylim([1e3, 1e8])
        plt.show()
        return

    def plot_R_X_caseY(self):
        # separate cases of Y
        Xs = {}
        Ys = {}
        Rs = {}
        for mesa in self.mesas:
            XYRs = self.cur_params.execute(
                'SELECT X,Y,zzz FROM resistance \
                 WHERE sample=? AND mesa=? AND Y>=10'.
                replace('zzz', self.var),
                (self.sample, mesa)).fetchall()
            if XYRs == []:
                continue
            Xs[mesa], Ys[mesa], Rs[mesa] = zip(*XYRs)
            ax.scatter(Xs[mesa], Rs[mesa], marker='o', label=mesa)

            XYRs = cur_params.execute(
                'SELECT X,Y,RA FROM resistance \
                 WHERE sample=? AND mesa=? AND Y<=9',
                (self.sample, mesa)).fetchall()
            if XYRs == []:
                continue
            Xs[mesa], Ys[mesa], Rs[mesa] = zip(*XYRs)
            ax.scatter(Xs[mesa], Rs[mesa], marker='o', c='r', label=mesa)
        plt.show()
        return

    def plot_R_XY(self):
        from matplotlib.colors import LogNorm
        for mesa in self.mesas:
            XYzs = self.cur_params.execute(
                       'SELECT X,Y,z FROM resistance WHERE sample=? AND mesa=?'.
                       replace('Y,z', 'Y,' + self.var),
                       (self.sample, mesa)
                   ).fetchall()

            # /100: inches to px (for 100dpi)
            # optimized size
            # X  Y  widt heig
            # 17 8  1100 500
            # 15 4  970  250
            # 4  1  270  300?
            # 4  8  270  500
            fig = plt.figure(figsize=((1100)/100, (500)/100))
            ax = fig.add_subplot(1,1,1)

            # Ticks and grid
            ax.grid(which='minor', linestyle='-', color='gray')
            ax.set_xticks(list(range(self.X_min, self.X_max+1)))
            # (min1,max9) -> 1.5, 2.5, ..., 8.5
            ax.set_xticks(
                [x + 0.5 for x in range(self.X_min, self.X_max)], minor=True)
            ax.set_yticks(list(range(self.Y_min, self.Y_max+1)))
            # (min1,max9) -> 1.5, 2.5, ..., 8.5
            ax.set_yticks(
                [x + 0.5 for x in range(self.Y_min, self.Y_max)], minor=True)

            # Axes
            plt.xlim([self.X_min - 0.6, self.X_max + 0.6])
            plt.ylim([self.Y_min - 0.5, self.Y_max + 0.5])
            ax.tick_params(labeltop=True, labelright=True)

            # Plot
            Xs = []
            Ys = []
            zs = []
            for (X, Y, z) in XYzs:
                if z is None:
                    continue
                Xs.append(X)
                Ys.append(Y)
                zs.append(z)
                txt = '{:.2E}'.format(z).replace('E', '\nE')  # 1.2 \n E+03
                ax.annotate(
                    txt, xy=(X,Y),
                    verticalalignment='center', horizontalalignment='center')

            if self.auto_scale:
                sc = ax.scatter(
                    Xs, Ys, 
                    c=zs, cmap='coolwarm', s=1200, marker='s', norm=LogNorm())
            else:
                sc = ax.scatter(
                    Xs, Ys, 
                    c=zs, cmap='coolwarm', s=1200, marker='s', norm=LogNorm(),
                    vmin=self.var_min, vmax=self.var_max)  # vmin, vmax: color scale
            #plt.colorbar(sc)

            file_name = self.save_dir + '{sample}_{mesa}_{var_y}-XY_auto.png'.\
                format(sample=self.sample, mesa=mesa, var_y=self.var)
            if not self.auto_scale:
                file_name = \
                    file_name.replace(
                        'auto','{c_min:.0E}_{c_max:1.0E}'.
                        format(c_min=self.var_min, c_max=self.var_max))
            plt.savefig(file_name, transparent=True, dpi=100)


class Pa300PlotIV(Pa300Plot):
    def __init__(self, sample, sql_params_path, sql_IVs_path):
        super().__init__(sample, sql_params_path)
        self.conn_IVs = sqlite3.connect(sql_IVs_path)
        self.cur_IVs = self.conn_IVs.cursor()

    def plot_I_VXY(self, V_min, V_max, remove_V):
        # TODO: V_min, V_max from SQL
        from matplotlib import cm
        import numpy as np
        from lib.algorithms import remove_X_near_0
        from lib.algorithms import remove_xyz_by_x
        for mesa in self.mesas:
            area = self.cur_params.execute(
                'SELECT area FROM mesas WHERE mesa=?',
                (mesa,)).fetchone()
            
            # Number of columns and rows in matrix plot
            numX = self.X_max - self.X_min + 1
            numY = self.Y_max - self.Y_min + 1
            
            # Set png file name
            if self.auto_scale:
                # sample_mesa_RA_auto_ohmm2_-0.2V_0.2V.png
                save_file_name_base = self.save_dir + \
                    '{}_{}_{}_auto_{}_{}V_{}V.png'. \
                    format(self.sample, mesa,
                           self.var, self.var_unit,
                           V_min, V_max)
            else:
                # sample_mesa_RA_1E10_1E11_ohmm2_-0.2V_0.2V.png
                save_file_name_base = self.save_dir + \
                    '{}_{}_{}_{}_{}_{}_{}V_{}V.png'. \
                    format(self.sample, mesa,
                           self.var, self.var_unit,
                           str(self.var_min), str(self.var_max),  # TODO test
                           V_min, V_max)
            print('Save to:', save_file_name_base)

            print('Making subplots frame...')
            # Takes long time. figsize: inches. (300dpi -> about (300*numX px, 300*numY px)
            # Bug: Error when (X_min == X_max) or (Y_min == Y_max) at axarr[rowi, coli]
            # They must be (X_min < X_max) and (Y_min < Y_max).
            numX = numX if numX > 1 else 2
            numY = numY if numY > 1 else 2

            f, axarr = plt.subplots(numY, numX, figsize=(numX, numY), facecolor='w')
            if not self.auto_scale:
                f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)
            else:
                f.subplots_adjust(top=0.99, bottom=0.01, left=0.01, right=0.99, wspace=0, hspace=0)

            for Y in range(self.Y_min, self.Y_max + 1):
                for X in range(self.X_min, self.X_max + 1):
                    print('Processing X{}Y{}.'.format(X, Y))
                    t0s = self.cur_params.execute('SELECT t0 FROM IV_params WHERE sample=? AND mesa=? AND X=? AND Y=?',
                                                (self.sample, mesa, X, Y)).fetchall()

                    # rowi coli X Y matrix (if numX == numY == 9)
                    # 00XminYmax     ...                90XmaxYmax
                    # ...
                    # 80Xmin(Ymin+1) ...
                    # 90XminYmin     91(Xmin+1)Ymin ... 99XmaxYmin
                    coli = -self.X_min + X
                    rowi = self.Y_max - Y
                    ax = axarr[rowi, coli]

                    if t0s == []:
                        print('No data on X{}Y{} (rowi{}coli{})'.format(X, Y, rowi, coli))
                        # No tick
                        ax.set_xticks([])
                        ax.set_yticks([])
                        continue
        
                    if self.var in ['J', 'dJdV']:
                        #ax.locator_params(nbins=5)  # number of ticks
                        ax.set_yticks([0])  # tick only zero level
                        ax.yaxis.set_major_formatter(plt.NullFormatter())  # Hide value of ticks
                    elif self.var in ['R', 'RA']:
                        ax.set_yticks([0])
                        ax.yaxis.set_major_formatter(plt.NullFormatter())
                        #ax.get_yaxis().get_major_formatter().set_powerlimits((0, 0))  # Force exponential ticks

                    # Get data XY
                    xs = np.array([])  # x axis values
                    ys = np.array([])  # y axis values
                    for t0 in t0s:
                        VIs_new = self.cur_IVs.execute('SELECT V, I FROM IVs WHERE t0=?', t0).fetchall() # Be sure that t0 has index (else slow)
                        VIs_new = np.array(VIs_new)
                        if self.var in ['RA', 'R']:
                            VIs_new = remove_X_near_0(VIs_new, remove_V)  # TODO: auto determine divergence near 0
                        Vs_new = VIs_new.transpose()[0]
                        xs = np.append(xs, Vs_new)
                        Js_new = VIs_new.transpose()[1]/area
                        if self.var == 'J':
                            ys = np.append(ys, Js_new)
                        elif self.var == 'RA':
                            RAs_new = Vs_new/Js_new
                            ys = np.append(ys, RAs_new)
                        elif self.var == 'R':
                            Rs_new = Vs_new/(Js_new*area)
                            ys = np.append(ys, Rs_new)
                        elif self.var == 'dJdV':
                            dJdV_new = np.gradient(Js_new, Vs_new)  # TODO: implement
                            ys = np.append(ys, dJdV_new)
                    xys_in_range = remove_xyz_by_x(lambda x: not V_min < x < V_max, xs, ys)
                    ys_in_range = xys_in_range[1]

                    # Plot
                    #ax.plot(xs, ys, 'b', linewidth=0.5)
                    ax.scatter(xs, ys, s=1, c=list(range(len(xs))), cmap=cm.rainbow, edgecolor='none')  # s: size

                    ax.set_xticks([])
                    ax.set_xlim([V_min, V_max])
                    if not self.auto_scale:
                        ax.set_yticks([])
                        ax.set_ylim([self.var_min, self.var_max])
                    elif self.var in ['J', 'dJdV']:
                        # Symmetric y limits with respect to y=0
                        y_abs_max = max(abs(ys_in_range))
                        ax.set_ylim([-y_abs_max, y_abs_max])
                        y_lim_txt = '{:.1E}'.format(y_abs_max).replace('E', '\nE')  # 1.23 \n E+4
                        # ha: horizontal alignment, va: vertical alignment, transAxes: relative coordinates
                        ax.text(0.01, 0.99, y_lim_txt, ha='left', va='top', transform=ax.transAxes)
                    elif self.var in ['R', 'RA']:
                        # Assuming ys > 0
                        y_min = min(ys_in_range)  # TODO: use ys only V_min-V_max
                        y_max = max(ys_in_range)
                        y_range = y_max - y_min
                        if not float('Inf') in [y_min, y_max]:
                            ax.set_ylim([y_min - 0.1*y_range, y_max + 0.1*y_range])
                        y_lim_txt_top = '{:.1E}'.format(y_max).replace('E', '\nE')  # 1.23 \n E+4
                        ax.text(0.01, 0.99, y_lim_txt_top, ha='left', va='top', transform=ax.transAxes)
                        y_lim_txt_bottom = '{:.1E}'.format(y_min).replace('E', '\nE')
                        ax.text(0.01, 0.01, y_lim_txt_bottom, ha='left', va='bottom', transform=ax.transAxes)

            print('Saving', save_file_name_base + '.png')
            plt.savefig(save_file_name_base + '.png', dpi=200, transparent=True)
            #print('Saving', save_file_name_base + '.pdf')
            #plt.savefig(save_file_name_base + '.pdf', transparent=True)  # dpi is ignored, transparent as well?
        return



if __name__ == '__main__':
    pp = Pa300PlotIV(c.p_sample, c.sql_params_dropbox, c.p_sql_IVs_path)
    pp.plot_I_VXY(-0.2, 0.2, 0.020)

    #p = Pa300Plot(c.p_sample, c.sql_params_dropbox)
    #p.var = ['J', 'R', 'RA'][1]
    #p.plot_R_XY()
    #p.auto_scale = True
    #p.mesas = p.mesas[0:4]
    #p.plot_R_X()
