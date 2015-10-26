# Std libs
#import math
#import os
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
                'SELECT X,Y,zzz FROM resistance WHERE sample=? AND mesa=? AND Y>=10'.
                replace('zzz', self.var),
                (self.sample, mesa)).fetchall()
            if XYRs == []:
                continue
            Xs[mesa], Ys[mesa], Rs[mesa] = zip(*XYRs)
            ax.scatter(Xs[mesa], Rs[mesa], marker='o', label=mesa)

            XYRs = cur_params.execute(
                'SELECT X,Y,RA FROM resistance WHERE sample=? AND mesa=? AND Y<=9',
                (c.p_sample, mesa)).fetchall()
            if XYRs == []:
                continue
            Xs[mesa], Ys[mesa], Rs[mesa] = zip(*XYRs)
            ax.scatter(Xs[mesa], Rs[mesa], marker='o', c='r', label=mesa)
        plt.show()
        return


if __name__ == '__main__':
    p = Pa300Plot(c.p_sample)
    p.var = ['J', 'R', 'RA'][1]
    #p.auto_scale = True
    p.plot_R_X()
