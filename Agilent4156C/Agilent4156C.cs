using System;
using System.Linq;
using static Instr.Functions;

namespace Instr
{
    public static class Agilent4156C
    {
        public static void ContactTest(IVisaCommunicator visa, double timeInterval,
            double timeEnd)
        {
            visa.Write("*RST");
            visa.Write(":PAGE:CHAN:MODE SAMP;"); // not in GPIB mannual damn

            DisableAllUnits(visa, false, 1, 3);
            ConfugureSmu(visa, false, 1, 3, 3);
            ConfugureSmu(visa, false, 3, 1, 3);

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
            DisableAllUnits(visa, false, groundSMU, sweepSMU);
            ConfugureSmu(visa, false, groundSMU, 3, 3);
            ConfugureSmu(visa, false, sweepSMU, 1, 1);

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
            DisableAllUnits(visa, false, 1, 2);
            return;
        }



        /// <summary>
        /// Get a response of "SYST:ERR?" command.
        /// </summary>
        /// <param name="visa"></param>
        /// <param name="useUSCommands"></param>
        /// <returns></returns>
        private static string ErrorQ(IVisaCommunicator visa, bool useUSCommands)
        {
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                return visa.Query("SYST:ERR?");
            }
        }

        /// <summary>
        /// Disable all units. if parameter "exceptUnits" is given, corresponding units
        /// (1: SMU1, 2: SMU2, 3: SMU3, 4: SMU4, 5: VSU1, 6: VSU2, 7: VMU1, 8: VMU2)
        /// are not disabled.
        /// </summary>
        /// <param name="visa"></param>
        /// <param name="useUSCommands"></param>
        /// <param name="exceptUnits">Numbers less than 1 or grater than 8 are ignored.</param>
        /// <example>
        /// DisableAllUnits(visa, false, 1, 3, 6) disables SMU1, SMU2, SMU4, VSU1, VMU1 and VMU2.
        /// </example>
        private static void DisableAllUnits(IVisaCommunicator visa, bool useUSCommands, params int[] exceptUnits)
        {
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                string[] units = new[] { "SMU1", "SMU2", "SMU3", "SMU4", "VSU1", "VSU2", "VMU1", "VMU2" };
                for (int i = 1; i <= 8; i++)
                {
                    if (exceptUnits.Contains(i)) continue;
                    visa.Write(":PAGE:CHAN:" + units[i] + ":DIS");
                }
            }
        }

        /// <summary>
        /// Implimenting.
        /// </summary>
        /// <param name="visa"></param>
        /// <param name="useUSCommands"></param>
        /// <param name="SmuNumber">1, 2, 3, or 4</param>
        /// <param name="mode">1: V, 2: I, 3: common</param>
        /// <param name="func">1: VAR1, 2: VAR2, 3: CONSTANT, 4: VAR1'</param>
        /// <param name="VName">default: "V#SMU"</param>
        /// <param name="IName">default: "I#SMU"</param>
        private static void ConfugureSmu(IVisaCommunicator visa, bool useUSCommands,
            int SmuNumber, int mode, int func, string VName = null, string IName = null)
        {
            if (VName == null) VName = "V" + SmuNumber;
            if (IName == null) IName = "I" + SmuNumber;
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                if (mode == 0 | func == 0) throw new ArgumentOutOfRangeException(); // if negative value or larger value,
                string modeStr = new string[] { null, "V", "I", "COMM" }[mode]; // these code will throw exceptions.
                string funcStr = new string[] { null, "VAR1", "VAR2", "CONS", "VARD" }[func]; // (not tested)
                string writeStr = $":PAGE:CHAN:SMU{SmuNumber}:VNAM '{VName}';INAM '{IName}';MODE {modeStr};FUNC {funcStr};";
                visa.Write(writeStr);
            }
        }

    }
}
