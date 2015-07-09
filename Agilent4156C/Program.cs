using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using Ivi.Visa.Interop;

namespace Automation.Suss100
{
    public static class Agilent4156C
    {

        [STAThread]
        static void Main()
        {
            string VISAResource = "GPIB0::18::INSTR";
            // Agilent
            var RM = new ResourceManager();
            var DMM = new FormattedIO488();
            DMM.IO = (IMessage)RM.Open(VISAResource);

            try
            {
                DMM.IO.Timeout = (int)10 * 60 * 1000; // 10min in [ms]
                SweepMeasurement(DMM, 500e-3, .1e-3, 10e-3, 1, 3, 10e-6);
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
        /// </summary>
        /// <param name="data"></param>
        /// <example>
        /// <code>
        /// Write2DimDouble(
        ///     new[] { new[] { 1.0, 2, }, new[] { 3.0, 4 } });
        /// returns "1,2\n3,4"
        /// </code>
        /// </example>
        public static string TwoDimDouble2String(double[][] data)
        {
            string joined = "";
            foreach (double[] item in data)
            {
                joined += String.Join(",", item) + "\n";
            }
            return joined;
        }

        /// <summary>
        /// </summary>
        /// <returns>Example: "2015-07-06_20-13-08"</returns>
        /// <remarks>Verified only in Japanese locale.</remarks>
        public static string GetTime()
        {
            string t = DateTime.Now.ToString();
            // 2015/07/06 20:13:08 --> 2015-07-06_20-13-08
            return t.Replace(":", "-").Replace("/", "-").Replace(" ", "_");
        }

        /// <summary>
        /// CommaStringToDoubleArray("1,2,3e3") --> {1.0, 2.0, 3000.0}
        /// </summary>
        /// <param name="s"></param>
        /// <returns></returns>
        public static double[] CommaStringToDoubleArray(string s)
        {
            return Array.ConvertAll(s.Split(','), Double.Parse);
        }

        /// <summary>
        /// </summary>
        /// <param name="start"></param>
        /// <param name="delta"></param>
        /// <param name="end"></param>
        /// <returns></returns>
        /// <example>
        /// AlternativeRange(1.00, 0.11, 1.55)
        /// returns {1.00, -1.00, 1.11, -1.11, 1.22, -1.22}
        /// </example>
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

        /// <summary>
        /// Grater than 1e10: Infinite.
        /// </summary>
        /// <param name="in1"></param>
        /// <param name="in2"></param>
        /// <param name="o"></param>
        /// <returns></returns>
        /// <example>
        /// double[][] o;
        /// ZipDetectInf(new[] { 1, 1e20, 3 }, new[] { 1.1, 3.3, 800 }, out o);
        /// returns true (1e20 > 1e10), o = new[][] {{1.0, 1.1}, {3.0, 800.0}}
        /// </example>
        public static bool ZipDetectInf(double[] in1, double[] in2, out double[][] o)
        {
            bool detectInfinity = false;
            IEnumerable<double[]> zipped = in1.Zip(in2, (a, b) => new[] { a, b });
            var zipInfRemoved = new List<double[]>();
            foreach (double[] pair in zipped)
            {
                if (pair[0] > 1e10 || pair[1] > 1e10)
                    detectInfinity = true;
                else
                    zipInfRemoved.Add(pair);
            }
            o = zipInfRemoved.ToArray();
            return detectInfinity;
        }
    }
}