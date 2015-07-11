using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using Ivi.Visa.Interop;
using static Instr.Function;


namespace Instr
{


    public static class Agilent4156C
    {
        [STAThread]
        static void Main()
        {
            var a = new AgilentVisaCommunicator("a");
            string VISAResource = "GPIB0::18::INSTR";
            // Agilent
            var RM = new ResourceManager();
            var DMM = new FormattedIO488();
            DMM.IO = (IMessage)RM.Open(VISAResource);
            WriteTest((s) => DMM.WriteString(s));

            try
            {
                DMM.IO.Timeout = (int)10 * 60 * 1000; // 10min in [ms]
                SweepMeasurement(DMM, 500e-3, .5e-3, 1e-3, 1, 3, 1e-6);
                //ContactTest(DMM, 100e-3, 20);
            }
            finally
            {
                DMM.IO.Close();
                System.Runtime.InteropServices.Marshal.ReleaseComObject(DMM);
                System.Runtime.InteropServices.Marshal.ReleaseComObject(RM);
            }
            //Application.EnableVisualStyles();
            //Application.SetCompatibleTextRenderingDefault(false);
            //Application.Run(new Form1());
        }

        private static int Placeholder(Action<string> write, Func<string, string> query) { return 0; }
        private static int ErrorQ(Action<string> write, Func<string, string> query)
        {
            string q;
            q = query("SYST:ERR?");
            return 0;
        }

        private static int WriteTest(Action<string> write)
        {
            write("*IDN?");
            return 0;
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

        public static void SweepMeasurement(FormattedIO488 DMM, double endV,
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
            DMM.WriteString("*RST");

            // Channel settings ////////////////////////////////////////////////
            // TODO: Integration time, Hold time, Deley time
            // Disable all units
            foreach (string unit in new[] { "SMU1", "SMU2", "SMU3", "SMU4",
                                         "VSU1", "VSU2", "VMU1", "VMU2" })
            {
                DMM.WriteString(":PAGE:CHAN:" + unit + ":DIS");
            }
            DMM.WriteString(
                ":PAGE:CHAN:SMU" + groundSMU + ":VNAM 'V" + groundSMU + "';" +
                ":PAGE:CHAN:SMU" + groundSMU + ":INAM 'I" + groundSMU + "';" +
                ":PAGE:CHAN:SMU" + groundSMU + ":MODE COMM;FUNC CONS;" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":VNAM 'V" + sweepSMU + "';" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":INAM 'I" + sweepSMU + "';" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":MODE V;FUNC VAR1;");

            // Measurement setup ///////////////////////////////////////////////
            DMM.WriteString(":PAGE:MEAS:SWE:VAR1:STAR 0");
            DMM.WriteString(":PAGE:MEAS:VAR1:STOP 0.1;");
            DMM.WriteString(":PAGE:CHAN:UFUN:DEF 'ABSI','A','ABS(I" + sweepSMU + ")'");
            DMM.WriteString("PAGE:DISP:GRAP:Y2:NAME 'ABSI'");
            // Without below line, error on :PAGE:DISP:SET:GRAP:Y1
            DMM.WriteString(":PAGE:MEAS:VAR1:STEP " + stepV + ";");
            DMM.WriteString(":PAGE:MEAS:VAR1:MODE DOUB;");
            // TODO: move to another place
            DMM.WriteString(":PAGE:DISP:SET:GRAP:Y1:MIN " + -yMax);
            DMM.WriteString(":PAGE:DISP:SET:GRAP:Y1:MAX " + yMax);
            DMM.WriteString(":PAGE:DISP:GRAP:Y2:SCAL LOG");
            DMM.WriteString(":PAGE:DISP:SET:GRAP:Y2:MIN 10e-13");
            DMM.WriteString(":PAGE:DISP:SET:GRAP:Y2:MAX 1e-3"); // on 4156C: dec/grid

            foreach (double v in AlternativeRange(0.1, 0.1, endV)) // 100mV step
            {
                // Measure setup ///////////////////////////////////////////////
                DMM.WriteString(":PAGE:DISP:SET:GRAP:X:MIN " + -Math.Abs(v));
                DMM.WriteString(":PAGE:DISP:SET:GRAP:X:MAX " + Math.Abs(v));
                // Measure /////////////////////////////////////////////////////
                DMM.WriteString(":PAGE:MEAS:SWE:VAR1:STOP " + v);
                string initTime = GetTime(); // 2015/07/06 20:13:08
                DMM.WriteString(":PAGE:SCON:MEAS:APP");
                //DMM.WriteString(":PAGE:SCON:MEAS:SING");
                //DMM.WriteString(":PAGE:SCON:MEAS:STOP");
                DMM.WriteString("*OPC?");
                DMM.ReadString();
                // Acuire and save data ////////////////////////////////////////
                //DMM.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                DMM.WriteString(":FORM:DATA ASC;:DATA? 'V" + sweepSMU + "';");
                //voltages.Add(DMM.ReadString());
                VStr = DMM.ReadString();
                //DMM.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'I2';");
                DMM.WriteString(":FORM:DATA ASC;:DATA? 'I" + sweepSMU + "';");
                //currents.Add(DMM.ReadString());
                IStr = DMM.ReadString();

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

