using System;
using System.Collections.Generic;
using Ivi.Visa.Interop;
using static Instr.Functions;

namespace Instr
{
    public static class Agilent4156C
    {
        [STAThread]
        static void Main()
        {
            string VISAResource = "GPIB0::18::INSTR";
            // Agilent
            var rm = new ResourceManager();
            var dmm = new FormattedIO488();
            dmm.IO = (IMessage)rm.Open(VISAResource);

            try
            {
                dmm.IO.Timeout = (int)10 * 60 * 1000; // 10min in [ms]
                SweepMeasurement(dmm, 500e-3, .5e-3, 1e-3, 1, 3, 1e-6);
                //ContactTest(dmm, 100e-3, 20);
            }
            finally
            {
                dmm.IO.Close();
                System.Runtime.InteropServices.Marshal.ReleaseComObject(dmm);
                System.Runtime.InteropServices.Marshal.ReleaseComObject(rm);
            }
        }

        private static string ErrorQ(IVisaCommunicator visa)
        {
            return visa.Query("SYST:ERR?");
        }

        public static void ContactTest(FormattedIO488 io, double timeInterval,
            double timeEnd)
        {
            io.WriteString("*RST");
            io.WriteString(":PAGE:CHAN:MODE SAMP;"); // not in GPIB mannual damn

            foreach (string unit in new[] { "SMU1", "SMU2", "SMU3", "SMU4",
                                         "VSU1", "VSU2", "VMU1", "VMU2" })
            {
                io.WriteString(":PAGE:CHAN:" + unit + ":DIS");
            }
            io.WriteString(
                ":PAGE:CHAN:SMU1:VNAM 'V1';" +
                ":PAGE:CHAN:SMU1:INAM 'I1';" +
                ":PAGE:CHAN:SMU1:MODE COMM;FUNC CONS;" +
                ":PAGE:CHAN:SMU3:VNAM 'V3';" +
                ":PAGE:CHAN:SMU3:INAM 'I3';" +
                ":PAGE:CHAN:SMU3:MODE V;FUNC CONS;"
                );

            io.WriteString(":PAGE:MEAS:SAMP:IINT 50e-3;POIN 1201;");
            io.WriteString(":PAGE:MEAS:SAMP:CONS:SMU3 1e-3;");
            io.WriteString(":PAGE:MEAS:SAMP:CONS:SMU3:COMP 10e-3;");


            io.WriteString(":PAGE:DISP:SET:GRAP:X:MIN 0;");
            io.WriteString(":PAGE:DISP:SET:GRAP:X:MAX 60;");
            io.WriteString(":PAGE:DISP:SET:GRAP:Y1:MIN 3e-5;");
            io.WriteString(":PAGE:DISP:SET:GRAP:Y1:MAX 4e-5;");
            io.WriteString(":PAGE:DISP:GRAP:Y2:NAME 'I3';");
            io.WriteString(":PAGE:DISP:GRAP:Y2:SCAL LOG;");
            io.WriteString(":PAGE:DISP:SET:GRAP:Y2:MIN 1e-12;"); // 1 Gohm at 1mV
            io.WriteString(":PAGE:DISP:SET:GRAP:Y2:MAX 100e-6;"); // 10 ohm at 1mV

            string initTime = GetTime(); // 2015/07/06 20:13:08
            io.WriteString(":PAGE:MEAS:MSET:ITIM MED;");
            io.WriteString(":PAGE:SCON:SING");


            io.WriteString("*OPC?");
            io.ReadString();
            io.WriteString(":FORM:DATA ASC;:DATA? '@TIME';");
            string t = io.ReadString();
            io.WriteString(":FORM:DATA ASC;:DATA? 'I3';");
            string i = io.ReadString();
            double[][] dat;
            ZipDetectInf(CommaStringToDoubleArray(t),
                CommaStringToDoubleArray(i), out dat);
            string writeStr = TwoDimDouble2String(dat);
            writeStr = initTime + "\nt,I\n" + writeStr;
            string filePath = Environment.ExpandEnvironmentVariables("%temp%") +
                "\\" + initTime + ".txt";
            System.IO.File.WriteAllText(filePath, writeStr);
            filePath = Environment.ExpandEnvironmentVariables("%temp%") +
                "\\last.txt";
            System.IO.File.WriteAllText(filePath, writeStr);
        }

