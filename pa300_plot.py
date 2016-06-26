import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
import pandas.io.sql as psql
import seaborn as sns

import lib.algorithms as al
from lib.database import Database

# TODO ampere engineer form, twin ticks A/m2


var_unit = {
    'I': 'A',
    'J': 'A/m^2',
    'R': 'ohm',
    'RA': 'ohm m^2'
}

dic_var_label = {
    'I': 'Current (A)',
    'J': 'Current density (A/m^2)',
    'R': 'Resistance(Ohm)',
    'RA': 'Resistance area product (Ohm m^2)',
}


def RX(db, sample, plot_mesas=None, RA=False, annotate=False, RY=False,
       make_legend=False, inst='suss_test',
       VI_remarks_plot={'g'},
       VI_remarks_del={'i', 'c', 'bd', 'h', 'l'},
       thickness=False):
    """

    :param sample: 'sample'
    :param plot_mesas: ['mesa1, 'mesa2'], None -> all
    :param VI_remarks:  TODO
    """
    sns.set_style('whitegrid')
    sns.set_context('poster')
    # colors = sns.husl_palette(4, l=.7)
    colors = sns.color_palette()

    yvar = 'RA' if RA else 'R'

    ax = plt.axes()
    assert isinstance(ax, Axes)
    ax.set_yscale('log')
    ax.set_xlabel('Y') if RY else ax.set_xlabel('X')
    ax.set_ylabel(dic_var_label[yvar])

    sql = 'SELECT mesa, area, color, marker FROM v03_sample_mesa ' \
          'WHERE sample=%s'
    df_mesa = psql.read_sql(sql, db.cnx, params=(sample,))
    for i, s_mesa in df_mesa.iterrows():
        if (plot_mesas is not None) and (s_mesa.mesa not in plot_mesas):
            continue
        sql = ('SELECT X, Y, X_pad, Y_pad, tX, tY, '
               'suss_R0 AS R0, suss_RA0 AS RA0, '
               'suss_R2 AS R2, VI_remarks AS rem FROM v04_device '
               'WHERE sample=%s AND mesa=%s')
        df_R = psql.read_sql(sql, db.cnx,
                             params=(sample, s_mesa.mesa))
        if thickness:
            df_R.X_pad = df_R.tX
        if df_R.empty:
            continue

        df_R['val'] = df_R.RA0 if RA else df_R.R0

        df_R_plot = df_R
        if VI_remarks_plot:
            filt = df_R_plot.rem.apply(lambda x: (set(x.split(' ')) & VI_remarks_plot)
                                            != set())
            df_R_plot = df_R_plot[filt]
        if VI_remarks_del:
            filt = df_R_plot.rem.apply(lambda x: (set(x.split(' ')) & VI_remarks_del)
                                            == set())
            df_R_plot = df_R_plot[filt]

        if s_mesa.marker == '6':
            s_mesa.marker = 6
        if RY:
            ax.scatter(df_R_plot.Y_pad, df_R_plot.val, c=colors[s_mesa.color],
                       s=50, marker=s_mesa.marker, label=s_mesa.mesa)
        else:
            ax.scatter(df_R_plot.X_pad, df_R_plot.val, c=colors[s_mesa.color],
                       s=50, marker=s_mesa.marker, label=s_mesa.mesa)
            ax.scatter(df_R_plot.X_pad, df_R_plot.val, c=colors[s_mesa.color],
                       s=50, marker=s_mesa.marker, label=s_mesa.mesa)
            # ax.scatter(df_R_plot.X_pad, df_R_plot.val, c=colors[s_mesa.color],
            #            s=50, marker=s_mesa.marker, label=s_mesa.mesa)
        if annotate:
            ann_xs = df_R.Y_pad if RY else df_R.X_pad
            ann_ys = df_R.RA0 if RA else df_R.R0
            for x, y, X, Y, rem in \
                    zip(ann_xs, ann_ys, df_R.X, df_R.Y, df_R.rem):
                ax.annotate(str(X) + ',' + str(Y) + rem, (x, y))

    # plt.xlim(0, 16)  # TODO
    # plt.ylim(1e-9, 1e3)  # TODO

    if make_legend:
        ax.legend(loc=2)
    plt.tight_layout()
    plt.show()
    pass


