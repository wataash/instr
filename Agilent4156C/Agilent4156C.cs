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

        public double[][] ContactTest(
            int groundSmu, int biasSmu,
            double timeInterval = 50e-3, int points = 10001,
            double voltage = 1e-3, double compliance = 10e-3)
        // TODO: order in the displayed order on 4156C
        {
            Write("*RST");
            if (useUSCommands)
                throw new NotImplementedException();
            else
                Write(":PAGE:CHAN:MODE SAMP;"); // not in GPIB mannual damn

            DisableAllUnits(groundSmu, biasSmu);
            ConfugureSmu(groundSmu, 3, 3);
            ConfugureSmu(biasSmu, 1, 3);

            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                Write($":PAGE:MEAS:SAMP:IINT {timeInterval};POIN {points};");
                Write($":PAGE:MEAS:SAMP:CONS:SMU{biasSmu} {voltage};");
                Write($":PAGE:MEAS:SAMP:CONS:SMU{biasSmu}:COMP {compliance};");
            }

            SetY2($"I{biasSmu}", true);
            ConfigureDisplay(0, 60, 3e-5, 4e-5, 1e-12, 100e-6); // 1 Gohm, 10 ohm at 1mV

            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                Write(":PAGE:MEAS:MSET:ITIM MED;");
                Write(":PAGE:SCON:SING");
            }

            Query("*OPC?");
            string times, currents;
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                times = Query(":FORM:DATA ASC;:DATA? '@TIME';");
                currents = Query($":FORM:DATA ASC;:DATA? 'I{biasSmu}';");
            }

            double[][] dat; // TODO: check has inf?
            ZipDetectInf(CommaStringToDoubleArray(times), CommaStringToDoubleArray(currents), out dat);
            return dat;
        }

        public double[][] DoubleSweepFromZero(
            int groundSMU, int sweepSMU,
            double endV,
            double stepV, double compI,
            double yLim, out bool aborted)
        {
            string VStr, IStr, filePath, writeStr;
            double[][] VI;

            Write("*RST");
            // TODO: Integration time, Hold time, Deley time
            DisableAllUnits(groundSMU, sweepSMU);
            ConfugureSmu(groundSMU, 3, 3);
            ConfugureSmu(sweepSMU, 1, 1);

            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                Write(":PAGE:MEAS:SWE:VAR1:STAR 0");
                Write($":PAGE:MEAS:VAR1:STOP {endV};");
                Write($":PAGE:CHAN:UFUN:DEF 'ABSI','A','ABS(I{sweepSMU})'");
                Write($"PAGE:DISP:GRAP:Y2:NAME 'ABSI'");
                // Without below line, error on :PAGE:DISP:SET:GRAP:Y1
                Write($":PAGE:MEAS:VAR1:STEP {stepV};");
                Write(":PAGE:MEAS:VAR1:MODE DOUB;");
            }

            ConfigureDisplay(Math.Min(0, endV), Math.Max(0, endV),
                Math.Min(0, yLim), Math.Max(0, yLim));
            SetY2($"I{sweepSMU}", true);

            Write(":PAGE:SCON:MEAS:SING");
            //dmm.WriteString(":PAGE:SCON:MEAS:APP");
            //dmm.WriteString(":PAGE:SCON:MEAS:STOP");
            Query("*OPC?");
            //dmm.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
            VStr = Query(":FORM:DATA ASC;:DATA? 'V" + sweepSMU + "';");
            IStr = Query(":FORM:DATA ASC;:DATA? 'I" + sweepSMU + "';");

            aborted = ZipDetectInf(CommaStringToDoubleArray(VStr),
                CommaStringToDoubleArray(IStr), out VI);
            return VI;
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

        private void SetY2(string y2Name, bool isLogScale = false)
        {
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                Write($":PAGE:DISP:GRAP:Y2:NAME '{y2Name}';");
                if (isLogScale) Write(":PAGE:DISP:GRAP:Y2:SCAL LOG;");
            }
        }
        private void ConfigureDisplay(double xmin, double xmax, double y1min, double y1max,
            double y2min = 1e-15, double y2max = 10e-3)
        {
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                Write($":PAGE:DISP:SET:GRAP:X:MIN {xmin};");
                Write($":PAGE:DISP:SET:GRAP:X:MAX {xmax};");
                Write($":PAGE:DISP:SET:GRAP:Y1:MIN {y1min};");
                Write($":PAGE:DISP:SET:GRAP:Y1:MAX {y1max};");
                Write($":PAGE:DISP:SET:GRAP:Y2:MIN {y2min};");
                Write($":PAGE:DISP:SET:GRAP:Y2:MAX {y2max};");
            }

        }
    }
}
