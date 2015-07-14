
namespace Instr
{
    public class SussPA300 : VisaCommunicator
    {
        // -- Referrence --
        // PBRemote.chm
        // ProberBench 6 Command and Interface Reference
        // - GPIB Interface
        // - Kernel Commands
        // 
        // ReadChuckPosition
        // ReadChuck Heights
        // MoveChuckSeparation
        // MoveChuckContact
        // 
        // MoveChuckIndex
        public SussPA300(string visaResource) : base(visaResource)
        {
            return;
        }

        void Test()
        {
            // near home position!

            // -- read --
            Query("ReadChuckPosition Y H D"); // home, separate: "0: 0.0 -0.5 -300.08"
                                              // home, align:    "0: 0.0 0.5 -99.95"
                                              // home, cont:     "0: 0.0 0.5 -1.27e-02"
            Query("ReadChuckIndex"); // 0: 1300.0 1300.0

            // -- move --
            Query("MoveChuckSeparation 5"); // 5% velocity
            Query("MoveChuckAlign 5"); // 5% velocity
            Query("MoveChuckContact 5"); // 5% velocity
            Query("MoveChuckIndex 0 0 H 5"); // from home position, 5% velocity

            // -- etc --
            Query("StopChuckMovement 7");
        }

    }
}
