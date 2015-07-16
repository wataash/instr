using System;
using System.Linq;

namespace Instr
{
    /// <summary>
    /// BEFORE USE -- Caribrate, do alignment, set home, set index and set z. Place the chuck near the home position.
    /// Device under measurement must be flat.
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

        int xLimNegaMicron { get; set; } = -20000; // 20,000um = 2cm
        int xLimPosMicron { get; set; } = 20000;
        int yLimNegaMicron { get; set; } = -20000;
        int yLimPosMicron { get; set; } = 20000;
        int zLimNegaMicron { get; set; } = -350;
        int zLimPosMicron { get; set; } = 50;

        /// <summary>
        /// Distance from home position
        /// TODO: unit test
        /// </summary>
        double[] xyzMicron
        {
            get
            {
                // "0: 0.0 -0.5 -300.08" -> {"0:", "0.0", "-0.5", "-300.08"}
                string[] q = Query("ReadChuckPosition Y H D").Split();
                return new[] { Double.Parse(q[1]), Double.Parse(q[2]), Double.Parse(q[3]) };
            }
        }
        double xMicron { get { return xyzMicron[0]; } }
        double yMicron { get { return xyzMicron[1]; } }
        double zMicron { get { return xyzMicron[2]; } }

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
        int xIndex { get { return (int)(xMicron / xIndexMicron); } }// TODO round
        int yIndex { get { return (int)(yMicron / yIndexMicron); } }// TODO round

        public int[] SepareteIndexMoveContact(int xIndex, int yIndex)
        {
            try
            {
                string responce;
                CheckStatus();
                responce = Query("MoveChuckSeparation 5"); // or align?
                if (ReadErrCode(responce) != 0) throw new Exception("Error on MoveChuckSeparation.");
                CheckStatus();
                while (this.xIndex != xIndex || this.yIndex != yIndex)
                {
                    // TODO
                    // move step by step
                    // Query($"MoveChuckIndex {xIndex} {yIndex} H 5"); // from home position, 5% velocity
                }
                CheckStatus();
                responce = Query("MoveChuckContact 5");
                CheckStatus();
            }
            catch (Exception)
            {
                throw;
            }
            finally
            {
                // separete
            }
            return new[] { 0, 0 };
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
        public double[] MoveIndexFromHere(int xNum, int yNum, int separateBefore)
        {
            if (Math.Abs(xNum) > 20 || Math.Abs(yNum) > 20) throw new ArgumentOutOfRangeException(nameof(xNum), "Too much long movement.");
            if (separateBefore < 0 || 2 < separateBefore) throw new ArgumentOutOfRangeException(nameof(separateBefore));
            CheckStatus();
            if (separateBefore == 1) Separate();
            if (separateBefore == 2) Align();
            CheckStatus();
            Query($"MoveChuckIndex {xNum} {yNum} R 5"); // from home position, 5% velocity
            CheckStatus();
            return xyzMicron;
        }

        public double[] Contact() { return new[] { 0.0 }; }
        public double[] Align() { return new[] { 0.0 }; }
        public double[] Separate() { return new[] { 0.0 }; }

        private void CheckStatus()
        {
            string[] q = Query("ReadChuckPosition Y H D").Split(':'); // new string[] { "0", " 0.0 0.5 -1.27e-02" }
            if (q[0] != "0") throw new SystemException("Error on ReadChuckPosition.");
            int[] xyz = q[1].Split().Select(Int32.Parse).ToArray();

            if (xyz[0] < xLimNegaMicron) throw new SystemException("x negative limit.");
            if (xyz[0] > xLimPosMicron) throw new SystemException("x positive limit.");
            if (xyz[1] < yLimNegaMicron) throw new SystemException("y negative limit.");
            if (xyz[1] > yLimPosMicron) throw new SystemException("y positive limit.");
            if (xyz[2] < zLimNegaMicron) throw new SystemException("z negative limit.");
            if (xyz[2] > zLimPosMicron) throw new SystemException("z positive limit.");
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
            Query("MoveChuckSeparation 5");  // 5% velocity
            Query("MoveChuckAlign 5");       // 5% velocity
            Query("MoveChuckContact 5");     // 5% velocity
            Query("MoveChuckIndex 0 0 H 5"); // from home position, 5% velocity
            // -- etc --
            Query("StopChuckMovement 7"); // 7 = 111(2) means stop z, y and x
        }

    }
}
