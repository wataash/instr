import visa

from lib.agilent4156c import Agilent4156C

agi_visa_rsrc_name = 'GPIB0::18::INSTR'
agi_visa_timeout_sec = 600  # 10min

# Initialize
rm = visa.ResourceManager()
print(rm.list_resources())

a_rsrc = rm.open_resource(agi_visa_rsrc_name)
a = Agilent4156C(a_rsrc, agi_visa_timeout_sec, False)

# Measure
a.contact_test(2, 1, 20e-3)
