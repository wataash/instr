using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using NationalInstruments.VisaNS;


enum SweepStaircaseType
{
    Linear, Log10, Log25, Log50
}

enum SweepMode
{
    Single, Double
}

namespace Agilent4156C
{
    static class Program
    {
        /// <summary>
        /// アプリケーションのメイン エントリ ポイントです。
        /// </summary>
        [STAThread]
        static void Main()
        {
            string resourceString = "GPIB0::18::INSTR";
            MessageBasedSession mbSession;

            //try
            //{
            //    mbSession = (MessageBasedSession)ResourceManager.
            //        GetLocalManager().Open(resourceString);
            //}
            //catch (InvalidCastException)
            //{
            //    MessageBox.
            //        Show("Resource selected must be a message-based session");
            //}
            //catch (Exception exp)
            //{
            //    //MessageBox.Show(exp.Message);
            //    Console.WriteLine(exp.Message);
            //}

            mbSession = (MessageBasedSession)ResourceManager.
                GetLocalManager().Open(resourceString);
            SweepMeasurement(mbSession, 500e-3, 1e-3, 10e-3, 1, 2);
            mbSession.Dispose();

            //Application.EnableVisualStyles();
            //Application.SetCompatibleTextRenderingDefault(false);
            //Application.Run(new Form1());
        }

        // Level 4 /////////////////////////////////////////////////////////////
        // min(stepmV): 0.1mV
        public static void SweepMeasurement(
            MessageBasedSession mbSession, double endV, double stepV,
            double compI, int groundSMU, int biasSMU)
        {
            // Let's hard code.
            //{
            //    string writeStr = "";
            //    writeStr += ":PAGE:CHAN:SMU1:FUNC CONS;";
            //    writeStr += ":PAGE:CHAN:SMU1:INAM 'I1';";
            //    writeStr += ":PAGE:CHAN:SMU1:MODE COMM;";
            //    writeStr += ":PAGE:CHAN:SMU1:SRES 0;";
            //    writeStr += ":PAGE:CHAN:SMU1:STAN OFF;";
            //    writeStr += ":PAGE:CHAN:SMU1:VNAM 'V1';";
            //    mbSession.Write(writeStr);
            //    writeStr = "";
            //    writeStr += ":PAGE:CHAN:SMU2:FUNC VAR1;";
            //    writeStr += ":PAGE:CHAN:SMU2:INAM 'I2';";
            //    writeStr += ":PAGE:CHAN:SMU2:MODE V;";
            //    writeStr += ":PAGE:CHAN:SMU2:SRES 0;";
            //    writeStr += ":PAGE:CHAN:SMU2:STAN OFF;";
            //    writeStr += ":PAGE:CHAN:SMU2:VNAM 'V2';";
            //    mbSession.Write(writeStr);
            //}
            // IntegTime();
            // hold delay time
            string s;
            mbSession.Write(":PAGE:MEAS:SWE:VAR1:STAR 0");
            s = ";:PAGE:MEAS:VAR1:STEP " + stepV + ";";
            mbSession.Write(s);
            // for
            mbSession.Write(":PAGE:MEAS:SWE:VAR1:STOP" + endV); //!!!!
            mbSession.Write(":PAGE:DISP:SET:GRAP:X:MIN" + -endV);
            mbSession.Write(":PAGE:DISP:SET:GRAP:X:MAX" + endV);
            // stepV!!
            mbSession.Write(":PAGE:SCON:MEAS:DOUB"); // doub以外にstop appがある
            s = mbSession.Query("*OPC?");
            s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
            s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'I2';");
            double v = 0.1;
            while (v <= endV)
            {
                mbSession.Write(":PAGE:DISP:SET:GRAP:X:MIN" + -v);
                mbSession.Write(":PAGE:DISP:SET:GRAP:X:MAX" + v);
                // pos
                mbSession.Write(":PAGE:MEAS:SWE:VAR1:STOP" + v);
                mbSession.Write(":PAGE:SCON:MEAS:DOUB");
                s = mbSession.Query("*OPC?");
                s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'I2';");
                // V/deltaV + 1 != points ならbreak;
                // nega
                mbSession.Write(":PAGE:MEAS:SWE:VAR1:STOP" + -v);
                mbSession.Write(":PAGE:SCON:MEAS:DOUB");
                s = mbSession.Query("*OPC?");
                s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'V2';");
                s = mbSession.Query(":FORM:BORD NORM;DATA REAL, 64;:DATA? 'I2';");
                // V/deltaV + 1 != points ならbreak;
                //
                v += 0.1;
            }
        }

