using System;
using System.Linq;
using static Instr.Functions;

namespace Instr
{
    public class Agilent4156C : VisaCommunicator
    {
        bool useUSCommands;

        public Agilent4156C(string visaResource, bool useUSCommands) : base(visaResource)
        {
            this.useUSCommands = useUSCommands;
        }

        public void ContactTest(double timeInterval, double timeEnd)
        {
            Write("*RST");
            if (useUSCommands)
                throw new NotImplementedException();
            else
                Write(":PAGE:CHAN:MODE SAMP;"); // not in GPIB mannual damn

            DisableAllUnits(1, 3);
            ConfugureSmu(1, 3, 3);
            ConfugureSmu(3, 1, 3);

            Write(":PAGE:MEAS:SAMP:IINT 50e-3;POIN 1201;");
            Write(":PAGE:MEAS:SAMP:CONS:SMU3 1e-3;");
            Write(":PAGE:MEAS:SAMP:CONS:SMU3:COMP 10e-3;");


            Write(":PAGE:DISP:SET:GRAP:X:MIN 0;");
            Write(":PAGE:DISP:SET:GRAP:X:MAX 60;");
            Write(":PAGE:DISP:SET:GRAP:Y1:MIN 3e-5;");
            Write(":PAGE:DISP:SET:GRAP:Y1:MAX 4e-5;");
            Write(":PAGE:DISP:GRAP:Y2:NAME 'I3';");
            Write(":PAGE:DISP:GRAP:Y2:SCAL LOG;");
            Write(":PAGE:DISP:SET:GRAP:Y2:MIN 1e-12;"); // 1 Gohm at 1mV
            Write(":PAGE:DISP:SET:GRAP:Y2:MAX 100e-6;"); // 10 ohm at 1mV

            string initTime = GetTime(); // 2015/07/06 20:13:08
            Write(":PAGE:MEAS:MSET:ITIM MED;");
            Write(":PAGE:SCON:SING");


            Query("*OPC?");
            string t = Query(":FORM:DATA ASC;:DATA? '@TIME';");
            string i = Query(":FORM:DATA ASC;:DATA? 'I3';");
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

        public void SweepMeasurement(double endV,
            double stepV, double compI, int groundSMU, int sweepSMU,
            double yMax)
        {
            // Hard code
            string VStr, IStr, filePath, writeStr;
            double[][] VI;
            bool abort;
            Write("*RST");

            // Channel settings ////////////////////////////////////////////////
            // TODO: Integration time, Hold time, Deley time
            DisableAllUnits(groundSMU, sweepSMU);
            ConfugureSmu(groundSMU, 3, 3);
            ConfugureSmu(sweepSMU, 1, 1);

            // Measurement setup ///////////////////////////////////////////////
            Write(":PAGE:MEAS:SWE:VAR1:STAR 0");
            Write(":PAGE:MEAS:VAR1:STOP 0.1;");
            Write(":PAGE:CHAN:UFUN:DEF 'ABSI','A','ABS(I" + sweepSMU + ")'");
            Write("PAGE:DISP:GRAP:Y2:NAME 'ABSI'");
            // Without below line, error on :PAGE:DISP:SET:GRAP:Y1
            Write(":PAGE:MEAS:VAR1:STEP " + stepV + ";");
            Write(":PAGE:MEAS:VAR1:MODE DOUB;");
            // TODO: move to another place
            Write(":PAGE:DISP:SET:GRAP:Y1:MIN " + -yMax);
            Write(":PAGE:DISP:SET:GRAP:Y1:MAX " + yMax);
            Write(":PAGE:DISP:GRAP:Y2:SCAL LOG");
            Write(":PAGE:DISP:SET:GRAP:Y2:MIN 10e-13");
            Write(":PAGE:DISP:SET:GRAP:Y2:MAX 1e-3"); // on 4156C: dec/grid

            foreach (double v in AlternativeRange(0.1, 0.1, endV)) // 100mV step
            {
                // Measure setup ///////////////////////////////////////////////
                Write(":PAGE:DISP:SET:GRAP:X:MIN " + -Math.Abs(v));
                Write(":PAGE:DISP:SET:GRAP:X:MAX " + Math.Abs(v));
                // Measure /////////////////////////////////////////////////////
                Write(":PAGE:MEAS:SWE:VAR1:STOP " + v);
                string initTime = GetTime(); // 2015/07/06 20:13:08
                Write(":PAGE:SCON:MEAS:APP");
                //dmm.WriteString(":PAGE:SCON:MEAS:SING");
                //dmm.WriteString(":PAGE:SCON:MEAS:STOP");
                Query("*OPC?");
                // Acuire and save data ////////////////////////////////////////
                //dmm.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                VStr = Query(":FORM:DATA ASC;:DATA? 'V" + sweepSMU + "';");
                IStr = Query(":FORM:DATA ASC;:DATA? 'I" + sweepSMU + "';");

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
            DisableAllUnits(1, 2);
            return;
        }



        /// <summary>
        /// Get a response of "SYST:ERR?" command.
        /// </summary>
        /// <returns></returns>
        private string ErrorQ()
        {
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                return Query("SYST:ERR?");
            }
        }

        /// <summary>
        /// Disable all units. if parameter "exceptUnits" is given, corresponding units
        /// (1: SMU1, 2: SMU2, 3: SMU3, 4: SMU4, 5: VSU1, 6: VSU2, 7: VMU1, 8: VMU2)
        /// are not disabled.
        /// </summary>
        /// <param name="exceptUnits">Numbers less than 1 or grater than 8 are ignored.</param>
        /// <example>
        /// DisableAllUnits(false, 1, 3, 6) disables SMU1, SMU2, SMU4, VSU1, VMU1 and VMU2.
        /// </example>
        private void DisableAllUnits(params int[] exceptUnits)
        {
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                string[] units = new[] { null, "SMU1", "SMU2", "SMU3", "SMU4", "VSU1", "VSU2", "VMU1", "VMU2" };
                for (int i = 1; i <= 8; i++)
                {
                    if (exceptUnits.Contains(i)) continue;
                    Write(":PAGE:CHAN:" + units[i] + ":DIS");
                }
            }
        }

        /// <summary>
        /// Implimenting.
        /// </summary>
        /// <param name="useUSCommands"></param>
        /// <param name="SmuNumber">1, 2, 3, or 4</param>
        /// <param name="mode">1: V, 2: I, 3: common</param>
        /// <param name="func">1: VAR1, 2: VAR2, 3: CONSTANT, 4: VAR1'</param>
        /// <param name="VName">default: "V#SMU"</param>
        /// <param name="IName">default: "I#SMU"</param>
        private void ConfugureSmu(int SmuNumber, int mode, int func, string VName = null, string IName = null)
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
                Write(writeStr);
            }
        }

    }
}
