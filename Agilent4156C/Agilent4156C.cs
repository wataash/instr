using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using Ivi.Visa.Interop;


namespace Instr
{
    public static class Agilent4156C
    {
        [STAThread]
        static void Main()
        {
            ChannelSetup(1,2);
            string VISAResource = "GPIB0::18::INSTR";
            // Agilent
            var RM = new ResourceManager();
            var DMM = new FormattedIO488();
            DMM.IO = (IMessage)RM.Open(VISAResource);

            try
            {
                DMM.IO.Timeout = (int)10 * 60 * 1000; // 10min in [ms]
                //SweepMeasurement(DMM, 500e-3, .1e-3, 10e-3, 1, 3, 10e-6);
                ContactTest(DMM, 100e-3, 20);
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
                ":PAGE:CHAN:SMU3:MODE V;FUNC VAR1;");
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

            foreach (double v in F.AlternativeRange(0.1, 0.1, endV)) // 100mV step
            {
                // Measure setup ///////////////////////////////////////////////
                DMM.WriteString(":PAGE:DISP:SET:GRAP:X:MIN " + -Math.Abs(v));
                DMM.WriteString(":PAGE:DISP:SET:GRAP:X:MAX " + Math.Abs(v));
                // Measure /////////////////////////////////////////////////////
                DMM.WriteString(":PAGE:MEAS:SWE:VAR1:STOP " + v);
                string initTime = F.GetTime(); // 2015/07/06 20:13:08
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

                abort = F.ZipDetectInf(F.CommaStringToDoubleArray(VStr),
                    F.CommaStringToDoubleArray(IStr), out VI);
                writeStr = F.TwoDimDouble2String(VI);
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

    class VisaCommunicator
    {

    }
}
