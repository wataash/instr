using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using Ivi.Visa.Interop;

namespace Agilent4156C
{
    public static class Program
    {
        /// <summary>
        /// アプリケーションのメイン エントリ ポイントです。
        /// </summary>
        [STAThread]
        static void Main()
        {
    //        System.IO.File.WriteAllText(
    //System.Environment.ExpandEnvironmentVariables("%temp%") +
    //"\\" + "test.ttxt", "aaa"
    //);
            string VISAResource = "GPIB0::18::INSTR";
            // Agilent
            var RM = new ResourceManager();
            var DMM = new FormattedIO488();
            DMM.IO = (IMessage)RM.Open(VISAResource);

            try
            {
                DMM.IO.Timeout = (int)10 * 60 * 1000; // 10min in [ms]
                SweepMeasurement(DMM, 200e-3, 10e-3, 10e-3, 1, 3);
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

        public static List<string> SweepMeasurement(FormattedIO488 DMM, double endV,
          double stepV, double compI, int groundSMU, int sweepSMU)
        {
            // Hard code
            var timeStamps = new List<string>();
            var voltages = new List<string>();
            var currents = new List<string>();
            DMM.WriteString("*RST");

            // Channel settings
            // TODO: Integration time, Hold time, Deley time
            // Disable all units
            foreach (string s in new[] { "SMU1", "SMU2", "SMU3", "SMU4",
                                         "VSU1", "VSU2", "VMU1", "VMU2" })
            {
                DMM.WriteString(":PAGE:CHAN:" + s + ":DIS");
            }
            DMM.WriteString(
                ":PAGE:CHAN:SMU" + groundSMU + ":VNAM 'V" + groundSMU + "';" +
                ":PAGE:CHAN:SMU" + groundSMU + ":INAM 'I" + groundSMU + "';" +
                ":PAGE:CHAN:SMU" + groundSMU + ":MODE COMM;FUNC CONS;" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":VNAM 'V" + sweepSMU + "';" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":INAM 'I" + sweepSMU + "';" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":MODE V;FUNC VAR1;");

            // Measurement setup
            DMM.WriteString(":PAGE:MEAS:SWE:VAR1:STAR 0");
            DMM.WriteString(":PAGE:MEAS:VAR1:STEP " + stepV + ";");
            DMM.WriteString(":PAGE:MEAS:VAR1:MODE DOUB;");
            DMM.WriteString(":PAGE:DISP:SET:GRAP:Y1:MIN " + -1e-12); // TODO: move to other code
            DMM.WriteString(":PAGE:DISP:SET:GRAP:Y1:MAX " + 1e-12); // TODO: move to other code

            //foreach (var item in collection)
            foreach (double v in AlternativeRange(0.1, 0.1, endV)) // 100mV step
            {
                // Measure setup
                DMM.WriteString(":PAGE:DISP:SET:GRAP:X:MIN " + -Math.Abs(v));
                DMM.WriteString(":PAGE:DISP:SET:GRAP:X:MAX " + Math.Abs(v));
                // Measure
                DMM.WriteString(":PAGE:MEAS:SWE:VAR1:STOP " + v);
                string initTime = DateTime.Now.ToString(); // 2015/07/06 20:13:08
                initTime = initTime.Replace(":", "-");
                initTime = initTime.Replace("/", "-");
                initTime = initTime.Replace(" ", "_"); // 2015-07-06_20-13-08
                DMM.WriteString(":PAGE:SCON:MEAS:APP");
                //DMM.WriteString(":PAGE:SCON:MEAS:SING");
                //DMM.WriteString(":PAGE:SCON:MEAS:STOP");
                DMM.WriteString("*OPC?");
                DMM.ReadString();
                //DMM.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                DMM.WriteString(":FORM:DATA ASC;:DATA? 'V" + sweepSMU + "';");
                voltages.Add(DMM.ReadString());
                //DMM.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'I2';");
                DMM.WriteString(":FORM:DATA ASC;:DATA? 'I" + sweepSMU + "';");
                currents.Add(DMM.ReadString());
                // break if (V/deltaV + 1 != points);
                System.IO.File.WriteAllText(
                    System.Environment.ExpandEnvironmentVariables("%temp%") +
                    "\\" + initTime + ".txt",
                    currents.Last());

                //System.IO.File.Write
            }
            return voltages;
        }

        public static double[] AlternativeRange(double start, double delta, double end)
        {
            // TODO: smart way using LINQ?
            var res = new List<double>();
            double append = start;
            while (append <= end)
            {
                res.Add(append);
                res.Add(-append);
                append += delta;
            }
            return res.ToArray();
        }

    }
}