        public static void SweepMeasurement(FormattedIO488 io, double endV,
            double stepV, double compI, int groundSMU, int sweepSMU,
            double yMax)
        {
            // Hard code
            string VStr, IStr, filePath, writeStr;
            double[][] VI;
            bool abort;
            var timeStamps = new List<string>();
            var voltages = new List<string>();
            var currents = new List<string>();
            io.WriteString("*RST");

            // Channel settings ////////////////////////////////////////////////
            // TODO: Integration time, Hold time, Deley time
            // Disable all units
            foreach (string unit in new[] { "SMU1", "SMU2", "SMU3", "SMU4",
                                         "VSU1", "VSU2", "VMU1", "VMU2" })
            {
                io.WriteString(":PAGE:CHAN:" + unit + ":DIS");
            }
            io.WriteString(
                ":PAGE:CHAN:SMU" + groundSMU + ":VNAM 'V" + groundSMU + "';" +
                ":PAGE:CHAN:SMU" + groundSMU + ":INAM 'I" + groundSMU + "';" +
                ":PAGE:CHAN:SMU" + groundSMU + ":MODE COMM;FUNC CONS;" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":VNAM 'V" + sweepSMU + "';" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":INAM 'I" + sweepSMU + "';" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":MODE V;FUNC VAR1;");

            // Measurement setup ///////////////////////////////////////////////
            io.WriteString(":PAGE:MEAS:SWE:VAR1:STAR 0");
            io.WriteString(":PAGE:MEAS:VAR1:STOP 0.1;");
            io.WriteString(":PAGE:CHAN:UFUN:DEF 'ABSI','A','ABS(I" + sweepSMU + ")'");
            io.WriteString("PAGE:DISP:GRAP:Y2:NAME 'ABSI'");
            // Without below line, error on :PAGE:DISP:SET:GRAP:Y1
            io.WriteString(":PAGE:MEAS:VAR1:STEP " + stepV + ";");
            io.WriteString(":PAGE:MEAS:VAR1:MODE DOUB;");
            // TODO: move to another place
            io.WriteString(":PAGE:DISP:SET:GRAP:Y1:MIN " + -yMax);
            io.WriteString(":PAGE:DISP:SET:GRAP:Y1:MAX " + yMax);
            io.WriteString(":PAGE:DISP:GRAP:Y2:SCAL LOG");
            io.WriteString(":PAGE:DISP:SET:GRAP:Y2:MIN 10e-13");
            io.WriteString(":PAGE:DISP:SET:GRAP:Y2:MAX 1e-3"); // on 4156C: dec/grid

            foreach (double v in AlternativeRange(0.1, 0.1, endV)) // 100mV step
            {
                // Measure setup ///////////////////////////////////////////////
                io.WriteString(":PAGE:DISP:SET:GRAP:X:MIN " + -Math.Abs(v));
                io.WriteString(":PAGE:DISP:SET:GRAP:X:MAX " + Math.Abs(v));
                // Measure /////////////////////////////////////////////////////
                io.WriteString(":PAGE:MEAS:SWE:VAR1:STOP " + v);
                string initTime = GetTime(); // 2015/07/06 20:13:08
                io.WriteString(":PAGE:SCON:MEAS:APP");
                //dmm.WriteString(":PAGE:SCON:MEAS:SING");
                //dmm.WriteString(":PAGE:SCON:MEAS:STOP");
                io.WriteString("*OPC?");
                io.ReadString();
                // Acuire and save data ////////////////////////////////////////
                //dmm.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                io.WriteString(":FORM:DATA ASC;:DATA? 'V" + sweepSMU + "';");
                //voltages.Add(dmm.ReadString());
                VStr = io.ReadString();
                //dmm.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'I2';");
                io.WriteString(":FORM:DATA ASC;:DATA? 'I" + sweepSMU + "';");
                //currents.Add(dmm.ReadString());
                IStr = io.ReadString();

                abort = ZipDetectInf(CommaStringToDoubleArray(VStr),
                    CommaStringToDoubleArray(IStr), out VI);
                writeStr = TwoDimDouble2String(VI);
                writeStr = initTime + "\nV,I\n" + writeStr;
                filePath = Environment.ExpandEnvironmentVariables("%temp%") +
                    "\\" + initTime + ".txt";
                System.IO.File.WriteAllText(filePath, writeStr);
                filePath = Environment.ExpandEnvironmentVariables("%temp%") +
                    "\\last.txt";
                System.IO.File.WriteAllText(filePath, writeStr);
                if (abort) break; // Finish if "stop button" on 4156C pressed.
            }
            return;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="channels">
        /// 1: SMU1, 2: SMU2, 3: SMU3, 4: SMU4, 5: VSU1, 6: VSU2, 7: VMU1, 8: VMU2
        /// </param>
        /// <returns></returns>
        private static int ChannelSetup(params int[] channels)
        {

            // if elem in channels
            // TODO: enum, ChannelSetup in another proj.
            throw new NotImplementedException();
            return 0;

        }

    }
}
