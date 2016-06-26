import lib.constants as c
from instr.suss_pa300 import SussPA300
from lib.database import Database


class PA300Setup(Database, SussPA300):
    def __init__(self, sample,
                 rsrc=None, reset=True, **mysql_config):
        Database.__init__(self, **mysql_config)
        SussPA300.__init__(self, rsrc, reset=reset)
        self.sample = sample

        query = 'SELECT mask, dX, dY, Xmin, Xmax, Ymin, Ymax FROM v02_sample ' \
                'WHERE sample=%s'
        self.mask, self.dX, self.dY, \
        self.X_min, self.X_max, self.Y_min, self.Y_max = \
            self.q_row_abs(query, (self.sample,))

        dat = self.q_all_abs('SELECT mesa_id, mesa FROM mesa '
                             'WHERE mask=%s', (self.mask,))
        self.dic_id_mesa = {mesa_id: mesa for mesa_id, mesa in dat}

        dat = self.q_all_abs('SELECT mesa_id, xm_probe, ym_probe FROM mesa '
                             'WHERE mask=%s', (self.mask,))
        self.dic_mid_xypr_default = {mesa: xm_ym for mesa, *xm_ym in dat}

        dat = self.q_all('SELECT mesa_id, xm_probe, ym_probe FROM suss_xm_ym '
                         'WHERE sample=%s', (self.sample,))
        self.dic_mid_xypr_specified = {mesa: xp_yp for mesa, *xp_yp in dat}

    def check_xm_ym_probe(self):
        # TODO all, sorted
        # List mesas
        for mesa_id, xpyp in self.dic_mid_xypr_default.items():
            print('{}: {}'.format(mesa_id, self.dic_id_mesa[mesa_id]), end=' ')
            if mesa_id in self.dic_mid_xypr_specified:
                print(self.dic_mid_xypr_specified[mesa_id])
            else:
                print('(Default)', xpyp)
                self.dic_mid_xypr_specified[mesa_id] = xpyp

        while True:
            print('X Y <mesa_id | c> [<mesa_id | c> ...] ')
            X, Y, *mesa_ids = input().split()
            x_off = self.dX * (int(X) - 1)
            y_off = self.dY * (int(Y) - 1)

            for mesa_id in mesa_ids:
                if mesa_id == 'c':
                    self.safe_move('H', -x_off, -y_off)
                elif int(mesa_id) in self.dic_mid_xypr_specified:
                    mesa_id = int(mesa_id)
                    print(self.dic_id_mesa[mesa_id])
                    x, y = self.dic_mid_xypr_specified[mesa_id]
                    x += x_off
                    y += y_off
                    self.safe_move('H', -x, -y)
                else:
                    print('Not found ', mesa_id)


if __name__ == '__main__':
    import visa

    debug_mode = False
    sample = 'dummy_sample'

    if debug_mode:
        suss = PA300Setup(sample, **c.mysql_config)
    else:
        rm = visa.ResourceManager()
        print(rm.list_resources())
        suss_rsrc = rm.open_resource('GPIB0::7::INSTR')
        suss = PA300Setup(sample, suss_rsrc, **c.mysql_config)

    suss.check_xm_ym_probe()
