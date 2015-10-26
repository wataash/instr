# Std libs
import os.path
import sqlite3
# Non-std libs
import matplotlib.pyplot as plt
# MyLibs
import constants as c


class Pa300Plot():
    """description of class"""
    def __init__(self, sample='sample'):
        # Database
        self.conn_params = sqlite3.connect(c.sql_params_dropbox)
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
        self.auto_scale = True
        self.c_min = {'J': 0, 'R': 1e3, 'RA': 1e-8}[self.var]
        self.c_max = {'J': 1, 'R': 1e5, 'RA': 1e-3}[self.var]
        # Miscellaneous
        self.save_dir = os.path.expanduser('~/Desktop/')

    def plot_I_V():
        raise NotImplementedError

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
                (c.p_sample, mesa)).fetchall()
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
                    vmin=self.c_min, vmax=self.c_max)  # vmin, vmax: color scale
            #plt.colorbar(sc)

            file_name = self.save_dir + '{sample}_{mesa}_{var_y}-XY_auto.png'.\
                format(sample=self.sample, mesa=mesa, var_y=self.var)
            if not self.auto_scale:
                file_name = \
                    file_name.replace(
                        'auto','{c_min:.0E}_{c_max:1.0E}'.
                        format(c_min=self.c_min, c_max=self.c_max))
            plt.savefig(file_name, transparent=True, dpi=100)


if __name__ == '__main__':
    p = Pa300Plot(c.p_sample)
    p.var = ['J', 'R', 'RA'][1]
    p.plot_R_XY()
    #p.auto_scale = True
    #p.mesas = p.mesas[0:4]
    p.plot_R_X()