        //// Level 3 /////////////////////////////////////////////////////////////
        //static void Initialize(MessageBasedSession mbSession)
        //{
        //    DefaultInstrumentSetup(mbSession);
        //    string q = ErrorQuery(mbSession);
        //    MessageBox.Show(q); // if not error not msgbox
        //}

        //public static void ConfigureMeasurementMode(
        //    MessageBasedSession mbSession, int measurementMode)
        //{
        //    string modeString;
        //    switch (measurementMode)
        //    {
        //        case 0:
        //            modeString = ":PAGE:CHAN:MODE SWE;";
        //            break;
        //        case 1:
        //            modeString = ":PAGE:CHAN:MODE SAMP;";
        //            break;
        //        case 2:
        //            modeString = ":PAGE:CHAN:MODE QSCV;";
        //            break;
        //        default:
        //            MessageBox.Show("mode must be 0, 1 or 2");
        //            modeString = ":PAGE:CHAN:MODE SWE;";
        //            break;
        //    }
        //    mbSession.Write(modeString);
        //    ErrorQuery(mbSession);
        //}

        //public static void ConfigurePrimarySweepMeasurement(
        //    MessageBasedSession mbSession, int sweepMode, double compliance,
        //    double powerCompliance, double startV, double stopV,
        //    int sweepStaircaseType, double stepV)
        //{
        //    string writeStr = "";
        //    switch (sweepMode)
        //    {
        //        case 0:
        //            writeStr += ":PAGE:MEAS:VAR1:MODE SING;";
        //            break;
        //        case 1:
        //            writeStr += ":PAGE:MEAS:VAR1:MODE DOUB;";
        //            break;
        //        default:
        //            MessageBox.Show("sweep mode 0 or 1");
        //            break;
        //    }
        //    // double tostr?
        //    writeStr += ":PAGE:MEAS:VAR1:COMP " + compliance + ";";
        //    switch (sweepStaircaseType)
        //    {
        //        case 0:
        //            writeStr += ":PAGE:MEAS:VAR1:SPAC LIN;";
        //            break;
        //        case 1:
        //            writeStr += ":PAGE:MEAS:VAR1:SPAC L10;";
        //            break;
        //        case 2:
        //            writeStr += ":PAGE:MEAS:VAR1:SPAC L25;";
        //            break;
        //        case 3:
        //            writeStr += ":PAGE:MEAS:VAR1:SPAC L50;";
        //            break;
        //        default:
        //            MessageBox.Show("err");
        //            break;
        //    }
        //    writeStr += ":PAGE:MEAS:VAR1:STAR " + startV + ";";
        //    writeStr += ":PAGE:MEAS:VAR1:STOP " + stopV + ";";
        //    writeStr += ":PAGE:MEAS:VAR1:STEP " + stepV + ";";
        //    mbSession.Write(writeStr);
        //    ErrorQuery(mbSession);
        //}

        //public static void ConfigureSubordinateSweepMeasurement(
        //    MessageBasedSession mbSession, double compliance,
        //    bool onPowerCompliance, double powerCompliance, int numSteps,
        //    double step, double start)
        //{

        //}

        //public static void ConfugreIntegrationTime(int NPLC, int integTimeMode,
        //    double shortIntegrationTime)
        //{

        //}

        //public static double[] ReadTraceData(
        //    MessageBasedSession mbSession, int timeout, string variableName)
        //{
        //    return new[] { 0.0, 0.0 };
        //}
        //public static void WaitForAcquisitionComplete(int timeoutMilliSec)
        //{

        //}


        //// Level 2 /////////////////////////////////////////////////////////////
        //static void Reset(MessageBasedSession mbSession)
        //{
        //    mbSession.Write("*RST");
        //    DefaultInstrumentSetup(mbSession);
        //}
        //// Level 1 /////////////////////////////////////////////////////////////
        //static void DefaultInstrumentSetup(MessageBasedSession mbSession)
        //{
        //    // *ESE 60 - enables command, execution, query, and device errors
        //    // in event status register
        //    // *SRE 48 - enables message available, standard event bits in the
        //    // status byte
        //    // * CLS - clears status
        //    mbSession.Write("*ESE 60;*SRE 48;*CLS;");
        //}
        //static string ErrorQuery(MessageBasedSession mbSession)
        //{
        //    mbSession.Write(":SYST:ERR?");
        //    //mbSession.Query()
        //    return mbSession.ReadString(256);
        //}

    }
}