def Rmap(db, sample, mesa=None, RA=True, clim=None, cbar=False,
         annotate=True, inst='suss_test', whiteout_remarks=set()):
    from matplotlib.colors import LogNorm
    sns.set_style('white')
    if mesa is not None:
        pass  # TODO

    sql = 'SELECT Xmin, Xmax, Ymin, Ymax FROM v02_sample WHERE sample=%s'
    X_min, X_max, Y_min, Y_max = db.q_row_abs(sql, (sample,))

    px_x = 50 * (X_max - X_min + 1)  # not optimized
    px_y = 50 * (Y_max - Y_min + 1)
    # 100dpi px -> inches
    _, ax = plt.subplots(figsize=(px_x / 100, px_y / 100))

    # Ticks and grids
    ax.grid(which='minor', linestyle='-', color='gray')
    ax.set_xticks(list(range(X_min, X_max + 1)))
    # (min1,max9) -> 1.5, 2.5, ..., 8.5
    ax.set_xticks([x + 0.5 for x in range(X_min, X_max)], minor=True)
    ax.set_yticks(list(range(Y_min, Y_max + 1)))
    # (min1,max9) -> 1.5, 2.5, ..., 8.5
    ax.set_yticks([x + 0.5 for x in range(Y_min, Y_max)], minor=True)

    # xylim
    plt.xlim([X_min - 0.6, X_max + 0.6])
    plt.ylim([Y_min - 0.5, Y_max + 0.5])
    ax.tick_params(labeltop=True, labelright=True)

    # scatter
    if inst == 'suss_test':
        sql = 'SELECT X_pad, Y_pad, suss_R0 as R, suss_RA0 as RA, ' \
              'suss_R2 as R2, VI_remarks as rem ' \
              'FROM v04_device WHERE sample=%s'
    elif inst == 'suss':
        sql = 'SELECT X_pad, Y_pad, suss2_R0 as R, suss2_RA0 as RA, ' \
              'suss2_R2 as R2, VI_remarks as rem ' \
              'FROM v04_device WHERE sample=%s'
    df_R = db.pdq(sql, (sample,))
    # df_R = df_R[df_R.R2.apply(al.num_9th) >= R2_9th_lim]
    df_R['val'] = df_R.RA if RA else df_R.R
    df_R['rem_list'] = df_R.rem.apply(lambda x: x.split(' '))
    # for black in blacklist:
    #     df_R = df_R[df_R.rem_list != black]

    df_R_plot = df_R
    whiteout = df_R.apply(lambda x: set(x.rem_list) & whiteout_remarks, axis=1)
    df_R_plot = df_R_plot[whiteout == set()]
    if clim is not None:
        df_R_plot = df_R_plot[clim[0] <= df_R_plot.val]
        df_R_plot = df_R_plot[df_R_plot.val <= clim[1]]
    else:
        clim = (df_R_plot.val.min(), df_R_plot.val.max())
    sc = ax.scatter(df_R_plot.X_pad, df_R_plot.Y_pad, c=df_R_plot.val,
                    cmap='coolwarm',
                    s=50, marker='s', norm=LogNorm(),
                    vmin=clim[0], vmax=clim[1])

    if annotate:
        # text
        for i, row_R in df_R.iterrows():
            if row_R.val < 0:
                print(row_R.val, '-> 1e-99')
                row_R.val = 1e-99
            txt = '{:.1f}'.format(math.log10(row_R.val))
            ax.annotate(txt, xy=(row_R.X_pad, row_R.Y_pad),
                        verticalalignment='center',
                        horizontalalignment='center',
                        size=4)
    if cbar:
        plt.colorbar(sc)
    plt.tight_layout()
    plt.show()


