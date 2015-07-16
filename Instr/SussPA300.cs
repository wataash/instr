using System;
using System.Linq;
using System.Collections.Generic;

namespace Instr
{
    /// <summary>
    /// BEFORE USE -- Caribrate, do alignment, set home, set index and set z. Place the chuck near the home position.
    /// Device under measurement must be flat.
    /// "H": relative to home position in micro meter unit.
    /// <para>Movement is restricted in -20000um &lt; x, y &lt; 20000um (2cm square) and -350um &lt; z &lt; 50um.</para>
    /// <para>[Referrences] ProberBench 6 Command and Interface Reference (PBRemote.chm)
    /// -- GPIB Interface, Kernel Commands</para>
    /// </summary>
    public class SussPA300 : VisaCommunicator
    {
        public SussPA300(string visaResource) : base(visaResource)
        {
            CheckStatus();
        }

        int xHLimNega { get; set; } = -20000; // 20,000um = 2cm
        int xHLimPos { get; set; } = 20000;
        int yHLimNega { get; set; } = -20000;
        int yHLimPos { get; set; } = 20000;
        int zHLimNega { get; set; } = -350;
        int zHLimPos { get; set; } = 50;

        /// <summary>
        /// Distance from home position
        /// TODO: unit test
        /// </summary>
        double[] xyzH
        {
            get
            {
                // "0: 0.0 -0.5 -300.08" -> {"0:", "0.0", "-0.5", "-300.08"}
                string[] q = Query("ReadChuckPosition Y H D").Split();
                return new[] { Double.Parse(q[1]), Double.Parse(q[2]), Double.Parse(q[3]) };
            }
        }
        double xH { get { return xyzH[0]; } }
        double yH { get { return xyzH[1]; } }
        double zH { get { return xyzH[2]; } }

        /// <summary>
        /// Index (delta) of {x, y} in [um] unit.
        /// TODO: unit test
        /// </summary>
        double[] xyIndexMicron
        {
            get
            {
                // "0: 1300.0 1300.0" -> {"0", "1300.0", "1300.0"}
                string[] q = Query("ReadChuckIndex").Split();
                return new[] { Double.Parse(q[1]), Double.Parse(q[2]) };
            }
        }
        double xIndexMicron { get { return xyIndexMicron[0]; } }
        double yIndexMicron { get { return xyIndexMicron[1]; } }
        int xIndex { get { return (int)Math.Round(xH / xIndexMicron); } }// TODO: test
        int yIndex { get { return (int)Math.Round(yH / yIndexMicron); } }

        private double v = 5;
        /// <summary>
        /// TODO: test, wrong way?
        /// </summary>
        private double velocity
        {
            get { return v; }
            set
            {
                if (value < 0 || 100 < value)
                    throw new ArgumentOutOfRangeException(nameof(value));
                v = value;
            }
        }

        /// <summary>
        /// If xyIndexMicron == {1000, 1000},
        /// MoveIndexFromHere(2, -1) -> moves chuck 2000um to right and 1000um to front (down).
        /// Returns xyz position.
        /// TODO: unit test
        /// </summary>
        /// <param name="xNum">-20 &lt; xNum &lt; 20</param>
        /// <param name="yNum">-20 &lt; yNum &lt; 20</param>
        /// <param name="separateBefore">0: not separate, 1: separate, 2: align</param>
        /// <returns></returns>
        public double[] MoveIndexR(int xNum, int yNum, int separateBefore)
        {
            if (Math.Abs(xNum) > 20 || Math.Abs(yNum) > 20) throw new ArgumentOutOfRangeException(nameof(xNum), "Too much long movement.");
            if (separateBefore < 0 || 2 < separateBefore) throw new ArgumentOutOfRangeException(nameof(separateBefore));
            CheckStatus();
            if (separateBefore == 1) Separate();
            if (separateBefore == 2) Align();
            CheckStatus();
            Query($"MoveChuckIndex {xNum} {yNum} R {velocity}");
            CheckStatus();
            return xyzH;
        }

        /// <summary>
        /// Move chuck ralative to the home position and contact prober.
        /// </summary>
        /// <param name="xH">x[um] from the home postion.</param>
        /// <param name="yH">y[um] from the home position.</param>
        /// <param name="separateBefore">0: not separate, 1: separate, 2: align</param>
        /// <returns>Achieved xyz[um] from home.</returns>
        public double[] MoveChuckHCont(double xH, double yH, int separateBefore = 1)
        {
            if (xH < xHLimNega || xHLimPos < xH) throw new ArgumentOutOfRangeException(nameof(xH));
            if (yH < xHLimNega || xHLimPos < yH) throw new ArgumentOutOfRangeException(nameof(yH));
            CheckStatus();
            if (separateBefore == 1)
            {
                Separate();
                CheckStatus();
            }
            if (separateBefore == 2)
            {
                Align();
                CheckStatus();
            }
            Query($"MoveChuck {xH} {yH} H 5");
            CheckStatus();
            Contact();
            CheckStatus();
            return xyzH;
        }

        /// <summary>
        /// TODO: test
        /// </summary>
        public void Contact()
        {
            CheckStatus();
            Query($"MoveChuckContact {velocity}");
            CheckStatus();
        }

        public void Align()
        {
            CheckStatus();
            Query($"MoveChuckAlign {velocity}");
            CheckStatus();
        }
        public void Separate()
        {
            CheckStatus();
            Query($"MoveChuckSeparation {velocity}");
            CheckStatus();
        }

        /// <summary>
        /// TODO: unit test
        /// </summary>
        private void CheckStatus()
        {
            string[] q = Query("ReadSystemStatus").Split(':'); // new string[] { "0", " PA300PS..." }
            if (q[0] != "0") throw new SystemException("Error on ReadSystemStatus.");
            if (xH < xHLimNega) throw new SystemException("x negative limit.");
            if (xH > xHLimPos) throw new SystemException("x positive limit.");
            if (yH < yHLimNega) throw new SystemException("y negative limit.");
            if (yH > yHLimPos) throw new SystemException("y positive limit.");
            if (zH < zHLimNega) throw new SystemException("z negative limit.");
            if (zH > zHLimPos) throw new SystemException("z positive limit.");
        }

        private int ReadErrCode(string responce)
        {
            return Int32.Parse(responce.Split(':')[0]);
        }

        /// <summary>
        /// DO NOT execute.
        /// </summary>
        private void Sample()
        {
            return; // prevent execution
            // -- read --
            Query("ReadChuckPosition Y H D"); // home, separate: "0: 0.0 -0.5 -300.08"
                                              // home, align:    "0: 0.0 0.5 -99.95"
                                              // home, cont:     "0: 0.0 0.5 -1.27e-02"
            Query("ReadChuckIndex"); // 0: 1300.0 1300.0
            // -- move --
            Query("MoveChuck 7500 5400 H 5"); // (7500um, 5400um) from home, 5% velocity
            Query("MoveChuckSeparation 5");   // 5% velocity
            Query("MoveChuckAlign 5");        // 5% velocity
            Query("MoveChuckContact 5");      // 5% velocity
            Query("MoveChuckIndex 0 0 H 5");  // from home position, 5% velocity
            // -- etc --
            Query("StopChuckMovement 7"); // 7 = 111(2) means stop z, y and x
        }

    }
}
