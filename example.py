import visa

from lib.agilent4156c import Agilent4156C
from lib.suss_pa300 import SussPA300

agi_visa_rsrc_name = 'GPIB0::18::INSTR'
agi_visa_timeout_sec = 600  # 10min
suss_visa_rsrc_name = 'GPIB0::7::INSTR'
suss_visa_timeout_sec = 10

# Initialize
rm = visa.ResourceManager()
print(rm.list_resources())

a_resource = rm.open_resource(agi_visa_rsrc_name)
print(a_resource.query('*IDN?'))
a = Agilent4156C(a_resource, agi_visa_timeout_sec, False)
print(a.q('*IDN?'))

s_resource = rm.open_resource(suss_visa_rsrc_name)
s = SussPA300(rm.open_resource(suss_visa_rsrc_name), suss_visa_timeout_sec, False)

# Measurement
Vs, Is = a.double_sweep_from_zero(1, 2, 0.1, 1e-6)
print(Vs, Is)

