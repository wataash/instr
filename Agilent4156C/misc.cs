﻿using NationalInstruments.VisaNS;
enum SweepStaircaseType
{
    Linear, Log10, Log25, Log50
}

enum SweepMode
{
    Single, Double
}

namespace Instr
{
    public class misc
    {
        static void f()
        {
            string VISAResource = "GPIB0::18::INSTR";
            MessageBasedSession mbSession;
            mbSession = (MessageBasedSession)ResourceManager.
                GetLocalManager().Open(VISAResource);
            SweepMeasurement(mbSession, 500e-3, 1e-3, 10e-3, 1, 2);
            mbSession.Dispose();

            // Robust
            //try
            //{
            //    mbSession = (MessageBasedSession)ResourceManager.
            //        GetLocalManager().Open(VISAResource);
            //}
            //catch (InvalidCastException)
            //{
            //    MessageBox.
            //        Show("Resource selected must be a message-based session");
            //}
            //catch (Exception exp)
            //{
            //    //MessageBox.Show(exp.Message);
            //    Console.WriteLine(exp.Message);
            //}  
        }

        public static void SweepMeasurement(MessageBasedSession mbSession,
            double endV, double stepV, double compI, int groundSMU, int biasSMU)
        {
            // Hard code
            {
                // Channel settings
                mbSession.Write(
                    ":PAGE:CHAN:SMU1:VNAM 'V1';INAM 'I1';MODE COMM;FUNC CONS;");
                mbSession.Write(
                    ":PAGE:CHAN:SMU2:VNAM 'V2';INAM 'I2';MODE V;FUNC VAR1;");
                mbSession.Write(":PAGE:CHAN:SMU3:DIS");
                mbSession.Write(":PAGE:CHAN:SMU4:DIS");
                mbSession.Write(":PAGE:CHAN:VSU1:DIS");
                mbSession.Write(":PAGE:CHAN:VSU2:DIS");
                mbSession.Write(":PAGE:CHAN:VMU1:DIS");
                mbSession.Write(":PAGE:CHAN:VMU2:DIS");
            }
            // IntegTime();
            // hold delay time
            {
                // Measurement setup
                mbSession.Write(":PAGE:MEAS:SWE:VAR1:STAR 0");
                mbSession.Write(":PAGE:MEAS:VAR1:STEP " + stepV + ";");
            }
            // foreach 0, 0.1, ..., endV
            double v = 0.1;
            while (v <= endV)
            {
                // Measure
                string s;
                mbSession.Write(":PAGE:DISP:SET:GRAP:X:MIN " + -v);
                mbSession.Write(":PAGE:DISP:SET:GRAP:X:MAX " + v);
                // pos
                mbSession.Write(":PAGE:MEAS:SWE:VAR1:STOP " + v);
                mbSession.Write(":PAGE:SCON:MEAS:SING"); // SING以外にstop appがある
                s = mbSession.Query("*OPC?"); // TODO: extend timeout
                s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'I2';");
                // break if (V/deltaV + 1 != points);
                // nega
                mbSession.Write(":PAGE:MEAS:SWE:VAR1:STOP" + -v);
                mbSession.Write(":PAGE:SCON:MEAS:SING");
                s = mbSession.Query("*OPC?");
                s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'I2';");
                // break if (V/deltaV + 1 != points);
                v += 0.1;
            }
        }

    }
}
