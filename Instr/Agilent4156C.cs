using System;
using System.Linq;
using static Instr.Functions;

namespace Instr
{
    public class Agilent4156C : VisaCommunicator
    {
        bool useUSCommands; // see GPIB manual

        public Agilent4156C(string visaResource, bool useUSCommands) : base(visaResource)
        {
            this.useUSCommands = useUSCommands;
            if (useUSCommands) Write("US");
        }

        /// <summary>
        /// Integration time is fixed to 20ms (1NPLC).
        /// Returns {{t0, t1, t2, ...}, {i0, i1, i2, ...}}
        /// </summary>
        /// <param name="groundSmu"></param>
        /// <param name="biasSmu"></param>
        /// <param name="timeInterval"></param>
        /// <param name="voltage"></param>
        /// <param name="compliance"></param>
        /// <param name="measTimeSecond">Converted to points=measTimeSecond/timeInterval. Ignored if "points" is given.</param>
        /// <param name="points">Overides "measTimeSecond".</param>
        /// <param name="y1Min"></param>
        /// <param name="y1Max"></param>
        /// <returns></returns>
        public double[][] ContactTest(
            int groundSmu, int biasSmu,
            double timeInterval = 10e-3,
            double voltage = 1e-3, double compliance = 10e-3,
            int measTimeSecond = 60, int points = 0, double y1Min = 0, double y1Max = 1e-3)
        // TODO: order in the displayed order on 4156C
        {
            if (points == 0) points = (int)(measTimeSecond / timeInterval);
            points = Math.Min(8000, points); // 8000: OK, 8500: "ERROR 7: DATA buffer full. Too many points."
            Write("*RST");
            if (useUSCommands)
                throw new NotImplementedException();
            else
                Write(":PAGE:CHAN:MODE SAMP;"); // not in GPIB mannual damn

            DisableAllUnits(groundSmu, biasSmu);
            //ConfugureSmu(groundSmu, 3, 3); // not necessary
            //ConfugureSmu(biasSmu, 1, 3); // not necessary

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
            ConfigureDisplay(0, measTimeSecond, y1Min, y1Max, 1e-12, 100e-6); // 1 Gohm, 10 ohm at 1mV

            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                Write(":PAGE:MEAS:MSET:ITIM MED;"); // fixed
                Write(":PAGE:SCON:SING");
            }

            Query("*OPC?");
            double[] times, currents;
            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                times = CommaStringToDoubleArray(Query(":FORM:DATA ASC;:DATA? '@TIME';"));
                // +0.000000E+000,+3.500000E-001,+6.000000E-001,+8.000000E-001,+9.91E+307,+9.91E+307
                currents = CommaStringToDoubleArray(Query($":FORM:DATA ASC;:DATA? 'I{biasSmu}';"));
                // +1.200000E-013,+1.200000E-013,+1.200000E-013,+1.200000E-013,+9.91E+307,+9.91E+307
            }
            return new[] {times, currents};
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="groundSMU"></param>
        /// <param name="sweepSMU"></param>
        /// <param name="endV"></param>
        /// <param name="stepV">should be larer tnan 0.</param>
        /// <param name="aborted"></param>
        /// <param name="displayCurrent">should be larger than 0.</param>
        /// <param name="compI"></param>
        /// <returns></returns>
        public double[][] DoubleSweepFromZero(
            int groundSMU, int sweepSMU,
            double endV, double stepV,
            out bool aborted, double displayCurrent = 10e-3, double compI = 10e-3)
        {
            if (displayCurrent <= 0) throw new ArgumentOutOfRangeException();
            if (stepV <= 0) throw new ArgumentOutOfRangeException();
            bool isP = endV > 0; // is positive sweep
            string VStr, IStr;
            double[][] VI;

            Write("*RST");
            // TODO: Integration time, Hold time, Deley time
            DisableAllUnits(groundSMU, sweepSMU);
            //ConfugureSmu(groundSMU, 3, 3); // not necessary
            //ConfugureSmu(sweepSMU, 1, 1); // not necessary

            if (useUSCommands)
            {
                throw new NotImplementedException();
            }
            else
            {
                Write(":PAGE:MEAS:VAR1:MODE DOUB;");
                //Write(":PAGE:MEAS:SWE:VAR1:STAR 0"); // not necessary
                Write($":PAGE:MEAS:VAR1:STOP {endV};");
                Write($":PAGE:MEAS:VAR1:STEP {(isP ? stepV : -stepV)};");
                // TODO: hold time, deley time
                // TODO: stop at abnormal
            }

            SetY2($"I{sweepSMU}", true);
            ConfigureDisplay(isP ? 0 : endV, isP ? endV : 0, isP ? 0 : -displayCurrent, isP ? displayCurrent : 0,
                isP ? 1e-15 : -10e-3, isP ? 10e-3 : -1e-15);



            Write(":PAGE:SCON:MEAS:SING");
            //dmm.WriteString(":PAGE:SCON:MEAS:APP");
            //dmm.WriteString(":PAGE:SCON:MEAS:STOP");
            Query("*OPC?");
            //dmm.WriteString(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");

            // +0.000000E+000,+1.000000E-003,+2.000000E-003,+3.000000E-003,+3.000000E-003,+2.000000E-003,+1.000000E-003,+0.000000E+000
            VStr = Query(":FORM:DATA ASC;:DATA? 'V" + sweepSMU + "';");
            // +1.000000E-013,+1.700000E-013,+1.500000E-013,+1.500000E-013,+1.100000E-013,+1.400000E-013,+1.800000E-013,+9.000000E-014
            IStr = Query(":FORM:DATA ASC;:DATA? 'I" + sweepSMU + "';");

            // VI: { {0,1E-13}, {0.001,1.7E-13}, ... }
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