def iv_matrix(db, sample, mesa, xlim=(-1.0, 1.0),
              XXYY=None, inst='%', save_path=None,
              R2_9th_lim=1.5, v_fit=(-0.1, 0.1),
              grayout_remarks={'i', 'lin', 'c', 'bd'},
              edit_remarks=False, db_rds=None, remarks_path=None, commit=False):
    """
    :param XXYY: (X_min, X_max, Y_min, Y_max). if is None -> all XYs
    """
    plt.close()
    sns.set_style("white")

    sql = ('SELECT device_id AS did, X, Y, area, suss_R0 AS R0, suss_RA0 AS RA0, '
           'VI_remarks as rem '
           'FROM v04_device WHERE sample=%s AND mesa=%s')
    df = db.pdq(sql, (sample, mesa,))

    if XXYY is None:
        X_min, X_max, Y_min, Y_max = \
            df.X.min(), df.X.max(), df.Y.min(), df.Y.max()
    else:
        X_min, X_max, Y_min, Y_max = XXYY

    # Number of columns and rows in matrix plot.
    numX = X_max - X_min + 1
    numY = Y_max - Y_min + 1
    if edit_remarks:
        devid_matrix = [[None for x in range(numX)] for y in range(numY)]
        remarks_matrix = [['NULL' for x in range(numX)] for y in range(numY)]

    # Takes long time.
    print('Making subplots frame...')
    #  http://matplotlib.org/api/pyplot_api.html
    subplot_kw = {'xlim': xlim, 'ylim': (-1, 1),
                  'xticks': [], 'yticks': [0]}
    f, axarr = plt.subplots(numY, numX, squeeze=False, subplot_kw=subplot_kw,
                            figsize=(numX, numY), facecolor='w')

    f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)

    for i, d in df.iterrows():
        if not ((X_min <= d.X <= X_max) and (Y_min <= d.Y <= Y_max)):
            continue
        row = Y_max - d.Y
        col = -X_min + d.X
        ax = axarr[row, col]  # row, col
        ax.yaxis.set_major_formatter(plt.NullFormatter())  # Hide ticks labels

        if edit_remarks:
            devid_matrix[row][col] = d.did
            remarks_matrix[row][col] = d.rem

        tx_lb = d.rem.replace(' ', '\n')  # text left bottom
        ax.text(0.1, 0, tx_lb, ha='left', va='bottom',
                transform=ax.transAxes, size='x-small')

        print('Querying vis... (X{} Y{} {} device id: {})'.
              format(d.X, d.Y, mesa, d.did), end=' ', flush=True)
        sql = 'SELECT V, I FROM v_py_matrix ' \
              'WHERE device_id=%s AND inst LIKE %s'
        VI = db.pdq(sql, (d.did, inst,))
        print('Done.', end=' ', flush=True)
        if VI.empty:
            print()
            continue

        # fit
        VI_fit = VI[(v_fit[0] <= VI.V) & (VI.V <= v_fit[1])]
        c1, c2, c3, R2 = al.fit_R3(VI_fit)
        if not math.isclose(1/c1, d.R0, rel_tol=1e-2):  # tolerance: 2 digits
            print('R0 difference: db{} calc{}'.format(d.R0, 1/c1),
                  end=' ', flush=True)

        # Vs, Is, Rs
        VI['R'] = VI.V / VI.I
        VI['Ifit'] = c1 * VI.V + c2 * VI.V ** 2 + c3 * VI.V ** 3
        VI['Rfit'] = VI.V / VI.Ifit

        # Normalize to ylim(-1, 1)
        I_scale = VI.I.abs().max()
        VI['In'] = VI.I / I_scale  # [-1, 1]
        VI['Ifitn'] = VI.Ifit / I_scale  # [-1, 1]
        # Intervals: assuming R > 0
        R_scale = VI.R[(VI.R > 0) & (VI.R != np.inf)].max()
        R_scale = VI.Rfit.max()
        VI['Rn'] = (VI.R / R_scale) * 0.9  # (0, 0.9]
        VI['Rn'] = VI.Rn*2 - 1  # (-1, 0.9]
        VI['Rfitn'] = (VI.Rfit / R_scale)*0.9*2 - 1  # (-1, 0.9]

        R2_num_9th = al.num_9th(R2)
        if (R2_num_9th <= R2_9th_lim) or \
                (grayout_remarks & set(d.rem.split(' ')) != set()):
            blue, _, red = sns.color_palette('pastel')[:3]
        else:
            blue, _, red = sns.color_palette()[:3]
        ax.plot(VI.V, VI.Rn, c=red, lw=0.5)
        ax.plot(VI.V, VI.In, c=blue, lw=0.5)
        ax.plot(VI.V, VI.Rfitn, '--', c='gray', lw=0.5)
        ax.plot(VI.V, VI.Ifitn, '--', c='gray', lw=0.5)

        # X Y R2-#9th R0 RA0
        tx_lt = 'X{}Y{}\n{:d}'.format(d.X, d.Y, d.did)
        ax.text(0, 1, tx_lt, ha='left', va='top',
                transform=ax.transAxes, size='x-small')

        tx_rb = 'R2 {:.2f} {:.1f}\nR{:.1e}\nRA{:.1e}'. \
            format(R2, R2_num_9th, 1 / c1, d.area / c1)
        ax.text(1, 0, tx_rb, ha='right', va='bottom',
                transform=ax.transAxes, size='x-small')
        print('')  # newline

    if edit_remarks:
        with open(remarks_path, 'w') as f:
            f.write('\n'.join([','.join(row) for row in remarks_matrix]))

    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path)
    pass

    if edit_remarks:
        print('Edit', remarks_path, '.')
        input()
        with open(remarks_path, 'r') as f:
            remarks_matrix2 = f.readlines()
        remarks_matrix2 = [row.split(',') for row in remarks_matrix2]
        pairs_remarks_devid = []
        for row in range(numY):
            for col in range(numX):
                if devid_matrix[row][col] is None:
                    continue
                remarks = remarks_matrix2[row][col].strip()
                pairs_remarks_devid.append((remarks, devid_matrix[row][col]))
        oper = 'UPDATE device SET VI_remarks=%s WHERE device_id=%s'
        db_rds.exem(oper, pairs_remarks_devid)
        if commit:
            db_rds.cnx.commit()
            print('Edit comitted.')


