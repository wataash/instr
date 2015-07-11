using System;
using static Instr.Functions;

namespace Instr
{
    public static class Agilent4156C
    {
        private static string ErrorQ(IVisaCommunicator visa)
        {
            return visa.Query("SYST:ERR?");
        }

        public static void ContactTest(IVisaCommunicator visa, double timeInterval,
            double timeEnd)
        {
            visa.Write("*RST");
            visa.Write(":PAGE:CHAN:MODE SAMP;"); // not in GPIB mannual damn

            foreach (string unit in new[] { "SMU1", "SMU2", "SMU3", "SMU4",
                                         "VSU1", "VSU2", "VMU1", "VMU2" })
            {
                visa.Write(":PAGE:CHAN:" + unit + ":DIS");
            }
            visa.Write(
                ":PAGE:CHAN:SMU1:VNAM 'V1';" +
                ":PAGE:CHAN:SMU1:INAM 'I1';" +
                ":PAGE:CHAN:SMU1:MODE COMM;FUNC CONS;" +
                ":PAGE:CHAN:SMU3:VNAM 'V3';" +
                ":PAGE:CHAN:SMU3:INAM 'I3';" +
                ":PAGE:CHAN:SMU3:MODE V;FUNC CONS;"
                );

            visa.Write(":PAGE:MEAS:SAMP:IINT 50e-3;POIN 1201;");
            visa.Write(":PAGE:MEAS:SAMP:CONS:SMU3 1e-3;");
            visa.Write(":PAGE:MEAS:SAMP:CONS:SMU3:COMP 10e-3;");


            visa.Write(":PAGE:DISP:SET:GRAP:X:MIN 0;");
            visa.Write(":PAGE:DISP:SET:GRAP:X:MAX 60;");
            visa.Write(":PAGE:DISP:SET:GRAP:Y1:MIN 3e-5;");
            visa.Write(":PAGE:DISP:SET:GRAP:Y1:MAX 4e-5;");
            visa.Write(":PAGE:DISP:GRAP:Y2:NAME 'I3';");
            visa.Write(":PAGE:DISP:GRAP:Y2:SCAL LOG;");
            visa.Write(":PAGE:DISP:SET:GRAP:Y2:MIN 1e-12;"); // 1 Gohm at 1mV
            visa.Write(":PAGE:DISP:SET:GRAP:Y2:MAX 100e-6;"); // 10 ohm at 1mV

            string initTime = GetTime(); // 2015/07/06 20:13:08
            visa.Write(":PAGE:MEAS:MSET:ITIM MED;");
            visa.Write(":PAGE:SCON:SING");


            visa.Query("*OPC?");
            string t = visa.Query(":FORM:DATA ASC;:DATA? '@TIME';");
            string i = visa.Query(":FORM:DATA ASC;:DATA? 'I3';");
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

        public static void SweepMeasurement(IVisaCommunicator visa, double endV,
            double stepV, double compI, int groundSMU, int sweepSMU,
            double yMax)
        {
            // Hard code
            string VStr, IStr, filePath, writeStr;
            double[][] VI;
            bool abort;
            visa.Write("*RST");

            // Channel settings ////////////////////////////////////////////////
            // TODO: Integration time, Hold time, Deley time
            // Disable all units
            foreach (string unit in new[] { "SMU1", "SMU2", "SMU3", "SMU4",
                                         "VSU1", "VSU2", "VMU1", "VMU2" })
            {
                visa.Write(":PAGE:CHAN:" + unit + ":DIS");
            }
            visa.Write(
                ":PAGE:CHAN:SMU" + groundSMU + ":VNAM 'V" + groundSMU + "';" +
                ":PAGE:CHAN:SMU" + groundSMU + ":INAM 'I" + groundSMU + "';" +
                ":PAGE:CHAN:SMU" + groundSMU + ":MODE COMM;FUNC CONS;" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":VNAM 'V" + sweepSMU + "';" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":INAM 'I" + sweepSMU + "';" +
                ":PAGE:CHAN:SMU" + sweepSMU + ":MODE V;FUNC VAR1;");

            // Measurement setup ///////////////////////////////////////////////
            visa.Write(":PAGE:MEAS:SWE:VAR1:STAR 0");
            visa.Write(":PAGE:MEAS:VAR1:STOP 0.1;");
            visa.Write(":PAGE:CHAN:UFUN:DEF 'ABSI','A','ABS(I" + sweepSMU + ")'");
            visa.Write("PAGE:DISP:GRAP:Y2:NAME 'ABSI'");
            // Without below line, error on :PAGE:DISP:SET:GRAP:Y1
            visa.Write(":PAGE:MEAS:VAR1:STEP " + stepV + ";");
            visa.Write(":PAGE:MEAS:VAR1:MODE DOUB;");
            // TODO: move to another place
            visa.Write(":PAGE:DISP:SET:GRAP:Y1:MIN " + -yMax);
            visa.Write(":PAGE:DISP:SET:GRAP:Y1:MAX " + yMax);
            visa.Write(":PAGE:DISP:GRAP:Y2:SCAL LOG");
            visa.Write(":PAGE:DISP:SET:GRAP:Y2:MIN 10e-13");
            visa.Write(":PAGE:DISP:SET:GRAP:Y2:MAX 1e-3"); // on 4156C: dec/grid

            foreach (double v in AlternativeRange(0.1, 0.1, endV)) // 100mV step
            {
                // Measure setup ///////////////////////////////////////////////
                visa.Write(":PAGE:DISP:SET:GRAP:X:MIN " + -Math.Abs(v));
                visa.Write(":PAGE:DISP:SET:GRAP:X:MAX " + Math.Abs(v));
                // Measure /////////////////////////////////////////////////////
                visa.Write(":PAGE:MEAS:SWE:VAR1:STOP " + v);
                string initTime = GetTime(); // 2015/07/06 20:13:08
                visa.Write(":PAGE:SCON:MEAS:APP");
                //dmm.WriteString(":PAGE:SCON:MEAS:SING");
                //dmm.WriteString(":PAGE:SCON:MEAS:STOP");
                visa.Query("*OPC?");
                // Acuire and save data ////////////////////////////////////////
                //dmm.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                VStr = visa.Query(":FORM:DATA ASC;:DATA? 'V" + sweepSMU + "';");
                IStr = visa.Query(":FORM:DATA ASC;:DATA? 'I" + sweepSMU + "';");

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