def iv(db, sample, mXYs=(('mesa', 1, 1),), inst='suss_test',
       xlim=(-1.0, 1.0), normalize=False, console=False,
       legend=True, window_length=9, polyoder=4,
       deriv=0):
    sns.set_palette('coolwarm', len(mXYs))
    for (mesa, X, Y) in mXYs:
        sql = 'SELECT VI_param_id FROM v05_VI_param ' \
              'WHERE sample=%s AND mesa=%s AND X=%s AND Y=%s AND inst=%s'
        ids = db.q_col_abs(sql, (sample, mesa, X, Y, inst,))
        ids = map(str, ids)
        sql = 'SELECT V, I FROM VI WHERE VI_param_id in ({})'. \
            format(','.join(ids))
        vis = db.q_all_abs(sql, None)
        if normalize:
            vis = np.array(vis)
            vis[:, 1] /= abs(vis[:, 1]).max()
        vis = al.savgol_vis(vis, window_length, polyoder, deriv)
        if console:
            print(mesa, X, Y)
            print(vis)
        plt.plot(*zip(*vis), '.-')
        plt.xlim(xlim)
    plt.xlabel('Voltage (V)')
    if deriv == 0:
        ylabel = 'Current (A)'
    elif deriv == 1:
        ylabel = 'dI/dV (A/V)'
    else:
        ylabel = 'd^I/d^V (A/V^2)'
    plt.ylabel(ylabel)
    if legend:
        pass  # TODO
    plt.show()


def snips():
    # dpi is ignored.
    plt.savefig('aaa.png', dpi=200, transparent=True)
    # force scientific form
    plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
